# -*- coding: UTF-8 -*-

import socket
from exc import ConnError, RwError
from struct import pack, unpack
from sentences import readableSentence
from words import getWordType, replyWord


class conSync:


    def __init__( self, logger ):
        self.logger = logger
        self.sock = None


    def sendAndReceive( self, sentence ):
        '''
        Write sentence and read as long as EOR (end of response).
        EOR is a combination of two words. Either !done or !fatal and a EOS
        Passed sentence is a writeableSentence object.
        
        Returns list of read sentences.
        '''

        sentences = []
        self.writeSentence( sentence )
        while True:
            read_sentence = self.readSentence()
            sentences.append( read_sentence )
            if '!done' in read_sentence:
                return sentences


    def writeSentence( self, sentence ):
        '''
        Write sentence to socket.
        Passed sentence is a writeableSentence object.
        '''

        # encode every word in sentence
        encoded = map( self.encWord, sentence )
        # join encoded words together forming a bytes string
        encoded = b''.join( encoded )
        # add an EOS byte
        encoded += b'\x00'

        for word in sentence:
            self.log.info( '<--- {word!s}'.format( word = word ) )
        self.log.info( '<--- EOS' )

        self.writeSock( encoded )


    def readSentence( self ):
        '''
        Read as long as EOS (end of sentence, 0 byte length b'\x00'). 
        This method may return an empty sentence.
        
        **Note** If '!fatal' is found in sentence, connection is closed 
        and ``ConnError`` exception is raised with a description. 
        
        :returns: readableSentence object.
        '''

        sentence = readableSentence()
        word = self.readWord()
        while word:
            # add word to sentence
            sentence += word
            word = self.readWord()

        if '!fatal' in sentence:
            # !fatal closes connection
            self.close()
            # join every word (that is not an replyWord) forming an error string
            estr = ', '.join( wr for wr in sentence if not isinstance( wr, replyWord ) )
            raise ConnError( 'connection closed: {0!r}'.format( estr ) )
        return sentence


    def readWord( self ):
        '''
        Read a single word.
        
        :returns: Word object.
        '''

        # when getLen() returns 0 it means an EOS
        to_read = self.getLen()
        if not to_read:
            self.log.info( '---> EOS' )
            return
        else:
            # read as many bytes as decoded previously
            word = self.readSock( to_read )
            word = word.decode( 'UTF-8', 'strict' )
            word_obj = getWordType( word )
            word = word_obj( word )
            self.log.info( '---> {word!s}'.format( word = word ) )
            return word


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
                self.log.debug( '---> {bstr!r}'.format( bstr = ret ) )
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
                self.log.debug( '<--- {bstr!r}'.format( bstr = string[:sent] ) )
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
        self.log.debug( 'read length = {length!r}'.format( decoded ) )

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
        eword = str( word ).encode( encoding = 'utf_8', errors = 'strict' )
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


    def __repr__( self ):
        return '<conSync {0[0]}:{0[1]}>'.format( self.sock.getpeername() )
