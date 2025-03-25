from os import (
    devnull,
)
from random import randint
from subprocess import Popen, check_call, PIPE
from tempfile import NamedTemporaryFile
import socket
from pathlib import Path

import pytest
import pytest_asyncio
import stamina

from librouteros import connect, async_connect
from librouteros.login import (
    plain,
    token,
    async_plain,
    async_token,
)

DEV_NULL = open(devnull, "w")

# All routeros vms which can be launched.
ROUTEROS_VMS = {
    "6.33.3": {
        "sync": token,
        "async": async_token,
        "username": "admin",
        "password": "",
    },
    "7.18.2": {
        "sync": plain,
        "async": async_plain,
        "username": "admin",
        "password": "password",
    },
}

# Routeros vms which differ in login methods.
ROUTEROS_LOGIN_VMS = ("7.18.2", "6.33.3")


def setup_qemu_disk(version):
    """Create a temporary disk image backed by original one."""
    img = NamedTemporaryFile()
    # Path to backing image must be absolute or relative to new image
    backing_img = Path().joinpath(f"images/routeros_{version}.qcow2").absolute()
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


def setup_qemu_vm(disk_image):
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
        "-accel",
        "tcg",
    ]
    proc = Popen(cmd, stdout=DEV_NULL, stderr=PIPE, close_fds=True)
    if proc.poll() is not None and proc.poll() != 0:
        raise pytest.fail("Failed to execute qemu {}".format(proc.stderr.read()))
    return port, proc


@pytest.fixture(params=ROUTEROS_VMS.keys())
def routeros_vm(request):
    """
    Setup routeros VM and return connect() arguments callable.
    """
    version = request.param
    host = "localhost"
    image = setup_qemu_disk(version)
    port, proc = setup_qemu_vm(image)
    request.addfinalizer(proc.kill)
    request.addfinalizer(image.close)
    for attempt in stamina.retry_context(
        on=(socket.error, socket.timeout),
        wait_initial=1,
        timeout=90,
    ):
        with attempt:
            sock = socket.create_connection((host, port), 1, ("", 0))
            sock.close()

    def params(ltype):
        return {
            "host": host,
            "port": port,
            "login_method": ROUTEROS_VMS[version][ltype],
            "timeout": 90,
            "username": ROUTEROS_VMS[version]["username"],
            "password": ROUTEROS_VMS[version]["password"],
        }

    return params


@pytest.fixture()
def routeros_api_sync(request, routeros_vm):
    return connect(**routeros_vm("sync"))


@pytest_asyncio.fixture()
async def routeros_api_async(request, routeros_vm):
    return await async_connect(**routeros_vm("async"))
