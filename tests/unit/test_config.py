# -*- coding: UTF-8 -*-

from unittest.mock import (
    AsyncMock,
    MagicMock,
    call,
)

import pytest

from librouteros.api import Api, AsyncApi, Path
from librouteros.config import (
    EXPORT_FILE,
    IMPORT_FILE,
    ROLLBACK_COMMENT,
    ROLLBACK_NAME,
    AsyncConfig,
    Config,
    backup_load_args,
    backup_save_args,
    compare,
    export_args,
    export_command,
    import_args,
    reset_args,
    ros_quote,
    scheduler_args,
    strip_header,
)
from librouteros.exceptions import ConnectionClosed, TrapError

# --------------------------------------------------------------------------- #
# Pure argument builders (the RouterOS command contract)
# --------------------------------------------------------------------------- #


def test_export_args_default():
    assert export_args(file="x", compact=False, verbose=False, terse=False, show_sensitive=False) == {"file": "x"}


def test_export_args_all_flags():
    assert export_args(file="x", compact=True, verbose=True, terse=True, show_sensitive=True) == {
        "file": "x",
        "compact": True,
        "verbose": True,
        "terse": True,
        "show-sensitive": True,
    }


@pytest.mark.parametrize(
    ("path", "command"),
    (
        (None, "/export"),
        ("ip/address", "/ip/address/export"),
        ("/ip/address/", "/ip/address/export"),
    ),
)
def test_export_command(path, command):
    # RouterOS has no path= parameter; a scoped export runs from within the menu.
    assert export_command(path) == command


def test_import_args_plain():
    assert import_args(filename="x.rsc", verbose=False, dry_run=False) == {"file-name": "x.rsc"}


def test_import_args_verbose():
    assert import_args(filename="x.rsc", verbose=True, dry_run=False) == {"file-name": "x.rsc", "verbose": True}


def test_import_args_dry_run_implies_verbose():
    """RouterOS rejects dry-run unless verbose is also set."""
    assert import_args(filename="x.rsc", verbose=False, dry_run=True) == {
        "file-name": "x.rsc",
        "verbose": True,
        "dry-run": True,
    }


def test_backup_save_args_unencrypted_by_default():
    assert backup_save_args(name="b", password=None, dont_encrypt=True) == {"name": "b", "dont-encrypt": True}


def test_backup_save_args_password_wins_over_dont_encrypt():
    assert backup_save_args(name="b", password="pw", dont_encrypt=True) == {"name": "b", "password": "pw"}  # noqa S106


def test_backup_save_args_encrypted_no_password():
    assert backup_save_args(name="b", password=None, dont_encrypt=False) == {"name": "b"}


def test_backup_load_args_requires_password_field():
    # /system/backup/load needs the password parameter even when unencrypted (empty).
    assert backup_load_args(name="b", password=None) == {"name": "b", "password": ""}
    assert backup_load_args(name="b", password="pw") == {"name": "b", "password": "pw"}  # noqa S106


def test_scheduler_args():
    args = scheduler_args(name=ROLLBACK_NAME, backup=ROLLBACK_NAME, seconds=300, password=None, policy="reboot,read")
    assert args["name"] == ROLLBACK_NAME
    assert args["interval"] == "300s"
    assert args["on-event"] == f'/system backup load name="{ROLLBACK_NAME}" password=""'
    assert args["policy"] == "reboot,read"


def test_scheduler_args_loads_the_resolved_backup_path():
    # The job name and the backup file can differ (backup carries the persistent path).
    args = scheduler_args(name=ROLLBACK_NAME, backup="flash/rb", seconds=10, password=None, policy="reboot")
    assert args["on-event"] == '/system backup load name="flash/rb" password=""'


def test_scheduler_args_password_embedded():
    args = scheduler_args(name=ROLLBACK_NAME, backup=ROLLBACK_NAME, seconds=10, password="pw", policy="reboot")  # noqa S106
    assert args["on-event"] == f'/system backup load name="{ROLLBACK_NAME}" password="pw"'


@pytest.mark.parametrize(
    ("value", "quoted"),
    (
        ("plain", '"plain"'),
        ("pre upgrade", '"pre upgrade"'),
        ("a$b", '"a\\$b"'),
        ('a"b', '"a\\"b"'),
        ("a\\b", '"a\\\\b"'),
        ("a\nb", '"a\\nb"'),
        ("a\rb", '"a\\rb"'),
    ),
)
def test_ros_quote_escapes_script_special_chars(value, quoted):
    assert ros_quote(value) == quoted


def test_scheduler_args_quotes_special_chars():
    # A password containing '$' must not break the on-event script.
    args = scheduler_args(name="pre upgrade", backup="pre upgrade", seconds=10, password="p$ss", policy="reboot")  # noqa S106
    assert args["on-event"] == '/system backup load name="pre upgrade" password="p\\$ss"'


def test_reset_args_defaults():
    assert reset_args(filename="flash/x.rsc", keep_users=True, no_defaults=True) == {
        "run-after-reset": "flash/x.rsc",
        "no-defaults": True,
        "keep-users": True,
    }


def test_reset_args_minimal():
    assert reset_args(filename="x.rsc", keep_users=False, no_defaults=False) == {"run-after-reset": "x.rsc"}


# --------------------------------------------------------------------------- #
# Diff / normalization helpers
# --------------------------------------------------------------------------- #


def test_strip_header():
    text = "# 2026-07-11 21:04:13 by RouterOS 7.21.5\n/ip address\n"
    assert strip_header(text) == "# by RouterOS 7.21.5\n/ip address\n"


def test_compare_identical_is_empty():
    cfg = "/ip address\nadd address=1.1.1.1/24\n"
    assert compare(cfg, cfg) == ""


def test_compare_ignores_header_and_crlf():
    a = "# 2026-01-01 00:00:00 by RouterOS 7.21.5\r\n/ip address\r\n"
    b = "# 2020-05-05 12:00:00 by RouterOS 7.21.5\n/ip address\n"
    assert compare(a, b) == ""


def test_compare_shows_added_line():
    a = "/ip address\nadd address=1.1.1.1/24\n"
    b = "/ip address\nadd address=1.1.1.1/24\nadd address=2.2.2.2/24\n"
    diff = compare(a, b)
    assert "+add address=2.2.2.2/24" in diff
    assert diff.startswith("--- running")


# --------------------------------------------------------------------------- #
# Config orchestration (helpers mocked; verify command flow + cleanup)
# --------------------------------------------------------------------------- #


def _config_with_mocked_helpers():
    cfg = Config(api=MagicMock(return_value=[]))
    cfg._file_remove = MagicMock()
    cfg._file_contents = MagicMock(return_value="line1\r\nline2\r\n")
    cfg._scheduler_remove = MagicMock()
    cfg._persistent_path = MagicMock(side_effect=lambda name: f"flash/{name}")
    return cfg


def test_export_reads_and_cleans_up():
    cfg = _config_with_mocked_helpers()
    result = cfg.export()
    assert result == "line1\nline2\n"  # newlines normalized, header untouched
    cfg.api.assert_called_once_with("/export", file=EXPORT_FILE)
    # /export overwrites, so the file is only removed afterwards (cleanup)
    cfg._file_remove.assert_called_once_with(f"{EXPORT_FILE}.rsc")
    cfg._file_contents.assert_called_once_with(f"{EXPORT_FILE}.rsc")


def test_export_passes_flags():
    cfg = _config_with_mocked_helpers()
    cfg.export(terse=True, show_sensitive=True)
    cfg.api.assert_called_once_with("/export", file=EXPORT_FILE, terse=True, **{"show-sensitive": True})


def test_export_scoped_path_uses_menu_command():
    cfg = _config_with_mocked_helpers()
    cfg.export(path="ip/address")
    cfg.api.assert_called_once_with("/ip/address/export", file=EXPORT_FILE)


def test_apply_text_uploads_imports_and_cleans_up():
    cfg = _config_with_mocked_helpers()
    cfg.apply("/ip address add address=1.1.1.1/24\n")
    cfg.api.path.return_value.add.assert_called_once_with(
        name=IMPORT_FILE, contents="/ip address add address=1.1.1.1/24\n"
    )
    cfg.api.assert_called_once_with("/import", **{"file-name": IMPORT_FILE})
    # stale removed before add, temp removed after import
    assert cfg._file_remove.call_args_list == [call(IMPORT_FILE), call(IMPORT_FILE)]


def test_apply_text_cleans_up_even_on_error():
    cfg = _config_with_mocked_helpers()
    cfg.api = MagicMock(side_effect=TrapError(message="Script Error"))
    with pytest.raises(TrapError):
        cfg.apply("/bogus\n")
    # temp file still removed in the finally block
    assert call(IMPORT_FILE) in cfg._file_remove.call_args_list
    assert cfg._file_remove.call_args_list[-1] == call(IMPORT_FILE)


def test_apply_filename_does_not_upload_or_clean():
    cfg = _config_with_mocked_helpers()
    cfg.apply(filename="onbox.rsc")
    cfg.api.path.return_value.add.assert_not_called()
    cfg._file_remove.assert_not_called()
    cfg.api.assert_called_once_with("/import", **{"file-name": "onbox.rsc"})


def test_apply_finally_does_not_mask_original_error():
    # If the imported config cuts our own access, the finally cleanup fails too; the
    # original import error must still propagate, not the cleanup's ConnectionClosed.
    cfg = _config_with_mocked_helpers()
    cfg.api = MagicMock(side_effect=TrapError(message="import failed"))
    # stale-removal (1st call) succeeds; the finally cleanup (2nd call) fails
    cfg._file_remove = MagicMock(side_effect=[None, ConnectionClosed("connection dropped")])
    with pytest.raises(TrapError, match="import failed"):
        cfg.apply("/some/config\n")


@pytest.mark.parametrize(
    ("text", "filename"),
    (
        (None, None),
        ("cfg", "file.rsc"),
    ),
)
def test_apply_rejects_ambiguous_source(text, filename):
    cfg = _config_with_mocked_helpers()
    with pytest.raises(ValueError, match="exactly one"):
        cfg.apply(text, filename=filename)


def test_validate_is_dry_run():
    cfg = _config_with_mocked_helpers()
    cfg.apply = MagicMock()
    cfg.validate("/ip address\n")
    cfg.apply.assert_called_once_with("/ip address\n", verbose=True, dry_run=True)


def test_backup_save_and_load_commands():
    cfg = _config_with_mocked_helpers()
    cfg.backup_save("snap")
    cfg.api.assert_called_with("/system/backup/save", name="snap", **{"dont-encrypt": True})
    cfg.api.reset_mock()
    cfg.backup_load("snap")
    cfg.api.assert_called_with("/system/backup/load", name="snap", password="")


def test_backup_save_persistent_uses_flash_path():
    cfg = _config_with_mocked_helpers()  # _persistent_path mock prepends "flash/"
    cfg.backup_save("snap", persistent=True)
    cfg.api.assert_called_once_with("/system/backup/save", name="flash/snap", **{"dont-encrypt": True})


def test_backup_load_persistent_uses_flash_path():
    cfg = _config_with_mocked_helpers()
    cfg.backup_load("snap", persistent=True)
    cfg.api.assert_called_once_with("/system/backup/load", name="flash/snap", password="")


def test_arm_rollback_saves_backup_and_adds_scheduler():
    cfg = _config_with_mocked_helpers()
    cfg.arm_rollback(300)
    calls = [c.args[0] for c in cfg.api.call_args_list]
    assert calls == ["/system/backup/save", "/system/scheduler/add"]
    cfg._scheduler_remove.assert_called_once_with(ROLLBACK_NAME)
    sched_kwargs = cfg.api.call_args_list[-1].kwargs
    assert sched_kwargs["name"] == ROLLBACK_NAME
    assert sched_kwargs["interval"] == "300s"


@pytest.mark.parametrize("bad", (0, -5, 0.5, 30.0))
def test_arm_rollback_rejects_non_positive_or_fractional(bad):
    # A fractional value would truncate to interval=0s and never fire.
    cfg = _config_with_mocked_helpers()
    with pytest.raises(ValueError, match="positive integer"):
        cfg.arm_rollback(bad)


def test_arm_rollback_removes_stale_job_before_backup():
    # The stale scheduler must be removed before the backup is taken, otherwise the
    # backup captures the rollback job and restoring it reboot-loops.
    cfg = _config_with_mocked_helpers()
    manager = MagicMock()
    cfg._scheduler_remove = manager.scheduler_remove
    cfg.backup_save = manager.backup_save
    cfg.arm_rollback(60)
    ordered = [c[0] for c in manager.mock_calls]
    assert ordered.index("scheduler_remove") < ordered.index("backup_save")


def test_cancel_rollback_removes_scheduler_and_persistent_backup():
    cfg = _config_with_mocked_helpers()  # _persistent_path mock prepends "flash/"
    cfg.cancel_rollback()
    cfg._scheduler_remove.assert_called_once_with(ROLLBACK_NAME)
    cfg._file_remove.assert_called_once_with(f"flash/{ROLLBACK_NAME}.backup")


def test_replace_uploads_then_resets():
    cfg = _config_with_mocked_helpers()
    cfg.replace("/ip address add address=1.1.1.1/24\n")
    cfg._persistent_path.assert_called_once_with("librouteros-replace.rsc")
    cfg.api.path.return_value.add.assert_called_once_with(
        name="flash/librouteros-replace.rsc", contents="/ip address add address=1.1.1.1/24\n"
    )
    cfg.api.assert_called_once_with(
        "/system/reset-configuration",
        **{"run-after-reset": "flash/librouteros-replace.rsc", "no-defaults": True, "keep-users": True},
    )


# --------------------------------------------------------------------------- #
# Query-builder helpers, exercised through a small filtering fake
# --------------------------------------------------------------------------- #


class FilteringFake:
    """
    Minimal fake Api that serves ``*/print`` queries built by the query DSL and
    records ``*/remove`` calls. Real librouteros Path/Query run on top of it.
    """

    def __init__(self, rows, blobs=None, version="7.21.5"):
        self.rows = rows  # {"/file/print": [ {...}, ... ]}
        self.blobs = blobs or {}  # {name: full-text} served by /file/read
        self.version = version
        self.removed = []

    def rawCmd(self, cmd, *words):
        filters = []
        for word in words:
            if word.startswith("?="):
                _, key, value = word.split("=", 2)
                filters.append((key, value))
        return iter([row for row in self.rows.get(cmd, []) if all(str(row.get(k)) == v for k, v in filters)])

    def __call__(self, cmd, **kwargs):
        if cmd == "/system/resource/print":
            return iter([{"version": self.version}])
        if cmd == "/file/read":
            blob = self.blobs.get(kwargs["file"], "")
            offset, size = kwargs["offset"], kwargs["chunk-size"]
            return iter([{"data": blob[offset : offset + size]}])
        if cmd.endswith("/remove"):
            self.removed.append(kwargs)
        return iter([])

    def path(self, *path):
        return Path(path="", api=self).join(*path)


def test_file_contents_returns_value():
    fake = FilteringFake({"/file/print": [{".id": "*1", "name": "a.rsc", "contents": "hello"}]})
    assert Config(api=fake)._file_contents("a.rsc") == "hello"


def test_file_contents_missing_raises():
    fake = FilteringFake({"/file/print": []})
    with pytest.raises(FileNotFoundError):
        Config(api=fake)._file_contents("missing.rsc")


def test_file_contents_large_file_reads_in_chunks():
    # Big files omit the 'contents' attribute; must chunk-read, never return "".
    big = "".join(f"line {i}\n" for i in range(20000))  # > _READ_CHUNK bytes
    fake = FilteringFake(
        {"/file/print": [{".id": "*1", "name": "big.rsc", "size": len(big)}]},  # no 'contents'
        blobs={"big.rsc": big},
    )
    assert Config(api=fake)._file_contents("big.rsc") == big


def test_file_contents_large_file_pre_7_13_raises():
    # /file/read is 7.13+; on older versions reading a big file must not silently return "".
    fake = FilteringFake(
        {"/file/print": [{".id": "*1", "name": "big.rsc", "size": 999999}]},  # no 'contents'
        version="7.12.0",
    )
    with pytest.raises(NotImplementedError, match=r"7\.13"):
        Config(api=fake)._file_contents("big.rsc")


def test_backup_exists():
    present = FilteringFake({"/file/print": [{".id": "*1", "name": "snap.backup"}]})
    absent = FilteringFake({"/file/print": []})
    assert Config(api=present).backup_exists("snap") is True
    assert Config(api=absent).backup_exists("snap") is False


def test_file_remove_removes_by_id():
    fake = FilteringFake({"/file/print": [{".id": "*7", "name": "a.rsc"}]})
    Config(api=fake)._file_remove("a.rsc")
    assert fake.removed == [{".id": "*7"}]


def test_file_remove_absent_is_noop():
    fake = FilteringFake({"/file/print": []})
    Config(api=fake)._file_remove("a.rsc")
    assert fake.removed == []


def test_rollback_pending_matches_our_job():
    present = FilteringFake(
        {"/system/scheduler/print": [{".id": "*1", "name": ROLLBACK_NAME, "comment": ROLLBACK_COMMENT}]}
    )
    absent = FilteringFake({"/system/scheduler/print": []})
    assert Config(api=present).rollback_pending() is True
    assert Config(api=absent).rollback_pending() is False


def test_rollback_pending_ignores_foreign_job_with_same_name():
    # A user scheduler that happens to share the reserved name is not ours.
    foreign = FilteringFake({"/system/scheduler/print": [{".id": "*1", "name": ROLLBACK_NAME, "comment": "user job"}]})
    assert Config(api=foreign).rollback_pending() is False


def test_has_flash_detection():
    withflash = FilteringFake({"/file/print": [{".id": "*1", "name": "flash", "type": "directory"}]})
    without = FilteringFake({"/file/print": []})
    assert Config(api=withflash)._persistent_path("x.rsc") == "flash/x.rsc"
    assert Config(api=without)._persistent_path("x.rsc") == "x.rsc"


# --------------------------------------------------------------------------- #
# Async parity (helpers mocked)
# --------------------------------------------------------------------------- #


async def test_async_export_orchestration():
    cfg = AsyncConfig(api=MagicMock())
    cfg._drain = AsyncMock(return_value=[])
    cfg._file_remove = AsyncMock()
    cfg._file_contents = AsyncMock(return_value="a\r\nb\r\n")
    result = await cfg.export()
    assert result == "a\nb\n"
    cfg._drain.assert_awaited_once_with("/export", file=EXPORT_FILE)
    cfg._file_contents.assert_awaited_once_with(f"{EXPORT_FILE}.rsc")


async def test_async_arm_rollback_removes_stale_job_before_backup():
    # Async mirror of the sync ordering fix: remove the stale job before the backup.
    cfg = AsyncConfig(api=MagicMock())
    cfg._drain = AsyncMock(return_value=[])
    order = []
    cfg._scheduler_remove = AsyncMock(side_effect=lambda *a, **k: order.append("remove"))
    cfg.backup_save = AsyncMock(side_effect=lambda *a, **k: order.append("backup"))
    await cfg.arm_rollback(60)
    assert order == ["remove", "backup"]


async def test_async_apply_uploads_and_cleans_up():
    cfg = AsyncConfig(api=MagicMock())
    cfg._drain = AsyncMock(return_value=[])
    cfg._file_remove = AsyncMock()
    cfg.api.path.return_value.add = AsyncMock()
    await cfg.apply("/ip address add address=1.1.1.1/24\n")
    cfg.api.path.return_value.add.assert_awaited_once_with(
        name=IMPORT_FILE, contents="/ip address add address=1.1.1.1/24\n"
    )
    cfg._drain.assert_awaited_once_with("/import", **{"file-name": IMPORT_FILE})


def test_api_config_accessor_returns_config():
    cfg = Api(protocol=MagicMock()).config()
    assert isinstance(cfg, Config)


def test_async_api_config_accessor_returns_async_config():
    cfg = AsyncApi(protocol=MagicMock()).config()
    assert isinstance(cfg, AsyncConfig)
