# -*- coding: UTF-8 -*-

import unittest
from mock import MagicMock, patch

import librouteros.drivers as drv
from librouteros.datastructures import DictData
from librouteros.connections import ReaderWriter
from librouteros.exc import LoginError, ConnError, CmdError


class PasswordMethods(unittest.TestCase):


    def test_password_encoding(self):
        self.assertEqual( drv.encPass( '259e0bc05acd6f46926dc2f809ed1bba', 'test'), '00c7fd865183a43a772dde231f6d0bff13' )


    def test_challenge_argument_extraction(self):
        sentence = ( '=ret=xxx', '!done' )
        self.assertEqual( drv.getChal( sentence ), 'xxx' )


    def test_error_raiseing_if_no_ret_argument(self):
        sentence = ( 'xxx', '!done' )
        self.assertRaises( LoginError, drv.getChal, sentence )


class ApiSentenceCreation(unittest.TestCase):


    def setUp(self):
        patcher = patch('librouteros.drivers.typeCheck')
        conn = MagicMock( spec = ReaderWriter )
        ds = MagicMock( spec = DictData )
        ds.data_type = dict
        self.type_mock = patcher.start()
        self.drv = drv.ApiSocketDriver( conn, ds )
        self.addCleanup(patcher.stop)


    def test_calls_data_structure_method(self):
        self.drv.mkApiSnt( dict() )
        self.drv.data_struct.mkApiSnt.assert_called_once_with( dict() )


    def test_calls_typeCheck(self):
        self.drv.mkApiSnt( 'string' )
        self.type_mock.assert_called_once_with( 'string', dict )

class ApiSentenceParsing(unittest.TestCase):


    def setUp(self):
        conn = MagicMock( spec = ReaderWriter )
        ds = MagicMock( spec = DictData )
        self.drv = drv.ApiSocketDriver( conn, ds )


    def test_api_respone_parsing_calls_data_structure_method(self):
        self.drv.parseResp( 'string' )
        self.drv.data_struct.parseApiResp.assert_called_once_with( 'string' )



class WriteMethods(unittest.TestCase):


    def setUp(self):
        conn = MagicMock( spec = ReaderWriter )
        ds = MagicMock( spec = DictData )
        self.drv = drv.ApiSocketDriver( conn, ds )


    def test_write_calls_connection_method_with_valid_arguments( self ):
        self.drv.writeSnt( '/level', ('string1', 'string2') )
        self.drv.conn.writeSentence.assert_called_once_with( ('/level', 'string1', 'string2') )



class ReadMethods(unittest.TestCase):


    def setUp(self):
        conn = MagicMock( spec = ReaderWriter )
        ds = MagicMock( spec = DictData )
        self.drv = drv.ApiSocketDriver( conn, ds )


    def test_read_calls_connection_method(self):
        self.drv.readSnt()
        self.drv.conn.readSentence.assert_called_once_with()


    def test_readDone_returns_valid_tuple_and_breaks_when_done(self):
        return_sequence = ( (), ('!done') )
        self.drv.readSnt = MagicMock( side_effect = return_sequence )
        retval = self.drv.readDone()
        self.assertEqual( retval, return_sequence )



class ClosingProcedure(unittest.TestCase):


    def setUp(self):
        conn = MagicMock( spec = ReaderWriter )
        ds = MagicMock( spec = DictData )
        self.drv = drv.ApiSocketDriver( conn, ds )


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
