# -*- coding: UTF-8 -*-

import unittest
from mock import MagicMock, call
from logging import Logger
import socket


from librouteros.connections import ReaderWriter
from librouteros.exc import ApiError, RwError, RwTimeout, ConnClosed



class EncodeLengths(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logger = MagicMock( spec = Logger )
        sock = MagicMock( spec = socket.socket )
        cls.ReaderWriter = ReaderWriter( sock, logger )


    def test_encode_length_less_than_128( self ):
        self.assertEqual( self.ReaderWriter.encodeLength( 127 ), b'\x7f' )


    def test_encode_length_less_than_16384( self ):
        self.assertEqual( self.ReaderWriter.encodeLength( 130 ), b'\x80\x82' )


    def test_encode_length_less_than_2097152( self ):
        self.assertEqual( self.ReaderWriter.encodeLength( 2097140 ), b'\xdf\xff\xf4' )


    def test_encode_length_less_than_268435456( self ):
        self.assertEqual( self.ReaderWriter.encodeLength( 268435440 ), b'\xef\xff\xff\xf0' )


    def test_encode_length_raises_exception_if_lenghth_exceeds_268435456( self ):
        self.assertRaises( ApiError, self.ReaderWriter.encodeLength, 268435456 )



class DecodeLengths(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        logger = MagicMock( spec = Logger )
        sock = MagicMock( spec = socket.socket )
        cls.ReaderWriter = ReaderWriter( sock, logger )


    def test_decode_length_less_than_128( self ):
        self.assertEqual( self.ReaderWriter.decodeLength( b'\x7f' ), 127 )


    def test_decode_length_less_than_16384( self ):
        self.assertEqual( self.ReaderWriter.decodeLength( b'\x80\x82' ), 130 )


    def test_decode_length_less_than_2097152( self ):
        self.assertEqual( self.ReaderWriter.decodeLength( b'\xdf\xff\xf4' ), 2097140 )


    def test_decode_length_less_than_268435456( self ):
        self.assertEqual( self.ReaderWriter.decodeLength( b'\xef\xff\xff\xf0'  ), 268435440 )


    def test_decode_length_raises_exception_if_lenghth_exceeds_268435456( self ):
        self.assertRaises( ApiError, self.ReaderWriter.decodeLength, b'\xf0\x00\x00\x00\x10' )



class GetLengths(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        logger = MagicMock( spec = Logger )
        sock = MagicMock( spec = socket.socket )
        cls.ReaderWriter = ReaderWriter( sock, logger )


    def test_get_length_less_than_128( self ):
        self.ReaderWriter.readSock = MagicMock( side_effect = [ b'\x7f', b'' ] )
        self.assertEqual( self.ReaderWriter.getLength(), 127 )


    def test_get_length_less_than_16384( self ):
        self.ReaderWriter.readSock = MagicMock( side_effect = [ b'\x80', b'\x82' ] )
        self.assertEqual( self.ReaderWriter.getLength(), 130 )


    def test_get_length_less_than_2097152( self ):
        self.ReaderWriter.readSock = MagicMock( side_effect = [ b'\xdf', b'\xff\xf4' ] )
        self.assertEqual( self.ReaderWriter.getLength(), 2097140 )


    def test_get_length_less_than_268435456( self ):
        self.ReaderWriter.readSock =  MagicMock( side_effect = [ b'\xef', b'\xff\xff\xf0' ] )
        self.assertEqual( self.ReaderWriter.getLength(), 268435440 )


    def test_get_length_raises_exception_if_lenghth_exceeds_268435456( self ):
        self.ReaderWriter.readSock = MagicMock( side_effect =  [ b'\xf0', b'' ] )
        self.assertRaises( ApiError, self.ReaderWriter.getLength )




class EncodeWordsAndSentences(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        logger = MagicMock( spec = Logger )
        sock = MagicMock( spec = socket.socket )
        cls.ReaderWriter = ReaderWriter( sock, logger )


    def test_encode_word( self ):
        word = '/ip/address/print'
        retval = b'\x11/ip/address/print'
        self.assertEqual( self.ReaderWriter.encodeWord( word ), retval )


    def test_encode_sentence( self ):
        sentence = ('/ip/address/set', '=.id=*6', '=disabled=true')
        retval = b'\x0f/ip/address/set\x07=.id=*6\x0e=disabled=true\x00'
        self.assertEqual( self.ReaderWriter.encodeSentence( sentence ), retval )




class DecodeSentences(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        logger = MagicMock( spec = Logger )
        sock = MagicMock( spec = socket.socket )
        cls.ReaderWriter = ReaderWriter( sock, logger )


    def test_decode_sentence( self ):
        encoded = (b'/ip/address/set', b'=.id=*6', b'=disabled=true')
        decoded = ('/ip/address/set', '=.id=*6', '=disabled=true')
        self.assertEqual( self.ReaderWriter.decodeSentence( encoded ), decoded )



class WriteSock(unittest.TestCase):


    def setUp(self):
        logger = MagicMock( spec = Logger )
        sock = MagicMock( spec = socket.socket )
        self.ReaderWriter = ReaderWriter( sock, logger )


    def test_writeSock_procedure( self ):
        test_string = b'some_simple_string'
        mock_return_seq = (5, 7, 6)
        expected_call_list = [call(b'some_simple_string'), call(b'simple_string'), call(b'string')]

        self.ReaderWriter.sock.send = MagicMock( side_effect = mock_return_seq )
        self.ReaderWriter.writeSock( test_string )
        self.assertEqual( self.ReaderWriter.sock.send.call_args_list, expected_call_list )


    def test_writeSock_does_not_write_anything_to_socket_if_called_with_empty_string( self ):
        self.ReaderWriter.writeSock( b'' )
        self.assertEqual( self.ReaderWriter.sock.send.call_count, 0 )


    def test_writeSock_raises_if_connection_gets_suddenly_terminated( self ):
        self.ReaderWriter.sock.send = MagicMock( return_value = 0 )
        self.assertRaises( RwError, self.ReaderWriter.writeSock, b'some_string' )


    def test_writeSock_raises_if_timed_out( self ):
        self.ReaderWriter.sock.send = MagicMock( side_effect = socket.timeout )
        self.assertRaises( RwTimeout, self.ReaderWriter.writeSock, b'some_string' )


    def test_writeSock_raises_if_other_error( self ):
        self.ReaderWriter.sock.send = MagicMock( side_effect = socket.error )
        self.assertRaises( RwError, self.ReaderWriter.writeSock, b'string' )



class ReadSock(unittest.TestCase):


    def setUp(self):
        logger = MagicMock( spec = Logger )
        sock = MagicMock( spec = socket.socket )
        self.ReaderWriter = ReaderWriter( sock, logger )


    def test_readSock_procedure( self ):
        mock_return_seq = [ b'first', b'second' ]
        expected_result = b''.join( mock_return_seq )
        call_length = sum(len(elem) for elem in mock_return_seq)

        self.ReaderWriter.sock.recv = MagicMock( side_effect = mock_return_seq )
        self.assertEqual( self.ReaderWriter.readSock( call_length ), expected_result )


    def test_readSock_returns_empty_if_called_with_0_length( self ):
        self.assertEqual( self.ReaderWriter.readSock(0), b'' )


    def test_readSock_raises_if_connection_gets_suddenly_terminated( self ):
        mock_return_seq = [ b'first', b'second', b'' ]
        readSock_call_length = sum(len(elem) for elem in mock_return_seq) + 1

        self.ReaderWriter.sock.recv = MagicMock( side_effect = mock_return_seq )
        self.assertRaises( RwError, self.ReaderWriter.readSock, readSock_call_length )


    def test_readSock_raises_if_timed_out( self ):
        self.ReaderWriter.sock.recv = MagicMock( side_effect = socket.timeout )
        self.assertRaises( RwTimeout, self.ReaderWriter.readSock, 10 )


    def test_readSock_raises_if_other_error( self ):
        self.ReaderWriter.sock.recv = MagicMock( side_effect = socket.error )
        self.assertRaises( RwError, self.ReaderWriter.readSock, 10 )



class WriteSentence(unittest.TestCase):


    def setUp(self):
        logger = MagicMock( spec = Logger )
        sock = MagicMock( spec = socket.socket )
        self.ReaderWriter = ReaderWriter( sock, logger )
        self.ReaderWriter.logWriteSentence = MagicMock()


    def test_whole_procedure( self ):
        self.ReaderWriter.encodeSentence = MagicMock( return_value = 'encoded_string' )
        self.ReaderWriter.writeSock = MagicMock()

        self.ReaderWriter.writeSentence( 'string' )
        self.ReaderWriter.logWriteSentence.assert_called_once_with( 'string' )
        self.ReaderWriter.encodeSentence.assert_called_once_with( 'string' )
        self.ReaderWriter.writeSock.assert_called_once_with( 'encoded_string' )


class ReadSentence(unittest.TestCase):


    def setUp(self):
        logger = MagicMock( spec = Logger )
        sock = MagicMock( spec = socket.socket )
        self.ReaderWriter = ReaderWriter( sock, logger )


    def test_whole_procedure( self ):
        get_length_return_seq = ( 10, 10, 0 )
        read_sock_calls = list( call(elem) for elem in get_length_return_seq[:-1] )
        read_sock_return_seq = [ 'first', 'second' ]
        decode_sentence_calls = [ call( read_sock_return_seq ) ]
        decoded_sentence = ( 'first', 'second' )

        self.ReaderWriter.getLength = MagicMock( side_effect = get_length_return_seq )
        self.ReaderWriter.readSock = MagicMock( side_effect = read_sock_return_seq )
        self.ReaderWriter.decodeSentence = MagicMock( return_value = decoded_sentence )
        self.ReaderWriter.logReadSentence = MagicMock()
        self.ReaderWriter.raiseIfFatal = MagicMock()

        self.assertEqual( self.ReaderWriter.readSentence(), decoded_sentence )
        self.ReaderWriter.logReadSentence.assert_called_once_with( decoded_sentence )
        self.assertEqual( self.ReaderWriter.readSock.call_args_list, read_sock_calls )
        self.assertEqual( self.ReaderWriter.decodeSentence.call_args_list, decode_sentence_calls )
        self.ReaderWriter.raiseIfFatal.assert_called_once_with( decoded_sentence )



class RaiseIfFatal(unittest.TestCase):


    def setUp(self):
        logger = MagicMock( spec = Logger )
        sock = MagicMock( spec = socket.socket )
        self.ReaderWriter = ReaderWriter( sock, logger )
        self.ReaderWriter.close = MagicMock()


    def test_raisesIfFatal(self):
        sentence = ('!fatal', 'connection terminated by remote hoost')
        self.assertRaises( ConnClosed,  self.ReaderWriter.raiseIfFatal, sentence )


    def test_raiseIfFatal_does_not_raises_if_no_error(self):
        self.ReaderWriter.raiseIfFatal( 'some string without error' )



class ClosingProcedures(unittest.TestCase):


    def setUp(self):
        logger = MagicMock( spec = Logger )
        sock = MagicMock( spec = socket.socket )
        self.ReaderWriter = ReaderWriter( sock, logger )


    def test_close_if_socket_closed(self):
        self.ReaderWriter.sock._closed = True
        self.ReaderWriter.close()
        self.assertFalse( self.ReaderWriter.sock.shutdown.called )


    def test_close_shutdowns_socket_if_socket_not_closed(self):
        self.ReaderWriter.sock._closed = False
        self.ReaderWriter.close()
        self.assertTrue( self.ReaderWriter.sock.shutdown.called )
        self.assertTrue( self.ReaderWriter.sock.close.called )


    def test_close_closes_socket_even_if_socket_error_is_raised(self):
        self.ReaderWriter.sock._closed = False
        self.ReaderWriter.sock.shutdown = MagicMock( side_effect = socket.error )
        self.ReaderWriter.close()
        self.assertTrue( self.ReaderWriter.sock.shutdown.called )
        self.assertTrue( self.ReaderWriter.sock.close.called )
