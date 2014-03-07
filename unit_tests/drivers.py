# -*- coding: UTF-8 -*-

import unittest
from mock import MagicMock, patch

import librouteros.drivers as drv
from librouteros.connections import ReaderWriter
from librouteros.exc import CmdError, ConnError
from librouteros.drivers import raiseIfFatal

class PasswordEncoding(unittest.TestCase):


    def test_password_encoding(self):
        self.assertEqual( drv.encPass( '259e0bc05acd6f46926dc2f809ed1bba', 'test'), '00c7fd865183a43a772dde231f6d0bff13' )


class RaiseIfFatal(unittest.TestCase):


    def test_raises_when_fatal(self):
        sentence = ('!fatal', 'connection terminated by remote hoost')
        self.assertRaises( ConnError,  raiseIfFatal, sentence )


    def test_does_not_raises_if_no_error(self):
        raiseIfFatal( 'some string without error' )


class WriteMethods(unittest.TestCase):


    def setUp(self):
        log_patcher = patch('librouteros.drivers.log_snt')
        conn = MagicMock( spec = ReaderWriter )
        self.drv = drv.SocketDriver( conn, None )
        self.log_mock = log_patcher.start()
        self.addCleanup(log_patcher.stop)


    def test_calls_connection_method_with_valid_arguments( self ):
        self.drv.writeSnt( '/level', ('string1', 'string2') )
        self.drv.conn.writeSentence.assert_called_once_with( ('/level', 'string1', 'string2') )


    def test_calls_log_sentence( self ):
        self.drv.writeSnt( ('/level'), ('word', ) )
        self.log_mock.assert_called_once_with( None, ('/level', 'word'), 'write' )



class ReadSentence(unittest.TestCase):


    def setUp(self):
        log_patcher = patch('librouteros.drivers.log_snt')
        fatal_patcher = patch('librouteros.drivers.raiseIfFatal')

        self.log_mock = log_patcher.start()
        self.fatal_patcher = fatal_patcher.start()

        conn = MagicMock( spec = ReaderWriter )
        self.drv = drv.SocketDriver( conn, None )

        self.addCleanup(log_patcher.stop)
        self.addCleanup(fatal_patcher.stop)


    def test_read_calls_connection_method(self):
        self.drv.readSnt()
        self.drv.conn.readSentence.assert_called_once_with()


    def test_calls_check_for_fatal_condition( self ):
        readSentence_return_value = ('first', 'second')

        self.drv.conn.readSentence.side_effect = readSentence_return_value
        self.drv.readSnt()
        self.fatal_patcher.called_once_with( readSentence_return_value )


    def test_calls_log_sentence( self ):
        readSentence_return_value = ( 'first', 'second' )

        self.drv.conn.readSentence.return_value = readSentence_return_value
        self.drv.readSnt()
        self.log_mock.assert_called_once_with( None, readSentence_return_value, 'read' )



class ReadDone(unittest.TestCase):


    def setUp(self):
        conn = MagicMock( spec = ReaderWriter )
        self.drv = drv.SocketDriver( conn, None )
        self.drv.readSnt = MagicMock()


    def test_returns_valid_tuple_and_breaks_when_done(self):
        return_sequence = ( (), ('!done') )
        self.drv.readSnt.side_effect = return_sequence
        retval = self.drv.readDone()
        self.assertEqual( retval, return_sequence )


class ClosingProcedure(unittest.TestCase):


    def setUp(self):
        conn = MagicMock( spec = ReaderWriter )
        self.drv = drv.SocketDriver( conn, None )


    def test_close_calls_conn_method(self):
        self.drv.close()
        self.drv.conn.close.assert_called_once_with()



class TrapParsing(unittest.TestCase):


    def test_trap_sentence_parsing_filters_api_attribute_words( self ):
        snt = ('!trap', 'string')
        retval = drv.sntTrapParse( snt )
        expected = ' '.join( word for word in snt[1:] )
        self.assertEqual( retval, expected )


    def test_trap_sentence_filters_reply_words( self ):
        snt = ('.reply_word', 'string')
        retval = drv.sntTrapParse( snt )
        expected = ' '.join( word for word in snt[1:] )
        self.assertEqual( retval, expected )



class TrapChecking(unittest.TestCase):


    def test_trap_in_sentences_raises(self):
        snts = ( ('!trap'), ('aaa') )
        self.assertRaises( CmdError, drv.trapCheck, snts )
