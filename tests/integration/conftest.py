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

import pytest
import py.path

from librouteros import connect
from librouteros.exceptions import LibRouterosError
from librouteros.login import (
    plain,
    token,
)

DEV_NULL = open(devnull, 'w')
VERSION_LOGIN = {'6.43rc21': plain, '6.33.3': token}


def api_session(login_method, port):
    last_exc = None
    for _ in range(30):
        try:
            return connect(
                host='127.0.0.1',
                port=port,
                username='admin',
                password='',
                login_method=login_method,
            )
        except (LibRouterosError, socket.error, socket.timeout) as exc:
            last_exc = exc
            sleep(1)
    raise RuntimeError('Could not connect to device. Last exception {}'.format(last_exc))


@pytest.fixture(scope='function', params=VERSION_LOGIN.keys())
def disk_image(request):
    """Create a temporary disk image backed by original one."""
    img = NamedTemporaryFile()
    request.addfinalizer(img.close)
    # Path to backing image must be absolute or relative to new image
    backing_img = str(py.path.local().join('images/routeros_{}.qcow2'.format(request.param)))
    cmd = [
        'qemu-img',
        'create',
        '-f',
        'qcow2',
        '-b',
        backing_img,
        img.name,
    ]
    check_call(cmd, stdout=DEV_NULL)
    return (img.name, request.param)


@pytest.fixture(scope='function')
def routeros(request, disk_image):
    #pylint: disable=redefined-outer-name
    image, version = disk_image
    port = randint(49152, 65535)
    accel = {
        'Darwin': 'hvf',
        'Linux': 'kvm',
    }
    if environ.get('TRAVIS') and environ.get('CI'):
        accel['Linux'] = 'tcg'
    cmd = [
        'qemu-system-x86_64',
        '-m',
        '64',
        '-display',
        'none',
        '-hda',
        image,
        '-net',
        'user,hostfwd=tcp::{}-:8728'.format(port),
        '-net',
        'nic,model=e1000',
        '-cpu',
        'max',
        '-accel',
        accel[platform.system()],
    ]
    proc = Popen(cmd, stdout=DEV_NULL, close_fds=True)
    request.addfinalizer(proc.kill)
    return api_session(login_method=VERSION_LOGIN[version], port=port)
