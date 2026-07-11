Configuration management
========================

The ``Config`` object provides configuration management (export, import/merge,
compare, backup, replace and a rollback safety net) on top of the binary API. No
SSH/terminal access is required. It targets **RouterOS 7.x**.

Obtain one from an ``Api`` (or ``AsyncApi``):

.. code-block:: python

    cfg = api.config()

    # async version
    cfg = async_api.config()

RouterOS configuration is imperative (an ``/export`` is a list of ``add``/``set``
actions, not declarative state) and has no native, non-reboot commit/rollback.
This object works within those constraints rather than pretending otherwise; read
the notes below before using ``replace()`` or the rollback timer in production.

Export
------

``/export`` returns nothing when run directly over the API, so ``export()``
writes to a temporary file, reads it back and cleans up. Newlines are normalized
to ``\n``; the volatile timestamp header line is left intact (use
``librouteros.compare`` or ``librouteros.config.strip_header`` to normalize it
away for diffing). Configurations larger than the API's inline limit (a few tens
of KB) are read back in chunks via ``/file/read`` (RouterOS 7.13+).

.. code-block:: python

    running = cfg.export()
    running = cfg.export(show_sensitive=True)     # include passwords/keys
    running = cfg.export(path="ip/address")       # scoped: runs /ip/address/export

    # async version
    running = await cfg.export()

Apply / merge
-------------

``apply()`` runs a ``.rsc`` script via ``/import``. Provide exactly one of
``text`` (uploaded to a temporary file first) or ``filename`` (a file already on
the device). This is a merge: the script's own ``add``/``set``/``remove`` actions
are executed in order.

.. code-block:: python

    cfg.apply("/ip address add address=10.0.0.1/24 interface=ether1\n")
    cfg.apply(filename="deploy.rsc")

    # async version
    await cfg.apply(text)

Errors are raised as :class:`~librouteros.exceptions.TrapError` (with line and
column). Import is not transactional: a syntax error aborts before any change is
made, but a valid-but-failing command applies earlier lines and then stops. Use
``validate()`` to dry-run a script first (RouterOS 7.16+):

.. code-block:: python

    cfg.validate(text)   # raises TrapError on any error, applies nothing

Compare
-------

``compare()`` exports the running configuration and returns a human readable
unified diff against a candidate. It is informational, not an executable RouterOS
patch. The module level :func:`librouteros.compare` diffs two strings directly.

.. code-block:: python

    print(cfg.compare(candidate))

    from librouteros import compare
    print(compare(running, candidate))

Backup
------

.. code-block:: python

    cfg.backup_save("before-change")            # writes before-change.backup
    cfg.backup_load("before-change")            # restores and REBOOTS the device

Backups are binary, same-device and same-version. Loading one reboots the device
(the API connection will drop). On devices that keep a RAM disk at the file-system
root, pass ``persistent=True`` (to both ``backup_save`` and ``backup_load``) to
store the backup under ``flash/`` so it survives a reboot. By default a backup with
no password is written unencrypted (it contains secrets); pass a ``password`` to
encrypt it.

Rollback safety net
-------------------

RouterOS has no native commit-confirm. ``arm_rollback()`` emulates one with a
device-side ``/system/scheduler`` job that restores a backup after ``seconds``.
Because the timer lives on the device it fires even if the client dies, the
session is lost, or you lock yourself out, with no safe-mode action limit.

.. code-block:: python

    cfg.arm_rollback(120)          # save a backup + schedule a restore in 120s
    cfg.apply(risky_config)        # push the change
    if still_reachable():
        cfg.cancel_rollback()      # confirm: cancel the scheduled restore
    # otherwise the scheduler fires, restores the backup and reboots

    cfg.rollback_pending()         # True while a rollback is armed

The automatic restore reverts by rebooting, and only within the ``seconds``
window. That is the trade for a net that survives a lock-out. The backup is stored
persistently so it survives the reboot. The scheduler job runs with a policy set
that ``/system backup load`` needs; RouterOS refuses to create the job unless the
API user holds every listed policy, so a restricted account can pass its own
``policy=`` to ``arm_rollback``.

Replace
-------

.. warning::

    ``replace()`` is destructive. It wipes the configuration, reboots and replays
    the supplied script via ``/system reset-configuration run-after-reset``. There
    is **no** automatic rollback for a replace: safe mode is ignored for resets,
    the run-after-reset script must finish within ~2 minutes, and with
    ``no_defaults`` the script must fully establish management connectivity or the
    device becomes unreachable. Ensure out-of-band (console / netinstall) recovery
    is available.

.. code-block:: python

    cfg.replace(full_config)                     # keep_users=True, no_defaults=True

.. note::

    Configuration management requires RouterOS 7.x. Nothing here uses SSH; every
    operation is a plain API command.

.. note::

    These helpers use fixed device-side file and scheduler names
    (``librouteros-export``, ``librouteros-import.rsc``, ``librouteros-rollback``,
    ``librouteros-replace``), so they are not safe to run concurrently against the
    same device from more than one client. Do not reuse those reserved names in your
    own configuration.
