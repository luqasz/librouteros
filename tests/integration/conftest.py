import pytest
import os
import hashlib
import requests
from time import sleep
from collections import namedtuple
from subprocess import Popen, PIPE, check_call
from librouteros import connect, ConnectionError


RouterosImage = namedtuple('RouterosImage', ('version', 'sha256', 'id'))

routeros_images = (
    RouterosImage(
        version='6.33.3',
        sha256='be3b9d982d1ffc893ad50d5295a5f4e55f222eb6088cd52ba8d453a6da800a28',
        id='0B7lhzJhvsd-8Z1IyRVFmSVpHcXc',
    ),
)


def download_file(id, destination):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={'id': id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {'id': id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination)


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None


def save_response_content(response, destination):
    CHUNK_SIZE = 32768
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)


def exists(path, sha256):
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest() == sha256
    else:
        return False


def get_api():
    for _ in range(30):
        try:
            return connect('127.0.0.1', 'admin', '', timeout=1)
        except ConnectionError:
            sleep(1)


@pytest.fixture(scope='session', params=routeros_images, ids=lambda v: v.version)
def ros_img(request):
    dst = 'images/routeros_{}.qcow2'.format(request.param.version)
    dst = os.path.join(os.getcwd(), dst)
    if not exists(dst, request.param.sha256):
        download_file(request.param.id, dst)
    return dst


@pytest.fixture(scope='session')
def disk_image(request, ros_img, tmpdir_factory):
    img = str(tmpdir_factory.mktemp('disk_img').join('routeros.qcow2'))
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
        '-vga', 'none',
        '-hda', disk_image,
        '-net', 'user,hostfwd=tcp::8728-:8728',
        '-net', 'nic,model=e1000',
    ]
    proc = Popen(cmd, stdout=PIPE, stdin=PIPE)
    api = get_api()
    yield api
    api.close()
    proc.kill()
