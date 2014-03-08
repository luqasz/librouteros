# -*- coding: UTF-8 -*-

import unittest
from mock import MagicMock, call, patch
import socket


import librouteros.connections as conn
from librouteros.exc import ConnError



class EncodeLengths(unittest.TestCase):


    def test_encode_length_less_than_128( self ):
        self.assertEqual( conn.enclen( 127 ), b'\x7f' )


    def test_encode_length_less_than_16384( self ):
        self.assertEqual( conn.enclen( 130 ), b'\x80\x82' )


    def test_encode_length_less_than_2097152( self ):
        self.assertEqual( conn.enclen( 2097140 ), b'\xdf\xff\xf4' )


    def test_encode_length_less_than_268435456( self ):
        self.assertEqual( conn.enclen( 268435440 ), b'\xef\xff\xff\xf0' )


    def test_encode_length_raises_exception_if_lenghth_exceeds_268435456( self ):
        self.assertRaises( ConnError, conn.enclen, 268435456 )



class DecodeLengths(unittest.TestCase):


    def test_decode_length_less_than_128( self ):
        self.assertEqual( conn.declen( b'\x7f' ), 127 )


    def test_decode_length_less_than_16384( self ):
        self.assertEqual( conn.declen( b'\x80\x82' ), 130 )


    def test_decode_length_less_than_2097152( self ):
        self.assertEqual( conn.declen( b'\xdf\xff\xf4' ), 2097140 )


    def test_decode_length_less_than_268435456( self ):
        self.assertEqual( conn.declen( b'\xef\xff\xff\xf0'  ), 268435440 )



class GetLengths(unittest.TestCase):


    def setUp(self):
        patcher = patch('librouteros.connections.declen')
        self.rwo = conn.ReaderWriter( None )
        self.dec_len_mock = patcher.start()
        self.addCleanup(patcher.stop)


    def test_calls_declen_less_than_128( self ):
        side_eff = [b'\x7f', b'']
        self.rwo.readSock = MagicMock( side_effect = side_eff )
        self.rwo.getLength()

        calls = self.rwo.readSock.mock_calls
        expected_calls = [ call(1), call(0) ]
        self.assertEqual( calls, expected_calls )


    def test_calls_declen_less_than_16384( self ):
        side_eff = [ b'\x80', b'\x82' ]
        self.rwo.readSock = MagicMock( side_effect = side_eff )
        self.rwo.getLength()

        calls = self.rwo.readSock.mock_calls
        expected_calls = [ call(1), call(1) ]
        self.assertEqual( calls, expected_calls )


    def test_calls_declen_less_than_2097152( self ):
        side_eff = [ b'\xdf', b'\xff\xf4' ]
        self.rwo.readSock = MagicMock( side_effect = side_eff )
        self.rwo.getLength()

        calls = self.rwo.readSock.mock_calls
        expected_calls = [ call(1), call(2) ]
        self.assertEqual( calls, expected_calls )


    def test_calls_declen_less_than_268435456( self ):
        side_eff = [ b'\xef', b'\xff\xff\xf0' ]
        self.rwo.readSock =  MagicMock( side_effect = side_eff )
        self.rwo.getLength()

        calls = self.rwo.readSock.mock_calls
        expected_calls = [ call(1), call(3) ]
        self.assertEqual( calls, expected_calls )


    def test_raises_if_lenghth_exceeds_268435456( self ):
        side_eff = [b'\xf0', b'']
        self.rwo.readSock = MagicMock( side_effect = side_eff )
        self.assertRaises( ConnError, self.rwo.getLength )




class EncodeWord(unittest.TestCase):


    def setUp(self):
        patcher = patch('librouteros.connections.enclen')
        self.enc_len_mock = patcher.start()
        self.enc_len_mock.return_value = b'len'
        self.addCleanup(patcher.stop)


    def test_calls_enclen( self ):
        word = 'word'
        conn.encword( word )
        self.enc_len_mock.called_once_with( 4 )


    def test_returns_bytes_encoded(self):
        retval = conn.encword( 'word' )
        self.assertEqual( retval, b'lenword' )


class EncodeSentence(unittest.TestCase):


    def setUp(self):
        patcher = patch('librouteros.connections.encword')
        self.enc_word_mock = patcher.start()
        self.enc_word_mock.side_effect = [ b'first', b'second' ]
        self.addCleanup(patcher.stop)


    def test_calls_encword( self ):
        sentence = ('first', 'second')
        conn.encsnt( sentence )
        expected_calls = [ call(elem) for elem in sentence ]
        self.assertEqual( self.enc_word_mock.mock_calls, expected_calls )


    def test_returns_bytes_encoded_sentence(self):
        retval = conn.encsnt(( 'first', 'second' ))
        self.assertEqual( retval, b'firstsecond\x00' )




class DecodeSentences(unittest.TestCase):


    def test_return_decoded(self):
        retval = conn.decsnt( (b'first', b'second') )
        self.assertEqual( retval, ('first', 'second') )




class WriteSock(unittest.TestCase):


    def setUp(self):
        sock = MagicMock( spec = socket.socket )
        self.rwo = conn.ReaderWriter( sock )


    def test_partial_sending(self):
        self.rwo.sock.send.side_effect = [ 2,2 ]
        self.rwo.writeSock( 'word' )
        expected_calls = [ call( 'word' ), call('rd') ]
        self.assertEqual( self.rwo.sock.send.mock_calls, expected_calls )


    def test_sending_whole_string_at_once(self):
        self.rwo.sock.send.side_effect = [ 4 ]
        self.rwo.writeSock( 'word' )
        self.rwo.sock.send.assert_called_once_with( 'word' )


    def test_sending_raises_when_no_bytes_sent(self):
        self.rwo.sock.send.side_effect = [ 0 ]
        self.assertRaises( ConnError, self.rwo.writeSock, 'word' )


    def test_sending_raises_socket_timeout(self):
        self.rwo.sock.send.side_effect = socket.timeout
        self.assertRaises( ConnError, self.rwo.writeSock, 'word' )


    def test_sending_raises_socket_error(self):
        self.rwo.sock.send.side_effect = socket.error
        self.assertRaises( ConnError, self.rwo.writeSock, 'word' )



class ReadSock(unittest.TestCase):


    def setUp(self):
        sock = MagicMock( spec = socket.socket )
        self.rwo = conn.ReaderWriter( sock )


    def test_partial_sending(self):
        self.rwo.sock.recv.side_effect = [ b'wo', b'rd' ]
        self.rwo.readSock( 4 )
        expected_calls = [ call(4), call(2) ]
        self.assertEqual( self.rwo.sock.recv.mock_calls, expected_calls )


    def test_sending_whole_string_at_once(self):
        self.rwo.sock.recv.side_effect = [ b'word' ]
        self.rwo.readSock( 4 )
        self.rwo.sock.recv.assert_called_once_with( 4 )


    def test_sending_raises_when_no_bytes_sent(self):
        self.rwo.sock.recv.side_effect = [ b'' ]
        self.assertRaises( ConnError, self.rwo.readSock, 4 )


    def test_sending_raises_socket_timeout(self):
        self.rwo.sock.recv.side_effect = socket.timeout
        self.assertRaises( ConnError, self.rwo.readSock, 4 )


    def test_sending_raises_socket_error(self):
        self.rwo.sock.recv.side_effect = socket.error
        self.assertRaises( ConnError, self.rwo.readSock, 4 )


    def test_returns_bytes_object(self):
        self.rwo.sock.recv.side_effect = [ b'wo', b'rd' ]
        retval = self.rwo.readSock( 4 )
        self.assertEqual( retval, b'word' )


    def test_returns_empty_bytes_when_called_with_0(self):
        retval = self.rwo.readSock( 0 )
        self.assertEqual( retval, b'' )

    def test_does_not_call_recv_when_called_with_0(self):
        self.rwo.readSock(0)
        self.assertEqual( self.rwo.sock.recv.call_count, 0 )



class WriteSentence(unittest.TestCase):


    def setUp(self):
        encsnt_patcher = patch('librouteros.connections.encsnt')
        self.encsnt_mock = encsnt_patcher.start()
        self.encsnt_mock.return_value = 'encoded'

        self.rwo = conn.ReaderWriter( None )
        self.rwo.writeSock = MagicMock()

        self.addCleanup(encsnt_patcher.stop)


    def test_calls_encode_sentence( self ):
        sentence = ('first', 'second')
        self.rwo.writeSentence( sentence )
        self.encsnt_mock.assert_called_once_with( sentence )


    def test_calls_write_to_socket( self ):
        sentence = ('first', 'second')
        self.rwo.writeSentence( sentence )
        self.rwo.writeSock.assert_called_once_with( 'encoded' )



class ReadSentence(unittest.TestCase):


    def setUp(self):
        decsnt_patcher = patch('librouteros.connections.decsnt')
        self.decsnt_mock = decsnt_patcher.start()
        self.decsnt_mock.return_value = 'decoded'

        self.rwo = conn.ReaderWriter( None )
        self.rwo.readSock = MagicMock( side_effect = [ 'first', 'second' ] )
        self.rwo.getLength = MagicMock( side_effect = [ 5,6,0 ] )

        self.addCleanup(decsnt_patcher.stop)


    def test_calls_get_length( self ):
        self.rwo.readSentence()
        self.assertEqual( self.rwo.getLength.call_count, 3 )


    def test_calls_read_socket( self ):
        self.rwo.readSentence()
        self.assertEqual( self.rwo.readSock.mock_calls, [ call(5), call(6) ] )


    def test_calls_decode_sentence( self ):
        self.rwo.readSentence()
        self.decsnt_mock.assert_called_once_with( [ 'first', 'second' ] )


    def test_returns_decoded(self):
        retval = self.rwo.readSentence()
        self.assertEqual( retval, 'decoded' )


class ClosingProcedures(unittest.TestCase):


    def setUp(self):
        sock = MagicMock( spec = socket.socket )
        self.ReaderWriter = conn.ReaderWriter( sock )


    def test_close_if_socket_closed(self):
        self.ReaderWriter.sock._closed = True
        self.ReaderWriter.close()
        self.assertFalse( self.ReaderWriter.sock.shutdown.called )


    def test_shutdowns_socket_if_socket_not_closed(self):
        self.ReaderWriter.sock._closed = False
        self.ReaderWriter.close()
        self.assertTrue( self.ReaderWriter.sock.shutdown.called )
        self.assertTrue( self.ReaderWriter.sock.close.called )


    def test_closes_socket_even_if_socket_error_is_raised(self):
        self.ReaderWriter.sock._closed = False
        self.ReaderWriter.sock.shutdown = MagicMock( side_effect = socket.error )
        self.ReaderWriter.close()
        self.assertTrue( self.ReaderWriter.sock.shutdown.called )
        self.assertTrue( self.ReaderWriter.sock.close.called )



class ConnectionTimeoutTests(unittest.TestCase):


    def setUp(self):
        self.drv = MagicMock()
        self.conn = conn.Connection( self.drv )

    def test_getting_timeout_value(self):
        self.conn.timeout
        self.drv.conn.sock.gettimeout.assert_called_once

    def test_setting_timeout_below_0_raises_ValueError(self):
        with self.assertRaises(ValueError):
            self.conn.timeout = 0

    def test_calls_setting_timeout(self):
        self.conn.timeout = 20
        self.drv.conn.sock.settimeout.assert_called_once_with(20)
