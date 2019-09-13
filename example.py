from getpass import getpass
from librouteros.query import (
        RowItem,
        Path,
        Or,
        )
import librouteros
import sys
import logging

mainlog = logging.getLogger('librouteros')
console = logging.StreamHandler(sys.stdout)
mainlog.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt='%(message)s')
console.setFormatter(formatter)
mainlog.addHandler(console)


api = librouteros.connect(
        input('hostname: '),
        input('username: '),
        getpass(),
        login_methods=(librouteros.login_plain, librouteros.login_token)
        )

path = Path('/interface', api=api)
name = RowItem('name')
disabled = RowItem('disabled')
for row in path.select(name, disabled).where(
        disabled == 'no',
        Or(
            name == 'ether2',
            name == 'wlan-lan',
            ),
        ):
    print(row)
