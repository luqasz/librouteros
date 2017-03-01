import pytest
import os
import py.path
from time import sleep
from subprocess import Popen, PIPE, check_call
from librouteros import connect, ConnectionError


def get_api():
    for _ in range(30):
        try:
            return connect('127.0.0.1', 'admin', '', timeout=1)
        except ConnectionError:
            sleep(1)


@pytest.fixture(scope='session', params=('6.33.3',))
def ros_img(request):
    """Return absolute path to backing disk image."""
    return os.path.join(os.getcwd(), 'images/routeros_{}.qcow2'.format(request.param))


@pytest.yield_fixture(scope='session')
def img_tmpdir():
    """Return py.path.local temporary directory and remove it at the end."""
    path = py.path.local.mkdtemp()
    yield path
    path.remove()


@pytest.fixture(scope='session')
def disk_image(request, ros_img, img_tmpdir):
    img = str(img_tmpdir.join('routeros.qcow2'))
    cmd = [
        'qemu-img', 'create',
        '-f', 'qcow2',
        # Path to backing file must be absolute or relative to new image
        '-b', ros_img,
        img,
    ]
    check_call(cmd)
    return img


@pytest.yield_fixture(scope='session')
def routeros(request, disk_image):
    cmd = [
        'qemu-system-i386',
        '-m', '64',
        '-nographic',
        '-hda', disk_image,
        '-net', 'user,hostfwd=tcp::8728-:8728',
        '-net', 'nic,model=e1000',
    ]
    proc = Popen(cmd, stdout=PIPE, stdin=PIPE)
    api = get_api()
    yield api
    api.close()
    proc.kill()
