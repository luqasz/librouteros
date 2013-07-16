# -*- coding: UTF-8 -*-

from binascii import unhexlify, hexlify
from hashlib import md5

class MikroTik:

    def connect( self, address, port = 8728, timeout = 10, src_addr = (0,0) ):
        try:
            # try to open socket connection to given address and port with timeout
            self.sock = socket.create_connection( ( address, port ), timeout, src_addr )
        except socket.error as estr:
            raise ConnError( estr )
        
    def _getVersion( self ):
        '''
        Getter for remote version number.
        '''
        if self._version:
            return self._version
        else:
            ret = self.talk( '/system/package/print' )
            ret = [pkg for pkg in ret if pkg.get( 'name' ) == 'system']
            try:
                self._version = ret[0]['version']
            except IndexError:
                raise ApiError( 'could not read remote version number.' )
            return self._version

    # class property with remote version number
    version = property( _getVersion )

    def close( self ):
        if not self.sock:
            return
        if self.sock._closed:
            return
        # shutdown socket
        try:
            self.sock.shutdown( socket.SHUT_RDWR )
        except socket.error:
            pass
        finally:
            self.sock.close()
            
            
    def login( self, username, password ):
        '''
        Log in with given username and password.
        
        :param username: Username to log in with.
        :param password: Password to log in with.
        '''

        try:
            response = self.talk( '/login' )
        except ApiError as estr:
            self.quit()
            raise LoginError( estr )

        # encode given password
        password = self._pw_enc( response[0]['ret'], password )

        try:
            response = self.talk( '/login', {'name': username, 'response': password} )
        except CmdError:
            self.quit()
            raise LoginError( 'wrong username and/or password' )

        self._logged = True
        
        def _pw_enc( self, chal, password ):
        '''
        Encode password to mikrotik format and return it.
        
        :param chal: Challenge response generated every time /login is called.
        :param password: Password given to login.
        :returns: Encoded password.
        '''

        chal = chal.encode( 'UTF-8', 'strict' )
        chal = unhexlify( chal )
        password = password.encode( 'UTF-8', 'strict' )
        md = md5()
        md.update( b'\x00' + password + chal )
        password = hexlify( md.digest() )
        password = '00' + password.decode( 'UTF-8', 'strict' )

        return password
    
    
    def quit( self ):
        '''
        Send /quit command and close the socket connection.
        Any attempt to read or write to socket will fail. 
        '''
        if self._logged:
            sentence = ( writeableSentence( commandWord( '/quit' ) ) )
            self.conn.writeSentence( sentence )
            self._logged = False

        self.conn.close()
        
    def __del__( self ):
        '''
        On garbage collection run quit()
        '''
        self.quit()