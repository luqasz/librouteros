# -*- coding: UTF-8 -*-

from binascii import unhexlify, hexlify
from hashlib import md5

from rosapi.exc import CmdError, LoginError, Error



class Api:


    def __init__( self, drv, logger ):
        self._logged = False
        self.logger = logger
        self.drv = drv


    def talk( self, cmd, args = {} ):
        '''
        Simplified method to 'talk' with routeros device.
        No tag support available.

        :param cmd: Command word to send
        :param args: Dictionary with key value pairs.
        '''

        snt = self.drv.mkSnt( cmd, args )
        self.drv.writeSnt( snt )
        response = self.drv.readDone()
        response = map( self.drv.parseSnt, response )
        #filter out empty sentences
        response = filter( None, response )

        return tuple( response )


    def login( self, username, password ):
        '''
        Log in with given username and password.

        :param username: Username to log in with.
        :param password: Password to log in with.
        '''


        try:
            self.drv.writeSnt( ( '/login', ) )
            chal = self.drv.readSnt()
        except Error as estr:
            self.close()
            raise LoginError( estr )
        else:
            chal = self.drv.parseSnt( chal )['ret']

        # encode given password
        password = self._pw_enc( chal, password )

        try:
            self.drv.writeSnt( ( '/login', '=name=' + username, '=response=' + password ) )
            self.drv.readDone()
        except CmdError:
            self.close()
            raise LoginError( 'wrong username and/or password' )
        else:
            self._logged = True


    def _pw_enc( self, chal, password ):
        '''
        Encode password to mikrotik format.

        :param chal: Challenge response generated on login.
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


    def close( self ):
        '''
        Close the connection. Send /quit first
        and then shut down socket through driver.
        '''

        self.logger.debug( 'Closing connection.' )

        try:
            self._send_quit()
        except Error:
            pass
        finally:
            self._logged = False
            self.drv.close()


    def _send_quit( self ):
        '''
        Send /quit command and close the socket connection.
        Any attempt to read or write to socket will fail.
        '''

        self.logger.debug( 'Sending /quit' )

        if self._logged:
            self.drv.writeSnt( ( '/quit', ) )
            self.drv.readSnt()


    def __del__( self ):
        '''
        On garbage collection run close()
        '''

        self.logger.debug( 'Autoclosing connection.' )
        self.close()
