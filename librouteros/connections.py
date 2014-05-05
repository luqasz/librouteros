# -*- coding: UTF-8 -*-

import socket
from struct import pack, unpack

from librouteros.exc import ConnError



def enclen( length ):
    '''
    Encode given length in mikrotik format.

    length: Integer < 268435456.
    returns: Encoded length in bytes.
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
        raise ConnError( 'unable to encode length of {0}'
                        .format( length ) )

    encoded_length = pack( '!I', ored_length )[offset:]
    return encoded_length


def declen( bytes ):
    '''
    Decode length based on given bytes.

    bytes_string: Bytes string to decode.
    returns: Length in integer.
    '''

    XORMAP = { 3:0, 2:0x8000, 1:0xC00000, 0:0xE0000000 }
    zfill = bytes.rjust(4, b'\x00')
    # how many \x00 have been prefixed
    xor = len(zfill) - len(bytes)
    decoded = unpack( '!I', zfill )[0]
    decoded ^= XORMAP[ xor ]

    return decoded


def decsnt( sentence ):

    return tuple( word.decode( 'UTF-8', 'strict' ) for word in sentence )


def encsnt( sentence ):
    '''
    Encode given sentence in API format.

    returns: Encoded sentence in bytes object.
    '''

    encoded = map( encword, sentence )
    encoded = b''.join( encoded )
    # append EOS byte
    encoded += b'\x00'

    return encoded


def encword( word ):
    '''
    Encode word in API format.

    returns: Encoded word in bytes object.
    '''

    encoded_len = enclen( len( word ) )
    encoded_word = word.encode( encoding = 'utf_8', errors = 'strict' )
    return encoded_len + encoded_word



def log_snt( logger, sentence, direction ):

    dstrs = { 'write':'<---', 'read':'--->' }
    dstr = dstrs.get( direction )

    for word in sentence:
        logger.debug( '{0} {1!r}'.format( dstr, word ) )

    logger.debug( '{0} EOS'.format( dstr ) )






class ReaderWriter:


    def __init__( self, sock, log ):
        self.sock = sock
        self.log = log


    def writeSnt( self, snt ):
        '''
        Write sentence to connection.

        sentence: Iterable (tuple or list) with words.
        '''

        encoded = encsnt( snt )
        self.writeSock( encoded )
        log_snt( self.log, snt, 'write' )


    def readSnt( self ):
        '''
        Read sentence from connection.

        returns: Sentence as tuple with words in it.
        '''

        snt = []
        for length in iter( self.getLen, 0 ):
            word = self.readSock( length )
            snt.append( word )

        decoded = decsnt( snt )
        log_snt( self.log, decoded, 'read' )

        return decoded


    def readSock( self, length ):
        '''
        Read as many bytes from socket as specified in length.
        Loop as long as every byte is read unless exception is raised.
        '''

        return_string = []
        to_read = length
        total_bytes_read = 0

        try:
            while to_read:
                read = self.sock.recv( to_read )
                return_string.append( read )
                to_read -= len( read )
                total_bytes_read = length - to_read

                if not read:
                    raise ConnError( 'connection unexpectedly closed. read {read}/{total} bytes.'
                                    .format( read = total_bytes_read, total = length ) )
        except socket.timeout:
            raise ConnError( 'socket timed out. read {read}/{total} bytes.'
                            .format( read = total_bytes_read, total = length ) )
        except socket.error as estr:
            raise ConnError( 'failed to read from socket: {reason}'.format( reason = estr ) )

        return b''.join( return_string )


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
                    raise ConnError( 'connection unexpectedly closed. sent {sent}/{total} bytes.'
                                    .format( sent = total_bytes_sent, total = string_length ) )
        except socket.timeout:
            raise ConnError( 'socket timed out. sent {sent}/{total} bytes.'
                            .format( sent = total_bytes_sent, total = string_length ) )
        except socket.error as estr:
            raise ConnError( 'failed to write to socket: {reason}'.format( reason = estr ) )


    def getLen( self ):
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
            raise ConnError( 'unknown controll byte received {0!r}'
                            .format( first_byte ) )

        additional_bytes = self.readSock( bytes_to_read )

        return declen( first_byte + additional_bytes )


    def close( self ):

        # do not do anything if socket is already closed
        if self.sock._closed:
            return
        # shutdown socket
        try:
            self.sock.shutdown( socket.SHUT_RDWR )
        except socket.error:
            pass
        finally:
            self.sock.close()
