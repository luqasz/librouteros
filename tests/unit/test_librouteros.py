# -*- coding: UTF-8 -*-

import pytest
from mock import (
    patch,
    Mock,
)
from librouteros import (
    defaults,
    Api,
    TrapError,
    connect,
)
from librouteros.login import (
    encode_password,
    login_plain,
    login_token,
)


def test_lib_default_arguments():
    assert {
            'timeout': 10,
            'port': 8728,
            'saddr': '',
            'subclass': Api,
            'encoding': 'ASCII',
            'ssl_wrapper': defaults['ssl_wrapper'],
            'login_methods': (login_token, login_plain),
            } == defaults


def test_password_encoding():
    result = encode_password('259e0bc05acd6f46926dc2f809ed1bba', 'test')
    assert result == '00c7fd865183a43a772dde231f6d0bff13'


def test_non_ascii_password_encoding():
    """Only ascii characters are allowed in password."""
    with pytest.raises(UnicodeEncodeError):
        encode_password(
                token='259e0bc05acd6f46926dc2f809ed1bba',
                password=u'łą'
                )


@patch('librouteros.create_transport')
def test_connect_raises_when_failed_login(transport_mock):
    failed = Mock(name='failed', side_effect=TrapError(message='failed to login'))
    with pytest.raises(TrapError):
        connect(host='127.0.0.1', username='admin', password='', login_methods=(failed, failed))
