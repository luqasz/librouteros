#-*- coding: UTF-8 -*-

import unittest
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from logging import Logger, NullHandler
from socket import error as sk_error, timeout as sk_timeout

from tests.helpers import make_patches
import librouteros as lr
from librouteros.exc import ConnError, LoginError, CmdError



class PasswordEncoding(unittest.TestCase):


    def test_password_encoding(self):
        self.assertEqual( lr._encpw( '259e0bc05acd6f46926dc2f809ed1bba', 'test'), '00c7fd865183a43a772dde231f6d0bff13' )


class NullLoggerTests(unittest.TestCase):

    def setUp(self):
        self.nl = lr._mkNullLogger()

    def test_creates_logger_instance(self):
        self.assertIsInstance( self.nl, Logger )

    def test_has_only_1_handler(self):
        self.assertEqual( len( self.nl.handlers ), 1 )

    def test_has_null_handler(self):
        self.assertIsInstance( self.nl.handlers[0], NullHandler )


class InitLogin(unittest.TestCase):

    def setUp(self):
        self.api_mock = MagicMock( spec = lr.api.Api )

    def test_calls_run_with_login(self):
        lr._initlogin( self.api_mock )
        self.api_mock.run.assert_called_once_with('/login')

    def test_returns_challenge_response(self):
        self.api_mock.run.return_value = ( {'ret':'string'}, )
        retval = lr._initlogin( self.api_mock )
        self.assertEqual( 'string', retval )


class ObjectsAssembly(unittest.TestCase):


    def setUp(self):
        make_patches(self, (
            ('rwo', 'librouteros.ReaderWriter'),
            ('api','librouteros.Api'),
            ('logger', 'librouteros._mkNullLogger')
            ))

    def test_does_not_call_null_logger_creation_if_provided_with_non_empty_logger(self):
        lr._mkobj('sock', True)
        self.assertEqual(0, self.logger_mock.call_count)

    def test_calls_null_logger_creation_if_not_provided_with(self):
        lr._mkobj('sock', None)
        self.assertEqual(1, self.logger_mock.call_count)

    def test_reader_writer_creation(self):
        lr._mkobj('sock', True)
        self.rwo_mock.assert_caled_once_with( 'sock', True )

    def test_instantiates_api_object_passing_reader_writer_as_parameter(self):
        m = self.rwo_mock.return_value = MagicMock()
        lr._mkobj('sock', None )
        self.api_mock.assert_called_once_with( m )



class Connection(unittest.TestCase):


    def setUp(self):
        make_patches(self, (
            ('create_conn', 'librouteros.create_connection'),
            ('encpw','librouteros._encpw'),
            ('mkobj', 'librouteros._mkobj'),
            ('initlogin', 'librouteros._initlogin')
            ))

        self.api_mock = MagicMock( spec = lr.api.Api )
        self.rwo_mock = MagicMock( spec = lr.connections.ReaderWriter )
        self.mkobj_mock.return_value = ( self.api_mock, self.rwo_mock )


    def test_raises_ConnError_if_socket_error(self):
        self.create_conn_mock.side_effect = sk_error('some error')
        self.assertRaises(ConnError, lr.connect, 'host', 'user', 'password')

    def test_raises_ConnError_if_socket_timeout(self):
        self.create_conn_mock.side_effect = sk_timeout('some error')
        self.assertRaises(ConnError, lr.connect, 'host', 'user', 'password')

    def test_create_connection_with_default_args(self):
        lr.connect('host', 'user', 'password')
        self.create_conn_mock.assert_called_once_with(('host', 8728), 10, ('', 0))

    def test_calls_object_assembly_function(self):
        self.create_conn_mock.return_value = 'socket'
        lr.connect('host','user','pw', logger='logger')
        self.mkobj_mock.assert_called_once_with( 'socket', 'logger' )

    def test_calls_initlogin(self):
        lr.connect('host', 'user', 'pass')
        self.initlogin_mock.assert_called_once_with( self.api_mock )

    def test_calls_api_run_with_username_and_password(self):
        self.encpw_mock.return_value = 'pass'
        lr.connect('host', 'user', 'pass')
        self.api_mock.run.assert_any_call( '/login', {'name':'user', 'response':'pass'} )

    def test_initial_login_raises_LoginError_when_initial_login_fails_with_ConnError(self):
        self.initlogin_mock.side_effect = ConnError
        self.assertRaises( LoginError, lr.connect, 'host', 'user', 'pass' )

    def test_initial_login_raises_LoginError_when_initial_login_fails_with_CmdError(self):
        self.initlogin_mock.side_effect = CmdError
        self.assertRaises( LoginError, lr.connect, 'host', 'user', 'pass' )

    def test_failed_login_with_CmdError_raises_LoginError(self):
        self.api_mock.run.side_effect = CmdError
        self.assertRaises( LoginError, lr.connect,'host','user','pw' )

    def test_failed_login_with_ConnError_raises_LoginError(self):
        self.api_mock.run.side_effect = ConnError
        self.assertRaises( LoginError, lr.connect,'host','user','pw' )

    def test_after_CmdError_calls_rwo_close(self):
        self.api_mock.run.side_effect = CmdError
        with self.assertRaises( LoginError ):
            lr.connect('host', 'user', 'pw')
            self.rwo_mock.close.assert_called_once_with()

    def test_after_initial_login_raises_ConnError_calls_rwo_close(self):
        self.api_mock.run.side_effect = ConnError
        with self.assertRaises( LoginError ):
            lr.connect('host', 'user', 'pw')
            self.rwo_mock.close.assert_called_once_with()

    def test_calls_encode_password(self):
        self.initlogin_mock.return_value = 'chal'
        lr.connect('host','user','pw')
        self.encpw_mock.assert_called_once_with( 'chal', 'pw' )

    def test_returns_api_object(self):
        returning = lr.connect('host', 'user', 'pw')
        self.assertEqual( self.api_mock, returning )


