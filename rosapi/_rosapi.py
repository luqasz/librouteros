# -*- coding: UTF-8 -*-

# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import socket
from struct import pack, unpack
from rosapi._exceptions import apiError, cmdError

class rosapi:

    def __init__( self, sock, logger ):
        # socket object
        self.sock = sock
        # indicate that by default we are not logged in. after successful login this value is set to True
        self._logged = False
        # logger object
        self.log = logger

    def talk( self, cmd, attrs = None ):
        """
        Send a command and receive response.
        
        :param cmd: String with command word. '/ip/service/print' etc.
        :param attrs: Additional attributes to pass. This can be a dictionary or a list. In case of a list   
        """

        # map bollean types to string equivalents in routeros api
        mapping = {False: 'false', True: 'true', None: ''}
        # write level and if attrs is empty pass True to self.write, else False
        self.writeWord( cmd, end = not attrs )
        if attrs:
            count = len( attrs )
            i = 0
            if isinstance( attrs, dict ):
                for name, value in attrs.items():
                    i += 1
                    last = ( i == count )
                    # write name and value (if bool is present convert to api equivalent) cast rest as string
                    value = str( mapping.get( value, value ) )
                    self.writeWord( '={name}={value}'.format( name = name, value = value ), last )
            if isinstance( attrs, list ):
                for string in attrs:
                    i += 1
                    last = ( i == count )
                    self.writeWord( str( string ), last )

        response = self.read()

        # when adding elements, api returns in response .id of added element
        if cmd.endswith( '/add' ):
            return response[0]['ret']
        else:
            return response

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
            raise apiError( 'unable to encode length of {0}'.format( length ) )

        length = pack( '!I', length )[offset:]
        return length

    def readLen( self ):
        """
        Read encoded length and return it as integer
        """
        controll_byte = self.readSock( 1 )
        controll_byte_int = unpack( 'B', controll_byte )[0]

        if controll_byte_int < 128:
            return controll_byte_int
        elif controll_byte_int < 192:
            offset = b'\x00\x00'
            additional_bytes = self.readSock( 1 )
            XOR = 0x8000
        elif controll_byte_int < 224:
            offset = b'\x00'
            additional_bytes = self.readSock( 2 )
            XOR = 0xC00000
        elif controll_byte_int < 240:
            offset = b''
            additional_bytes = self.readSock( 3 )
            XOR = 0xE0000000
        else:
            raise apiError( 'unknown controll byte received {0!r}'.format( controll_byte ) )

        length = offset + controll_byte + additional_bytes
        length = unpack( '!I', length )[0]
        length ^= XOR

        return length

    def writeSock( self, bstring ):
        """
        Write given string to socket. Loop as long as every byte in string is written unless exception is raised.
        
        **Note** When timeout or socket error occurs ``apiError`` is raised with description of error. 
        
        :param bstring: bytes string to write
        :ivar sock: socket object
        """

        # initialize total bytes sent count
        tb_sent = 0
        # count how long the string is
        bstring_len = len( bstring )

        try:

            while tb_sent < bstring_len:
                b_sent = self.sock.send( bstring[tb_sent:] )
                if not b_sent:
                    raise apiError( 'connection unexpectedly closed. sent {sent}/{total} bytes.'
                                    .format( sent = tb_sent, total = bstring_len ) )
                tb_sent += b_sent

        except socket.error as estr:
            raise apiError( 'failed to write to socket: {reason}'.format( reason = estr ) )
        except socket.timeout:
            raise apiError( 'socket timed out. sent {sent}/{total} bytes.'
                            .format( sent = tb_sent, total = bstring_len ) )


    def readSock( self, length ):
        """
        Read as many bytes from socket as specified in :param length:. Loop as long as every byte is read unless exception is raised
        Returns bytes string read. 
        
        **Note** When timeout or socket error occurs ``apiError`` is raised with description of error. 
        
        :param length: how many bytes to read
        :returns: Bytes string read. 
        """

        # initialize empty list that will hold every bytes read
        ret_str = []
        # initialize how many bytes have been read so far
        b_read = 0

        try:

            while b_read < length:
                ret = self.sock.recv( length - b_read )
                if not ret:
                    raise apiError( 'connection unexpectedly closed. read {read}/{total} bytes.'
                                    .format( read = b_read, total = length ) )
                # add read bytes to list
                ret_str.append( ret )
                b_read += len( ret )

        except socket.timeout:
            raise apiError( 'socket timed out. read {read}/{total} bytes.'
                            .format( read = b_read, total = length ) )
        except socket.error as estr:
            raise apiError( 'failed to read from socket: {reason}'.format( reason = estr ) )


        # return joined bytes as one byte string
        return b''.join( ret_str )

    def writeWord( self, word, end = True ):
        """
        Encodes and writes word.
        
        :param word: String to encode and write.  
        :param end: Boolean value if end of sentence.
        """
        length = len( word )
        enc_len = self.encLen( length )
        self.writeSock( enc_len )

        word = word.encode( 'UTF-8', 'strict' )
        self.log.debug( '<<< {word!r} ({length})'.format( word = word, length = length ) )
        self.writeSock( word )

        # if end is set to bool(true) send ending character chr(0)
        if end:
            self.log.debug( '<<< EOS' )
            self.writeSock( b'\x00' )


    def read( self ):
        """
        Read response after writing sentence.
        """

        response = []
        sentence = []
        error = False
        # EOR end of response
        EOR = False
        # DONE !done reply word
        DONE = False
        while not EOR:
            # read encoded length
            length = self.readLen()
            if not length:
                self.log.debug( '>>> EOS' )
                if sentence:
                    # add conde for .tag support here. if tag exists in sentence ....
                    # decode (from bytes) every element in sentence
                    sentence = [elem.decode( 'UTF-8', 'strict' ) for elem in sentence]
                    # push the sentence into response
                    response.append( sentence )
                    # reset the sentence
                    sentence = []

            if length:
                # read as many bytes as we decoded from readLen
                word = self.readSock( length )
                self.log.debug( '>>> {word!r} ({length})'.format( word = word, length = length ) )
                # add all words to sentence that do not start with !.
                if not word.startswith( b'!' ):
                    sentence.append( word )
                # mark an error when it occurs
                elif word == b'!trap':
                    error = True
                # mark end of reply
                elif word == b'!done':
                    DONE = True
            # make a note when got !done and EOS this marks end of response
            if ( DONE and not length ):
                EOR = True
                self.log.debug( '>>> EOR' )

        return self.parseResponse( response, error )

    def parseResponse( self, response, error ):
        """
        Parse read response. A list is created in witch every element (sentence) is a dictionary.
        
        :param repsonse: Given response
        :param error: Error flag. If this is set to True then cmdError exception is raised with response as message.
        """
        parsed_response = []

        for sentence in response:
            # every element in sentence will be split by second occurrence of '='
            # ['=name=ssh', '=port=22'] will be [['name', 'ssh'], ['port', '22']]
            sentence = [item.split( '=', 2 )[1:] for item in sentence]
            # construct a dictionary with key and value casted to python objects by self.typeCast
            sentence = dict( map( self.typeCast, item ) for item in sentence )
            parsed_response.append( sentence )

        if error:
            msg = ', '.join( ' '.join( '{0}="{1}"'.format( k, v ) for ( k, v ) in inner.items() ) for inner in parsed_response )
            raise cmdError( msg )

        return parsed_response

    def typeCast( self, string ):
        """
        Cast strings into possibly integer, boollean.
        
        :param string: String to cast to python equivalent
        """
        mapping = {'true': True, 'false': False, '': None}
        try:
            ret = int( string )
        except ValueError:
            ret = mapping.get( string, string )
        return ret

    def __del__( self ):
        """
        Disconnect while garbage collecting.
        """

        self.close()

    def send_quit( self ):
        """
        Send /quit command to logout properly. This has to be done in a separate method because, instead of !done we will receive !fatal as end of response mark. 
        """

        self.writeWord( '/quit' )
        END = False
        while not END:
            # read length
            length = self.readLen()
            if length:
                # read word
                word = self.readSock( length )
                self.log.debug( '>>> {word!r} ({length})'.format( word = word, length = length ) )
            else:
                self.log.debug( '>>> EOS' )
                END = True

    def close( self ):
        """
        Logout and close the connection.
        
        :ivar sock: socket object.
        :ivar _logged: Flag to hold login status. 
        """

        if self.sock._closed:
            return

        if self._logged:
            self.send_quit()
            # set logged flag to False
            self._logged = False

        # shutdown socket
        self.sock.shutdown( socket.SHUT_RDWR )
        self.sock.close()
