# -*- coding: UTF-8 -*-

import unittest
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from librouteros.api import Api
from librouteros.exc import CmdError, ConnError, LibError
from librouteros.connections import ReaderWriter
from tests.helpers import make_patches

class RunMethod(unittest.TestCase):


    def setUp(self):
        make_patches( self, (
            ( 'parsresp','librouteros.api.parsresp' ),
            ( 'mksnt','librouteros.api.mksnt' ),
            ( 'trapcheck','librouteros.api.trapCheck' ),
            ( 'raisefatal', 'librouteros.api.raiseIfFatal' )
                ))

        rwo = MagicMock( spec = ReaderWriter )
        self.api = Api( rwo )
        self.api.close = MagicMock()
        self.api._readDone = MagicMock()


    def test_calls_mksnt(self):
        self.api.run( 'some level' )
        self.mksnt_mock.assert_called_once_with( dict() )

    def test_calls_write_sentence_with_combined_tuple(self):
        lvl = '/ip/address'
        retval = ('=key=value',)
        self.mksnt_mock.return_value = ( retval )
        self.api.run( lvl, 'some args' )
        self.api.rwo.writeSnt.assert_called_once_with( (lvl,) + retval )

    def test_calls_readdone(self):
        self.api.run( 'some string' )
        self.api._readDone.assert_called_once_with()

    def test_calls_trapCheck(self):
        self.api._readDone.return_value = ( 'some read sentence' )
        self.api.run( 'some level' )
        self.trapcheck_mock.assert_called_once_with( 'some read sentence' )

    def test_calls_parsresp(self):
        self.api._readDone.return_value = 'read sentence'
        self.api.run( 'some level' )
        self.parsresp_mock.assert_called_once_with( 'read sentence' )

    def test_checks_for_fatal_condition(self):
        self.api._readDone.return_value = ( 'some read sentence' )
        self.api.run( 'some level' )
        self.raisefatal_mock.assert_called_once_with( 'some read sentence' )

    def test_raises_CmdError_if_trap_in_sentence(self):
        self.trapcheck_mock.side_effect = CmdError()
        self.assertRaises( CmdError, self.api.run, ( 'some level' ) )

    def test_raises_ConnError_if_fatal_in_sentence(self):
        self.raisefatal_mock.side_effect = ConnError()
        self.assertRaises( ConnError, self.api.run, ( 'some level' ) )



class ReadLoop(unittest.TestCase):


    def setUp(self):
        rwo = MagicMock( spec = ReaderWriter )
        self.api = Api( rwo )
        self.api.close = MagicMock()


    def test_breaks_if_done_in_sentence(self):
        self.api.rwo.readSnt.side_effect = ['1','2','!done']
        self.api._readDone()
        self.assertEqual( self.api.rwo.readSnt.call_count, 3 )



class ClosingConnecton(unittest.TestCase):


    def setUp(self):
        rwo = MagicMock( spec = ReaderWriter )
        self.api = Api( rwo )

    def test_calls_write_sentence(self):
        self.api.close()
        self.api.rwo.writeSnt.assert_called_once_with( ('/quit',) )

    def test_calls_read_sentence(self):
        self.api.close()
        self.api.rwo.readSnt.assert_called_once_with()

    def test_calls_reader_writers_close_method(self):
        self.api.close()
        self.api.rwo.close.assert_called_once_with()

    def test_calls_reader_writers_close_method_even_if_write_raises_LibError(self):
        self.api.rwo.writeSnt.side_effect = LibError()
        self.api.close()
        self.api.rwo.close.assert_called_once_with()

    def test_calls_reader_writers_close_method_even_if_read_raises_LibError(self):
        self.api.rwo.readSnt.side_effect = LibError()
        self.api.close()
        self.api.rwo.close.assert_called_once_with()



class TimeoutManipulations(unittest.TestCase):


    def setUp(self):
        self.rwo = MagicMock()
        self.api = Api( self.rwo )

    def test_getting_timeout_value(self):
        self.api.timeout
        self.rwo.sock.gettimeout.assert_called_once

    def test_setting_timeout_0_raises_ValueError(self):
        with self.assertRaises(ValueError):
            self.api.timeout = 0

    def test_setting_timeout_lower_than_0_raises_ValueError(self):
        with self.assertRaises(ValueError):
            self.api.timeout = -1

    def test_calls_setting_timeout(self):
        self.api.timeout = 20
        self.rwo.sock.settimeout.assert_called_once_with(20)

