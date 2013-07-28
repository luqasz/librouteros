# -*- coding: UTF-8 -*-

import socket
from struct import pack, unpack

from exc import RwError, RwTimeout, ConnError



class ReaderWriter:


    def __init__( self, sock, logger ):
        self.logger = logger
        self.sock = sock


    def writeSnt( self, snt ):
        '''
        Write sentence to socket.
        Whole sentence is encoded and sent at once.
        
        :param snt: Iterable with words.
        '''

        encoded = map( self.encWord, snt )
        encoded += b'\x00'
        self.writeSock( encoded )


    def readSnt( self ):
        '''
        Read as long as EOS (end of sentence, 0 byte length b'\x00'). 
        
        :returns: List with decoded words.
        '''

        sentence = []

        to_read = self.getLen()
        while to_read:
            word = self.readSock( to_read )
            # add word to sentence
            sentence.append( word )
            # read another length of word
            to_read = self.getLen()

        sentence = [ word.decode( 'UTF-8', 'strict' ) for word in sentence ]
        return sentence


    def readSock( self, length ):
        """
        Read as many bytes from socket as specified in :param length:. Loop as long as every byte is read unless exception is raised
        Returns bytes string read. 
        
        **Note** When timeout or socket error occurs ``RwError`` is raised with description of error. 
        
        :param length: how many bytes to read
        :returns: Bytes string read. 
        """

        ret_str = b''
        # how many bytes to read
        to_read = length
        try:
            while to_read:
                ret = self.sock.recv( to_read )
                self.logger.debug( '---> {bstr!r}'.format( bstr = ret ) )
                if not ret:
                    raise RwError( 'connection unexpectedly closed. read {read}/{total} bytes.'
                                    .format( read = ( length - len( ret_str ) ), total = length ) )
                ret_str += ret
                to_read -= len( ret )
        except socket.timeout:
            raise RwError( 'socket timed out. read {read}/{total} bytes.'
                            .format( read = ( length - len( ret_str ) ), total = length ) )
        except socket.error as estr:
            raise RwError( 'failed to read from socket: {reason}'.format( reason = estr ) )

        return ret_str


    def writeSock( self, string ):
        """
        Write given string to socket. Loop as long as every byte in string is written unless exception is raised.
        
        **Note** When timeout or socket error occurs ``RwError`` is raised with description of error. 
        
        :param bstring: bytes string to write
        :ivar sock: socket object
        """

        str_len = len( string )
        try:
            while string:
                sent = self.sock.send( string )
                if not sent:
                    raise RwError( 'connection unexpectedly closed. sent {sent}/{total} bytes.'
                                    .format( sent = ( str_len - len( string ) ), total = str_len ) )
                self.logger.debug( '<--- {bstr!r}'.format( bstr = string[:sent] ) )
                string = string[sent:]
        except socket.timeout:
            raise RwError( 'socket timed out. sent {sent}/{total} bytes.'
                            .format( sent = ( str_len - len( string ) ), total = str_len ) )
        except socket.error as estr:
            raise RwError( 'failed to write to socket: {reason}'.format( reason = estr ) )


    def getLen( self ):
        """
        Read encoded length and return it as integer
        """
        first_byte = self.readSock( 1 )
        first_byte_int = unpack( 'B', first_byte )[0]

        if first_byte_int < 128:
            return first_byte_int
        elif first_byte_int < 192:
            additional_bytes = 1
        elif first_byte_int < 224:
            additional_bytes = 2
        elif first_byte_int < 240:
            additional_bytes = 3
        else:
            raise ConnError( 'unknown controll byte received {0!r}'.format( first_byte ) )

        additional_bytes = self.readSock( additional_bytes )
        decoded = self.decLen( first_byte, additional_bytes )
        self.logger.debug( 'read length = {length!r}'.format( decoded ) )

        return decoded


    def decLen( self, first_byte, additional_bytes ):

        addit_len = len( additional_bytes )

        if addit_len < 192:
            offset = b'\x00\x00'
            XOR = 0x8000
        elif addit_len < 224:
            offset = b'\x00'
            XOR = 0xC00000
        elif addit_len < 240:
            offset = b''
            XOR = 0xE0000000

        decoded = offset + first_byte + additional_bytes
        decoded = unpack( '!I', decoded )[0]
        decoded ^= XOR

        return decoded


    def encWord( self, word ):
        '''
        Encode every word.
        
        :param word: Word object.
        :returns: Encoded word length with word itself in bytes. 
        '''
        elen = self.encLen( len( word ) )
        eword = word.encode( encoding = 'utf_8', errors = 'strict' )
        return elen + eword


    def encLen( self, length ):
        """
        Encode given length in mikrotik format.
        
        **Note** if :param length: is >= 268435456 ``apiError`` will be raised.
        
        :param length: Integer < 268435456.
        :returns: Encoded length in bytes. 
        """

        if length < 0x80:
            offset = -1
        elif length < 0x4000:
            length |= 0x8000
            offset = -2
        elif length < 0x200000:
            length |= 0xC00000
            offset = -3
        elif length < 0x10000000:
            length |= 0xE0000000
            offset = -4
        else:
            raise ConnError( 'unable to encode length of {0}'.format( length ) )

        length = pack( '!I', length )[offset:]
        return length
