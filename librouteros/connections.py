# -*- coding: UTF-8 -*-

import socket
from struct import pack, unpack

from librouteros.exc import RwError, RwTimeout, ConnClosed, ApiError



class ReaderWriter:


    def __init__( self, sock, logger ):
        self.logger = logger
        self.sock = sock


    def writeSentence( self, sentence ):
        '''
        Write sentence to connection.

        :param sentence: Iterable (tuple or list) with words.
        '''

        self.logWriteSentence( sentence )
        encoded = self.encodeSentence( sentence )
        self.writeSock( encoded )


    def readSentence( self ):
        '''
        Read sentence from connection.

        :returns: Sentence as tuple with words in it.
        '''

        sentence = []
        to_read = self.getLength()

        while to_read:
            word = self.readSock( to_read )
            sentence.append( word )
            to_read = self.getLength()

        decoded_sentence = self.decodeSentence( sentence )
        self.logReadSentence( decoded_sentence )
        self.raiseIfFatal( decoded_sentence )

        return decoded_sentence


    def raiseIfFatal( self, sentence ):
        '''
        Check if a given sentence contains error message. If it does then raise an exception.
        !fatal means that connection have been closed and no further transmission will work.
        '''

        if '!fatal' in sentence:
            error = ', '.join( word for word in sentence if word != '!fatal' )
            raise ConnClosed( error )


    def logWriteSentence( self, sentence ):

        for word in sentence:
            self.logger.info( '<--- {word!s}'.format( word = word ) )

        self.logger.info( '<--- EOS' )


    def logReadSentence( self, sentence ):

        for word in sentence:
            self.logger.info( '---> {word!s}'.format( word = word ) )

        self.logger.info( '---> EOS' )


    def readSock( self, length ):
        '''
        Read as many bytes from socket as specified in length.
        Loop as long as every byte is read unless exception is raised.
        '''

        return_string = b''
        to_read = length
        total_bytes_read = 0

        try:
            while to_read:
                read = self.sock.recv( to_read )
                return_string += read
                to_read -= len( read )
                total_bytes_read = length - to_read

                if not read:
                    raise RwError( 'connection unexpectedly closed. read {read}/{total} bytes.'
                                    .format( read = total_bytes_read, total = length ) )
        except socket.timeout:
            raise RwTimeout( 'socket timed out. read {read}/{total} bytes.'
                            .format( read = total_bytes_read, total = length ) )
        except socket.error as estr:
            raise RwError( 'failed to read from socket: {reason}'.format( reason = estr ) )

        return return_string


    def writeSock( self, string ):
        '''
        Writt given string to socket. Loop as long as every byte in
        string is written unless exception is raised.
        '''

        string_length = len( string )
        total_bytes_sent = 0

        try:
            while string:
                sent = self.sock.send( string )
                # remove sent bytes from begining of string
                string = string[sent:]
                total_bytes_sent = string_length - len( string )

                if not sent:
                    raise RwError( 'connection unexpectedly closed. sent {sent}/{total} bytes.'
                                    .format( sent = total_bytes_sent, total = string_length ) )
        except socket.timeout:
            raise RwTimeout( 'socket timed out. sent {sent}/{total} bytes.'
                            .format( sent = total_bytes_sent, total = string_length ) )
        except socket.error as estr:
            raise RwError( 'failed to write to socket: {reason}'.format( reason = estr ) )



    def decodeSentence( self, sentence ):

        sentence = tuple( word.decode( 'UTF-8', 'strict' ) for word in sentence )

        return sentence


    def encodeSentence( self, sentence ):

        encoded = map( self.encodeWord, sentence )
        encoded = b''.join( encoded )
        # append EOS byte
        encoded += b'\x00'

        return encoded


    def encodeWord( self, word ):

        encoded_len = self.encodeLength( len( word ) )
        encoded_word = word.encode( encoding = 'utf_8', errors = 'strict' )
        return encoded_len + encoded_word


    def getLength( self ):
        '''
        Read encoded length and return it as integer.
        '''

        first_byte = self.readSock( 1 )
        first_byte_int = unpack( 'B', first_byte )[0]

        if first_byte_int < 128:
            bytes_to_read = 0
        elif first_byte_int < 192:
            bytes_to_read = 1
        elif first_byte_int < 224:
            bytes_to_read = 2
        elif first_byte_int < 240:
            bytes_to_read = 3
        else:
            raise ApiError( 'unknown controll byte received {0!r}'
                            .format( first_byte ) )

        additional_bytes = self.readSock( bytes_to_read )
        bytes_string = first_byte + additional_bytes
        decoded = self.decodeLength( bytes_string )

        return decoded


    def decodeLength( self, bytes_string ):
        '''
        Decode length based on given bytes.

        :param bytes_string: Bytes string to decode.
        :returns: Decoded as integer length.
        '''

        bytes_length = len( bytes_string )

        if bytes_length < 2:
            offset = b'\x00\x00\x00'
            XOR = 0
        elif bytes_length < 3:
            offset = b'\x00\x00'
            XOR = 0x8000
        elif bytes_length < 4:
            offset = b'\x00'
            XOR = 0xC00000
        elif bytes_length < 5:
            offset = b''
            XOR = 0xE0000000
        else:
            raise ApiError( 'unknown controll byte received {0!r}'
                    .format( bytes_string[:1] ) )

        combined_bytes = offset + bytes_string
        decoded = unpack( '!I', combined_bytes )[0]
        decoded ^= XOR

        return decoded


    def encodeLength( self, length ):
        '''
        Encode given length in mikrotik format.

        :param length: Integer < 268435456.
        :returns: Encoded length in bytes.
        '''

        if length < 128:
            ored_length = length
            offset = -1
        elif length < 16384:
            ored_length = length | 0x8000
            offset = -2
        elif length < 2097152:
            ored_length = length | 0xC00000
            offset = -3
        elif length < 268435456:
            ored_length = length | 0xE0000000
            offset = -4
        else:
            raise ApiError( 'unable to encode length of {0}'
                            .format( length ) )

        encoded_length = pack( '!I', ored_length )[offset:]
        return encoded_length


    def close( self ):

        if self.sock._closed:
            return
        # shutdown socket
        try:
            self.sock.shutdown( socket.SHUT_RDWR )
        except socket.error:
            pass
        finally:
            self.sock.close()


