from getpass import getpass
from librouteros.query import (
        RowItem,
        Path,
        Or,
        And,
        )


import librouteros, sys, logging

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
        login_methods=(librouteros.login_plain,librouteros.login_token)
        )
# for row in api.rawCmd(
#         '/interface/print',
#         '=.proplist=name',
#         '?=name=ether2',
#         '?=name=wlan-lan',
#         '?#|',
#         # '?=disabled=false',
#         # '#&',
#         ):
#     print(row)


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
