import pytest

from librouteros.config import ROLLBACK_NAME
from librouteros.exceptions import TrapError
from librouteros.query import Key

# The config-management engine targets RouterOS 7.x. Some primitives used here
# (notably /import dry-run) only exist on 7.16+, so skip on older devices.

_NAME = Key("name")
_ID = Key(".id")


def _major(api):
    resource = next(iter(api("/system/resource/print")))
    return int(str(resource["version"]).split(".", 1)[0])


def _skip_pre7(api):
    if _major(api) < 7:
        pytest.skip("config management requires RouterOS 7.x")


def _addresses(api):
    return [row.get("address") for row in api("/ip/address/print")]


def _remove_addresses_with_comment(api, comment):
    for row in api("/ip/address/print", **{".proplist": ".id,comment"}):
        if row.get("comment") == comment:
            tuple(api("/ip/address/remove", **{".id": row[".id"]}))


def test_export_returns_running_config(routeros_api_sync):
    api = routeros_api_sync
    _skip_pre7(api)
    config = api.config().export()
    assert isinstance(config, str)
    assert config.strip()
    assert "\r\n" not in config  # newlines normalized
    assert "# " in config  # export header present


def test_apply_merge_then_visible(routeros_api_sync):
    api = routeros_api_sync
    _skip_pre7(api)
    cfg = api.config()
    comment = "librouteros-it-merge"
    try:
        cfg.apply(f"/ip address add address=10.99.1.1/24 interface=ether1 comment={comment}\r\n")
        assert "10.99.1.1/24" in _addresses(api)
    finally:
        _remove_addresses_with_comment(api, comment)
    assert "10.99.1.1/24" not in _addresses(api)


def test_apply_bad_script_raises_and_changes_nothing(routeros_api_sync):
    api = routeros_api_sync
    _skip_pre7(api)
    cfg = api.config()
    before = _addresses(api)
    with pytest.raises(TrapError):
        cfg.apply("/ip address add address=10.99.2.1/24 interface=ether1\r\n/bogus/path set x=1\r\n")
    # syntax error aborts the import before applying anything
    assert _addresses(api) == before


def test_validate_accepts_good_script(routeros_api_sync):
    api = routeros_api_sync
    _skip_pre7(api)
    cfg = api.config()
    before = _addresses(api)
    cfg.validate("/ip address add address=10.99.3.1/24 interface=ether1\r\n")  # must not raise
    assert _addresses(api) == before  # dry-run never applies anything


def test_validate_rejects_bad_script(routeros_api_sync):
    api = routeros_api_sync
    _skip_pre7(api)
    cfg = api.config()
    before = _addresses(api)
    with pytest.raises(TrapError):
        cfg.validate("/bogus/path set x=1\r\n")
    assert _addresses(api) == before  # nothing applied


def test_compare_detects_added_line(routeros_api_sync):
    api = routeros_api_sync
    _skip_pre7(api)
    cfg = api.config()
    running = cfg.export()
    candidate = running + "/ip address add address=10.99.4.1/24 interface=ether1\n"
    diff = cfg.compare(candidate)
    assert "+/ip address add address=10.99.4.1/24 interface=ether1" in diff


def test_rollback_arm_pending_cancel(routeros_api_sync):
    api = routeros_api_sync
    _skip_pre7(api)
    cfg = api.config()

    def scheduler_names():
        return [row.get("name") for row in api("/system/scheduler/print", **{".proplist": "name"})]

    def file_names():
        return [row.get("name") for row in api("/file/print", **{".proplist": "name"})]

    assert cfg.rollback_pending() is False
    try:
        cfg.arm_rollback(300)
        assert cfg.rollback_pending() is True
        assert ROLLBACK_NAME in scheduler_names()
        assert f"{ROLLBACK_NAME}.backup" in file_names()
    finally:
        cfg.cancel_rollback()
    assert cfg.rollback_pending() is False
    assert ROLLBACK_NAME not in scheduler_names()
    assert f"{ROLLBACK_NAME}.backup" not in file_names()


def test_export_leaves_no_temp_file(routeros_api_sync):
    api = routeros_api_sync
    _skip_pre7(api)
    cfg = api.config()
    cfg.export()
    names = [str(row.get("name", "")) for row in api("/file/print", **{".proplist": "name"})]
    assert not any(name.startswith("librouteros-export") for name in names)


@pytest.mark.asyncio
async def test_async_export_and_merge(routeros_api_async):
    api = routeros_api_async
    resource = await anext(api("/system/resource/print"))
    if int(str(resource["version"]).split(".", 1)[0]) < 7:
        pytest.skip("config management requires RouterOS 7.x")
    cfg = api.config()
    config = await cfg.export()
    assert config.strip()

    comment = "librouteros-it-async"
    try:
        await cfg.apply(f"/ip address add address=10.99.5.1/24 interface=ether1 comment={comment}\r\n")
        addresses = [row.get("address") async for row in api("/ip/address/print")]
        assert "10.99.5.1/24" in addresses
    finally:
        async for row in api("/ip/address/print", **{".proplist": ".id,comment"}):
            if row.get("comment") == comment:
                await api.path("ip", "address").remove(str(row[".id"]))


@pytest.mark.skip(reason="destructive: reboots the device; run manually against a disposable device")
def test_replace_reboots_into_new_config(routeros_api_sync):
    api = routeros_api_sync
    _skip_pre7(api)
    cfg = api.config()
    cfg.replace(cfg.export() + "/system identity set name=REPLACED\r\n")
