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
)


def test_default_ssl_wrapper():
    """Assert that wrapper returns same object as it was called with."""
    assert defaults['ssl_wrapper'](int) is int


@pytest.mark.parametrize("key, value",(
    ('timeout', 10),
    ('port', 8728),
    ('saddr', ''),
    ('subclass', Api),
    ('encoding', 'ASCII'),
    ('login_method', login_plain),
))
def test_defaults(key, value):
    assert defaults[key] == value


def test_default_keys():
    assert set(defaults.keys()) == set((
            'timeout',
            'port',
            'saddr',
            'subclass',
            'encoding',
            'login_method',
            'ssl_wrapper'
            ))


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
        connect(host='127.0.0.1', username='admin', password='', login_method=failed)
