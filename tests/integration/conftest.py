from time import sleep
from os import (
    devnull,
    environ,
)
from random import randint
from subprocess import Popen, check_call
from tempfile import NamedTemporaryFile
import socket
import platform
from pathlib import Path

import pytest
import pytest_asyncio

from librouteros import connect, async_connect
from librouteros.exceptions import LibRouterosError
from librouteros.login import (
    plain,
    token,
    async_plain,
    async_token,
)

DEV_NULL = open(devnull, "w")
VERSION_LOGIN = {
    "6.44.5": {
        "sync": plain,
        "async": async_plain,
    },
    "6.33.3": {
        "sync": token,
        "async": async_token,
    },
}


def api_session(port):
    last_exc = None
    for _ in range(30):
        try:
            return connect(
                host="127.0.0.1",
                port=port,
                username="admin",
                password="",
                timeout=60,
            )
        except (LibRouterosError, socket.error, socket.timeout) as exc:
            last_exc = exc
            sleep(1)
    raise RuntimeError("Could not connect to device. Last exception {}".format(last_exc))


async def api_session_async(port):
    last_exc = None
    for _ in range(30):
        try:
            return await async_connect(
                host="127.0.0.1",
                port=port,
                username="admin",
                password="",
                timeout=60,
            )
        except (LibRouterosError, socket.error, socket.timeout) as exc:
            last_exc = exc
            sleep(1)
    raise RuntimeError("Could not connect to device. Last exception {}".format(last_exc))


def disk_image(version):
    """Create a temporary disk image backed by original one."""
    img = NamedTemporaryFile()
    # Path to backing image must be absolute or relative to new image
    backing_img = Path().joinpath("images/routeros_{}.qcow2".format(version)).absolute()
    cmd = [
        "qemu-img",
        "create",
        "-f",
        "qcow2",
        "-F",
        "qcow2",
        "-b",
        str(backing_img),
        img.name,
    ]
    check_call(cmd, stdout=DEV_NULL)
    return img


def routeros_vm(disk_image):
    # pylint: disable=redefined-outer-name
    port = randint(49152, 65535)
    cmd = [
        "qemu-system-x86_64",
        "-m",
        "64",
        "-display",
        "none",
        "-hda",
        disk_image.name,
        "-net",
        "user,hostfwd=tcp::{}-:8728".format(port),
        "-net",
        "nic,model=virtio",
        "-cpu",
        "max",
    ]
    proc = Popen(cmd, stdout=DEV_NULL, close_fds=True)
    return port, proc


@pytest.fixture(scope="function", params=VERSION_LOGIN.keys())
def routeros_login(request):
    # pylint: disable=redefined-outer-name
    version = request.param
    image = disk_image(version)
    port, proc = routeros_vm(image)
    request.addfinalizer(proc.kill)
    request.addfinalizer(image.close)

    def get_login_method(exc_type):
        return port, VERSION_LOGIN[version][exc_type]

    return get_login_method


@pytest.fixture(scope="function")
def routeros_api(request):
    # pylint: disable=redefined-outer-name
    version = "6.44.5"
    image = disk_image(version)
    port, proc = routeros_vm(image)
    request.addfinalizer(proc.kill)
    request.addfinalizer(image.close)
    return api_session(port=port)


@pytest_asyncio.fixture(scope="function")
async def routeros_api_async(request):
    # pylint: disable=redefined-outer-name
    version = "6.44.5"
    image = disk_image(version)
    port, proc = routeros_vm(image)
    request.addfinalizer(proc.kill)
    request.addfinalizer(image.close)
    return await api_session_async(port=port)
