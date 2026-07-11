# -*- coding: UTF-8 -*-

"""
Vendor-generic configuration management built on top of the RouterOS binary API.

Everything here is implemented with plain API commands (``/export``, ``/import``,
``/file``, ``/system/backup``, ``/system/scheduler``, ``/system/reset-configuration``)
so no SSH/terminal access is required. RouterOS has no native, non-reboot
commit/rollback; a device-side ``/system/scheduler`` job that restores a backup acts
as a dead man's switch (see :meth:`Config.arm_rollback`).

Requires RouterOS 7.x.
"""

from __future__ import annotations

import asyncio
import difflib
import re
from logging import getLogger
from posixpath import join as pjoin
from time import sleep
from typing import TYPE_CHECKING

from librouteros.exceptions import LibRouterosError, TrapError
from librouteros.query import And, Key
from librouteros.types import ReplyDict, ROSType

LOGGER = getLogger("librouteros")

if TYPE_CHECKING:
    from librouteros.api import Api, AsyncApi

# Transient file / job names used on the device. Reused (and cleaned up) between calls.
EXPORT_FILE = "librouteros-export"
IMPORT_FILE = "librouteros-import.rsc"
ROLLBACK_NAME = "librouteros-rollback"
REPLACE_NAME = "librouteros-replace"

# Default scheduler policy for the rollback job. This is a known-working set (validated
# on RouterOS 7.x that the fired job actually loads the backup); a narrower set silently
# fails at fire time. RouterOS also rejects scheduler creation unless the API user holds
# every listed policy, so a restricted account can override this via arm_rollback.
_ROLLBACK_POLICY = "ftp,reboot,read,write,policy,test"

# How much of a large file to pull per /file/read call (bytes).
_READ_CHUNK = 32768
# A file just written by /export is briefly unreadable via /file/read even though it
# already shows up in /file/print; retry the read a few times before giving up.
_READ_RETRIES = 6
_READ_RETRY_DELAY = 0.2

# Marks the rollback scheduler as ours so a user job that happens to share the reserved
# name is not mistaken for it (and never removed by cancel_rollback).
ROLLBACK_COMMENT = "librouteros rollback dead man switch"

# First line of an /export is a volatile timestamp header:
#   # 2026-07-11 21:04:13 by RouterOS 7.21.5
# Strip the date/time so repeated exports diff cleanly.
_HEADER_RE = re.compile(r"^# \S+ \S+ by (.+)$", flags=re.MULTILINE)

# Query keys for /file and /system/scheduler reads.
_ID = Key(".id")
_NAME = Key("name")
_CONTENTS = Key("contents")
_TYPE = Key("type")
_COMMENT = Key("comment")
_SIZE = Key("size")


def strip_header(text: str) -> str:
    """Replace the volatile ``# <date> <time> by ...`` export header with ``# by ...``."""
    return _HEADER_RE.sub(r"# by \1", text)


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n")


def normalize_for_diff(text: str) -> list[str]:
    text = strip_header(normalize_newlines(text))
    # rstrip each line so trailing-whitespace noise does not show up as a change
    return [line.rstrip() for line in text.splitlines()]


def compare(running: str, candidate: str, *, context: int = 3) -> str:
    """
    Return a human readable unified diff between two RouterOS configurations.

    This is informational only, not an executable RouterOS patch. Both sides are
    normalized (newlines, volatile export header, trailing whitespace) before diffing.

    :param running: Configuration currently on the device (e.g. from :meth:`Config.export`).
    :param candidate: Desired configuration.
    :param context: Number of unified-diff context lines.
    :returns: Unified diff, or an empty string when there is no difference.
    """
    diff = difflib.unified_diff(
        normalize_for_diff(running),
        normalize_for_diff(candidate),
        fromfile="running",
        tofile="candidate",
        n=context,
        lineterm="",
    )
    return "\n".join(diff)


def export_args(
    *,
    file: str,
    compact: bool,
    verbose: bool,
    terse: bool,
    show_sensitive: bool,
) -> dict[str, ROSType]:
    args: dict[str, ROSType] = {"file": file}
    if compact:
        args["compact"] = True
    if verbose:
        args["verbose"] = True
    if terse:
        args["terse"] = True
    if show_sensitive:
        args["show-sensitive"] = True
    return args


def export_command(path: str | None) -> str:
    # RouterOS has no `path=` parameter; a scoped export runs from within the menu,
    # e.g. `/ip/address/export`.
    if path is None:
        return "/export"
    return pjoin("/", path, "export")


def import_args(*, filename: str, verbose: bool, dry_run: bool) -> dict[str, ROSType]:
    # RouterOS rejects dry-run unless verbose is also set.
    if dry_run:
        verbose = True
    args: dict[str, ROSType] = {"file-name": filename}
    if verbose:
        args["verbose"] = True
    if dry_run:
        args["dry-run"] = True
    return args


def backup_save_args(*, name: str, password: str | None, dont_encrypt: bool) -> dict[str, ROSType]:
    args: dict[str, ROSType] = {"name": name}
    if password is not None:
        args["password"] = password
    elif dont_encrypt:
        args["dont-encrypt"] = True
    return args


def backup_load_args(*, name: str, password: str | None) -> dict[str, ROSType]:
    # /system/backup/load requires the password parameter even for an unencrypted
    # backup (in which case it is an empty string).
    return {"name": name, "password": password if password is not None else ""}


def ros_quote(value: str) -> str:
    """
    Quote a value for safe embedding in a RouterOS console script string.

    The scheduler ``on-event`` is executed as a RouterOS script, so a raw value
    containing a space, ``;``, ``"``, ``\\``, ``$`` (variable substitution) or a control
    character would otherwise produce a malformed command that only fails when the timer
    fires. A raw newline in particular is not a valid RouterOS string literal.
    """
    escaped = (
        value.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\r", "\\r").replace("\n", "\\n")
    )
    return f'"{escaped}"'


def scheduler_args(*, name: str, backup: str, seconds: int, password: str | None, policy: str) -> dict[str, ROSType]:
    # The password is mandatory for /system backup load, empty for an unencrypted backup.
    # Both the backup name and password are quoted so special characters cannot break the
    # script. ``backup`` may differ from the job ``name`` (it carries the persistent path).
    on_event = (
        f"/system backup load name={ros_quote(backup)} password={ros_quote(password if password is not None else '')}"
    )
    return {
        "name": name,
        "interval": f"{seconds}s",
        "on-event": on_event,
        "policy": policy,
        "comment": ROLLBACK_COMMENT,
    }


def reset_args(*, filename: str, keep_users: bool, no_defaults: bool) -> dict[str, ROSType]:
    args: dict[str, ROSType] = {"run-after-reset": filename}
    if no_defaults:
        args["no-defaults"] = True
    if keep_users:
        args["keep-users"] = True
    return args


class Config:
    """
    Configuration management helper bound to a synchronous :class:`~librouteros.api.Api`.

    Obtain one via :meth:`~librouteros.api.Api.config` or ``Config(api=...)``.
    """

    def __init__(self, api: Api) -> None:
        self.api: Api = api

    # -- low level /file helpers ------------------------------------------------

    def _version(self) -> tuple[int, ...]:
        version = next(iter(self.api("/system/resource/print")))["version"]
        return tuple(int(part) for part in str(version).split()[0].split("."))

    def _file_contents(self, name: str) -> str:
        rows = tuple(self.api.path("file").select(_SIZE, _CONTENTS).where(_NAME == name))
        if not rows:
            raise FileNotFoundError(f"File {name!r} not found on device.")
        contents = rows[0].get("contents")
        if contents is not None:
            return str(contents)
        # Files larger than the API's inline limit (~a few tens of KB) do not expose the
        # 'contents' property; read them back in chunks. /file/read needs RouterOS 7.13+.
        if self._version() < (7, 13):
            raise NotImplementedError("Reading a file larger than the inline API limit requires RouterOS 7.13+.")
        return self._file_read(name, int(rows[0].get("size") or 0))

    def _file_read(self, name: str, size: int) -> str:
        parts: list[str] = []
        offset = 0
        while offset < size:
            data = self._read_chunk(name, offset)
            if not data:
                break
            parts.append(data)
            offset += len(data)
        return "".join(parts)

    def _read_chunk(self, name: str, offset: int) -> str:
        args: dict[str, ROSType] = {"file": name, "offset": offset, "chunk-size": _READ_CHUNK}
        for attempt in range(_READ_RETRIES):
            try:
                rows = list(self.api("/file/read", **args))
                return str(rows[0].get("data", "")) if rows else ""
            except TrapError:
                # The file is not readable yet (just written by /export); back off.
                if attempt == _READ_RETRIES - 1:
                    raise
                sleep(_READ_RETRY_DELAY)
        return ""  # pragma: no cover

    def _file_remove(self, name: str) -> None:
        ids = tuple(row[".id"] for row in self.api.path("file").select(_ID).where(_NAME == name))
        if ids:
            self.api.path("file").remove(*(str(i) for i in ids))

    def _safe_file_remove(self, name: str) -> None:
        # Best-effort cleanup for finally blocks: must not mask the original error (e.g.
        # the imported config just cut our own management access).
        try:
            self._file_remove(name)
        except (LibRouterosError, OSError) as exc:
            LOGGER.warning("Failed to remove temporary file %r: %s", name, exc)

    def _has_flash(self) -> bool:
        rows = tuple(self.api.path("file").select(_TYPE).where(_NAME == "flash"))
        return any(row.get("type") == "directory" for row in rows)

    def _persistent_path(self, filename: str) -> str:
        # Devices with a 'flash' directory only persist files stored inside it.
        return f"flash/{filename}" if self._has_flash() else filename

    def _scheduler_remove(self, name: str) -> None:
        # Only match our own job (name + comment), never a user job of the same name.
        scheduler = self.api.path("system", "scheduler")
        ids = tuple(row[".id"] for row in scheduler.select(_ID).where(And(_NAME == name, _COMMENT == ROLLBACK_COMMENT)))
        if ids:
            scheduler.remove(*(str(i) for i in ids))

    # -- public api -------------------------------------------------------------

    def export(
        self,
        *,
        compact: bool = False,
        verbose: bool = False,
        terse: bool = False,
        show_sensitive: bool = False,
        path: str | None = None,
    ) -> str:
        """
        Return the device configuration as text.

        ``/export`` writes nothing to the API when run directly, so this exports to a
        temporary file and reads its contents back. Newlines are normalized to ``\\n``;
        the volatile timestamp header is left intact (use :func:`compare` or
        :func:`strip_header` to normalize it away).

        :param compact: Output only the modified configuration (RouterOS default).
        :param verbose: Output the whole configuration including defaults.
        :param terse: Output configuration as full single-line commands.
        :param show_sensitive: Include sensitive data (passwords, keys). Hidden by default.
        :param path: Limit export to a menu path, e.g. ``"ip/address"`` (runs
            ``/ip/address/export``).
        """
        args = export_args(
            file=EXPORT_FILE, compact=compact, verbose=verbose, terse=terse, show_sensitive=show_sensitive
        )
        # /export overwrites an existing file, so no need to remove it first.
        tuple(self.api(export_command(path), **args))
        try:
            return normalize_newlines(self._file_contents(f"{EXPORT_FILE}.rsc"))
        finally:
            self._safe_file_remove(f"{EXPORT_FILE}.rsc")

    def apply(
        self,
        text: str | None = None,
        *,
        filename: str | None = None,
        verbose: bool = False,
        dry_run: bool = False,
    ) -> None:
        """
        Import (run) a RouterOS ``.rsc`` script.

        Provide exactly one of ``text`` (uploaded to a temporary file first) or
        ``filename`` (an ``.rsc`` already present on the device).

        Import is not transactional: a syntax error aborts before any change is made,
        but a valid-but-failing command applies earlier lines then stops. Errors are
        raised as :class:`~librouteros.exceptions.TrapError` (with line/column). Use
        :meth:`validate` to check a script first and :meth:`arm_rollback` for a net.

        :param text: Configuration script to upload and run.
        :param filename: Name of an ``.rsc`` file already on the device.
        :param verbose: Execute and report each line individually.
        :param dry_run: Simulate without applying (implies ``verbose``; RouterOS 7.16+).
        """
        if filename is not None and text is not None:
            raise ValueError("Provide exactly one of 'text' or 'filename'.")
        if filename is not None:
            tuple(self.api("/import", **import_args(filename=filename, verbose=verbose, dry_run=dry_run)))
        elif text is not None:
            # /file/add fails if the file already exists, so remove any stale copy first.
            self._file_remove(IMPORT_FILE)
            self.api.path("file").add(name=IMPORT_FILE, contents=text)
            try:
                tuple(self.api("/import", **import_args(filename=IMPORT_FILE, verbose=verbose, dry_run=dry_run)))
            finally:
                self._safe_file_remove(IMPORT_FILE)
        else:
            raise ValueError("Provide exactly one of 'text' or 'filename'.")

    def validate(self, text: str) -> None:
        """
        Dry-run a configuration script, raising on any error, without applying it.

        Requires RouterOS 7.16+.
        """
        self.apply(text, verbose=True, dry_run=True)

    def compare(self, candidate: str, *, context: int = 3, **export_kwargs: bool | str | None) -> str:
        """
        Return a unified diff between the running configuration and ``candidate``.

        The running configuration is exported automatically. Extra keyword arguments
        are forwarded to :meth:`export` (e.g. ``show_sensitive=True``).
        """
        running = self.export(**export_kwargs)  # type: ignore[arg-type]
        return compare(running, candidate, context=context)

    def backup_save(
        self, name: str, *, password: str | None = None, dont_encrypt: bool = True, persistent: bool = False
    ) -> None:
        """
        Save a binary backup (``name.backup``). Backups are same-device/same-version.

        :param name: Backup file name (``.backup`` appended automatically).
        :param password: Encrypt with this password. When omitted and ``dont_encrypt``
            is true, the backup is left unencrypted.
        :param dont_encrypt: Do not encrypt when no ``password`` is given.
        :param persistent: Store under ``flash/`` on devices that keep a RAM disk at the
            file-system root, so the backup survives a reboot.
        """
        target = self._persistent_path(name) if persistent else name
        tuple(
            self.api(
                "/system/backup/save", **backup_save_args(name=target, password=password, dont_encrypt=dont_encrypt)
            )
        )

    def backup_load(self, name: str, *, password: str | None = None, persistent: bool = False) -> None:
        """
        Load a binary backup. This reboots the device (the API connection will drop).

        :param persistent: Resolve ``name`` the same way :meth:`backup_save` did with
            ``persistent=True``.
        """
        target = self._persistent_path(name) if persistent else name
        tuple(self.api("/system/backup/load", **backup_load_args(name=target, password=password)))

    def backup_exists(self, name: str, *, persistent: bool = False) -> bool:
        """Return whether ``name.backup`` exists on the device."""
        target = self._persistent_path(name) if persistent else name
        rows = tuple(self.api.path("file").select(_NAME).where(_NAME == f"{target}.backup"))
        return len(rows) > 0

    def arm_rollback(
        self, seconds: int, *, name: str = ROLLBACK_NAME, password: str | None = None, policy: str = _ROLLBACK_POLICY
    ) -> None:
        """
        Arm a device-side rollback that restores the current config after ``seconds``.

        Saves a backup of the current state (to persistent storage so it survives a
        reboot) and schedules a ``/system/scheduler`` job that reloads it, rebooting the
        device. Call :meth:`cancel_rollback` to confirm/keep the new configuration before
        the timer fires. Because the timer lives on the device it survives client death, a
        lost session, or a lock-out, with no safe-mode action limit.

        :param seconds: Delay before the automatic restore fires (a positive integer).
        :param name: Backup and scheduler job name.
        :param password: Optional backup password. Note: it is embedded in the scheduler
            ``on-event`` (visible via export); prefer leaving it unset.
        :param policy: Scheduler policy set. RouterOS refuses to create the job unless the
            API user holds every listed policy; restricted accounts can narrow this.
        """
        if not isinstance(seconds, int) or seconds < 1:
            raise ValueError("seconds must be a positive integer.")
        # Remove any stale job BEFORE the backup so the backup cannot capture the
        # rollback scheduler itself (which would reboot-loop when restored).
        self._scheduler_remove(name)
        backup = self._persistent_path(name)
        self.backup_save(backup, password=password)
        tuple(
            self.api(
                "/system/scheduler/add",
                **scheduler_args(name=name, backup=backup, seconds=seconds, password=password, policy=policy),
            )
        )

    def cancel_rollback(self, *, name: str = ROLLBACK_NAME) -> None:
        """Cancel an armed rollback (the confirm path): remove the job and its backup."""
        self._scheduler_remove(name)
        self._file_remove(f"{self._persistent_path(name)}.backup")

    def rollback_pending(self, *, name: str = ROLLBACK_NAME) -> bool:
        """Return whether a rollback job armed by :meth:`arm_rollback` is still scheduled."""
        scheduler = self.api.path("system", "scheduler")
        rows = tuple(scheduler.select(_NAME).where(And(_NAME == name, _COMMENT == ROLLBACK_COMMENT)))
        return len(rows) > 0

    def replace(
        self,
        text: str,
        *,
        keep_users: bool = True,
        no_defaults: bool = True,
        name: str = REPLACE_NAME,
    ) -> None:
        """
        Replace the whole configuration by wiping and rebooting into ``text``.

        Uploads ``text`` to persistent storage and runs ``/system reset-configuration
        run-after-reset=...``. This is destructive: the device wipes its configuration,
        reboots, and replays the script (the API connection drops).

        There is NO automatic rollback for a replace: safe mode is ignored for resets,
        the run-after-reset script must finish within ~2 minutes, and with
        ``no_defaults`` the script must fully establish management connectivity or the
        device becomes unreachable. Ensure out-of-band (console/netinstall) recovery.

        The script is imperative, so its ``add`` lines fail if the entity already
        exists in whatever the reset leaves behind (e.g. an ``/ip dhcp-client add`` when
        the platform re-creates a management dhcp-client after reset); such a failure
        aborts the rest of the script. The candidate must match the post-reset state.

        :param keep_users: Retain existing user accounts across the reset.
        :param no_defaults: Do not lay down RouterOS factory defaults before the script.
        :param name: Base name for the uploaded ``.rsc`` file.
        """
        filename = self._persistent_path(f"{name}.rsc")
        # /file/add fails if the file already exists, so remove any stale copy first.
        self._file_remove(filename)
        self.api.path("file").add(name=filename, contents=text)
        tuple(
            self.api(
                "/system/reset-configuration",
                **reset_args(filename=filename, keep_users=keep_users, no_defaults=no_defaults),
            )
        )


class AsyncConfig:
    """
    Configuration management helper bound to an :class:`~librouteros.api.AsyncApi`.

    Async mirror of :class:`Config`; see it for method semantics.
    """

    def __init__(self, api: AsyncApi) -> None:
        self.api: AsyncApi = api

    async def _drain(self, cmd: str, /, **kwargs: ROSType) -> list[ReplyDict]:
        return [row async for row in self.api(cmd, **kwargs)]

    # -- low level /file helpers ------------------------------------------------

    async def _version(self) -> tuple[int, ...]:
        rows = [row async for row in self.api("/system/resource/print")]
        return tuple(int(part) for part in str(rows[0]["version"]).split()[0].split("."))

    async def _file_contents(self, name: str) -> str:
        rows = [row async for row in self.api.path("file").select(_SIZE, _CONTENTS).where(_NAME == name)]
        if not rows:
            raise FileNotFoundError(f"File {name!r} not found on device.")
        contents = rows[0].get("contents")
        if contents is not None:
            return str(contents)
        # Large files do not expose 'contents'; read them in chunks. /file/read needs 7.13+.
        if await self._version() < (7, 13):
            raise NotImplementedError("Reading a file larger than the inline API limit requires RouterOS 7.13+.")
        return await self._file_read(name, int(rows[0].get("size") or 0))

    async def _file_read(self, name: str, size: int) -> str:
        parts: list[str] = []
        offset = 0
        while offset < size:
            data = await self._read_chunk(name, offset)
            if not data:
                break
            parts.append(data)
            offset += len(data)
        return "".join(parts)

    async def _read_chunk(self, name: str, offset: int) -> str:
        args: dict[str, ROSType] = {"file": name, "offset": offset, "chunk-size": _READ_CHUNK}
        for attempt in range(_READ_RETRIES):
            try:
                rows = await self._drain("/file/read", **args)
                return str(rows[0].get("data", "")) if rows else ""
            except TrapError:
                # The file is not readable yet (just written by /export); back off.
                if attempt == _READ_RETRIES - 1:
                    raise
                await asyncio.sleep(_READ_RETRY_DELAY)
        return ""  # pragma: no cover

    async def _file_remove(self, name: str) -> None:
        ids = [row[".id"] async for row in self.api.path("file").select(_ID).where(_NAME == name)]
        if ids:
            await self.api.path("file").remove(*(str(i) for i in ids))

    async def _safe_file_remove(self, name: str) -> None:
        try:
            await self._file_remove(name)
        except (LibRouterosError, OSError) as exc:
            LOGGER.warning("Failed to remove temporary file %r: %s", name, exc)

    async def _has_flash(self) -> bool:
        rows = [row async for row in self.api.path("file").select(_TYPE).where(_NAME == "flash")]
        return any(row.get("type") == "directory" for row in rows)

    async def _persistent_path(self, filename: str) -> str:
        return f"flash/{filename}" if await self._has_flash() else filename

    async def _scheduler_remove(self, name: str) -> None:
        # Only match our own job (name + comment), never a user job of the same name.
        scheduler = self.api.path("system", "scheduler")
        ids = [
            row[".id"] async for row in scheduler.select(_ID).where(And(_NAME == name, _COMMENT == ROLLBACK_COMMENT))
        ]
        if ids:
            await scheduler.remove(*(str(i) for i in ids))

    # -- public api -------------------------------------------------------------

    async def export(
        self,
        *,
        compact: bool = False,
        verbose: bool = False,
        terse: bool = False,
        show_sensitive: bool = False,
        path: str | None = None,
    ) -> str:
        """See :meth:`Config.export`."""
        args = export_args(
            file=EXPORT_FILE, compact=compact, verbose=verbose, terse=terse, show_sensitive=show_sensitive
        )
        # /export overwrites an existing file, so no need to remove it first.
        await self._drain(export_command(path), **args)
        try:
            return normalize_newlines(await self._file_contents(f"{EXPORT_FILE}.rsc"))
        finally:
            await self._safe_file_remove(f"{EXPORT_FILE}.rsc")

    async def apply(
        self,
        text: str | None = None,
        *,
        filename: str | None = None,
        verbose: bool = False,
        dry_run: bool = False,
    ) -> None:
        """See :meth:`Config.apply`."""
        if filename is not None and text is not None:
            raise ValueError("Provide exactly one of 'text' or 'filename'.")
        if filename is not None:
            await self._drain("/import", **import_args(filename=filename, verbose=verbose, dry_run=dry_run))
        elif text is not None:
            # /file/add fails if the file already exists, so remove any stale copy first.
            await self._file_remove(IMPORT_FILE)
            await self.api.path("file").add(name=IMPORT_FILE, contents=text)
            try:
                await self._drain("/import", **import_args(filename=IMPORT_FILE, verbose=verbose, dry_run=dry_run))
            finally:
                await self._safe_file_remove(IMPORT_FILE)
        else:
            raise ValueError("Provide exactly one of 'text' or 'filename'.")

    async def validate(self, text: str) -> None:
        """See :meth:`Config.validate`."""
        await self.apply(text, verbose=True, dry_run=True)

    async def compare(self, candidate: str, *, context: int = 3, **export_kwargs: bool | str | None) -> str:
        """See :meth:`Config.compare`."""
        running = await self.export(**export_kwargs)  # type: ignore[arg-type]
        return compare(running, candidate, context=context)

    async def backup_save(
        self, name: str, *, password: str | None = None, dont_encrypt: bool = True, persistent: bool = False
    ) -> None:
        """See :meth:`Config.backup_save`."""
        target = await self._persistent_path(name) if persistent else name
        await self._drain(
            "/system/backup/save", **backup_save_args(name=target, password=password, dont_encrypt=dont_encrypt)
        )

    async def backup_load(self, name: str, *, password: str | None = None, persistent: bool = False) -> None:
        """See :meth:`Config.backup_load`."""
        target = await self._persistent_path(name) if persistent else name
        await self._drain("/system/backup/load", **backup_load_args(name=target, password=password))

    async def backup_exists(self, name: str, *, persistent: bool = False) -> bool:
        """See :meth:`Config.backup_exists`."""
        target = await self._persistent_path(name) if persistent else name
        rows = [row async for row in self.api.path("file").select(_NAME).where(_NAME == f"{target}.backup")]
        return len(rows) > 0

    async def arm_rollback(
        self, seconds: int, *, name: str = ROLLBACK_NAME, password: str | None = None, policy: str = _ROLLBACK_POLICY
    ) -> None:
        """See :meth:`Config.arm_rollback`."""
        if not isinstance(seconds, int) or seconds < 1:
            raise ValueError("seconds must be a positive integer.")
        # Remove any stale job BEFORE the backup so the backup cannot capture the
        # rollback scheduler itself (which would reboot-loop when restored).
        await self._scheduler_remove(name)
        backup = await self._persistent_path(name)
        await self.backup_save(backup, password=password)
        await self._drain(
            "/system/scheduler/add",
            **scheduler_args(name=name, backup=backup, seconds=seconds, password=password, policy=policy),
        )

    async def cancel_rollback(self, *, name: str = ROLLBACK_NAME) -> None:
        """See :meth:`Config.cancel_rollback`."""
        await self._scheduler_remove(name)
        await self._file_remove(f"{await self._persistent_path(name)}.backup")

    async def rollback_pending(self, *, name: str = ROLLBACK_NAME) -> bool:
        """See :meth:`Config.rollback_pending`."""
        scheduler = self.api.path("system", "scheduler")
        rows = [row async for row in scheduler.select(_NAME).where(And(_NAME == name, _COMMENT == ROLLBACK_COMMENT))]
        return len(rows) > 0

    async def replace(
        self,
        text: str,
        *,
        keep_users: bool = True,
        no_defaults: bool = True,
        name: str = REPLACE_NAME,
    ) -> None:
        """See :meth:`Config.replace`."""
        filename = await self._persistent_path(f"{name}.rsc")
        # /file/add fails if the file already exists, so remove any stale copy first.
        await self._file_remove(filename)
        await self.api.path("file").add(name=filename, contents=text)
        await self._drain(
            "/system/reset-configuration",
            **reset_args(filename=filename, keep_users=keep_users, no_defaults=no_defaults),
        )
