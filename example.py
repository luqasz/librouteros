from getpass import getpass
from librouteros.query import (
        Key,
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

name = Key('name')
rates = Key('supported-rates-a/g')
for row in api.path('/interface/wireless').select(name, rates):
    print(row)
