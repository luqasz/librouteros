from time import sleep
from os import devnull
from subprocess import Popen, check_call
from tempfile import NamedTemporaryFile
import socket

import pytest
import py.path

from librouteros import connect
from librouteros.exceptions import LibRouterosError

DEV_NULL = open(devnull, 'w')


def api_session():
    for x in range(30):
        try:
            return connect(host='127.0.0.1', port=8728, username='admin', password='')
        except (LibRouterosError, socket.error, socket.timeout):
            sleep(1)
    else:
        raise LibRouterosError('could not connect to device')


@pytest.fixture(scope='session', params=('6.33.3', '6.43rc21'))
def disk_image(request):
    """Create a temporary disk image backed by original one."""
    img = NamedTemporaryFile()
    request.addfinalizer(img.close)
    cmd = [
        'qemu-img',
        'create',
        '-f',
        'qcow2',
        '-b',
                                                                                     # Path to backing file must be absolute or relative to new image
        str(py.path.local().join('images/routeros_{}.qcow2'.format(request.param))),
        img.name,
    ]
    check_call(cmd, stdout=DEV_NULL)
    return img.name


@pytest.fixture(scope='session')
def routeros(request, disk_image):
    cmd = [
        'qemu-system-i386',
        '-m',
        '64',
        '-display',
        'none',
        '-hda',
        disk_image,
        '-net',
        'user,hostfwd=tcp::8728-:8728',
        '-net',
        'nic,model=e1000',
    ]
    proc = Popen(cmd, stdout=DEV_NULL, close_fds=True)
    request.addfinalizer(proc.kill)
    return api_session()
