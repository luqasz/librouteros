# -*- coding: UTF-8 -*-

from librouteros.exceptions import TrapError


def test_TrapError_newlines():
    r"""Assert that string representation replaces \r\n with comma."""
    error = TrapError(message='some\r\n string')
    assert str(error) == 'some, string'
