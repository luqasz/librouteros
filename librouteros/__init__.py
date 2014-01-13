# -*- coding: UTF-8 -*-

from logging import getLogger, NullHandler
from socket import create_connection, error as sk_error, timeout as sk_timeout

from librouteros.exc import ConnError, Error, CmdError, LoginError
from librouteros.drivers import ApiSocketDriver, trapCheck, getChal, encPass
from librouteros.connections import ReaderWriter
from librouteros.datastructures import DictData
from librouteros.api import Api


def connect( host, port = 8728,
            timeout = 10, saddr = '', sport = 0, logger = None ):

    try:
        sk = create_connection( ( host, port ), timeout, ( saddr, sport ) )
    except ( sk_error, sk_timeout ) as e:
        raise ConnError( e )

    logger_instance = _mkNullLogger() if not logger else logger
    rwo = ReaderWriter( sk, logger_instance )
    drv = ApiSocketDriver( rwo, DictData() )

    return Connection( rwo, drv )




class Connection:

    def __init__( self, rwo, drv ):
        self.rwo = rwo
        self.drv = drv
        self._logged = False



    def login( self, username, password ):

        chal = self.initLogin()
        encpw = encPass( chal, password )

        try:
            self.drv.writeSnt( '/login', ( '=name=' + username, '=response=' + encpw ) )
            sentence = self.drv.readDone()
            trapCheck( sentence )
        except CmdError:
            raise LoginError( 'wrong username and/or password' )

        return Api( self.drv )


    def initLogin( self ):
        '''
        Send an initial login.

        :returns: Chal response used to encode password.
        '''

        try:
            self.drv.writeSnt( '/login' )
            sentence = self.drv.readSnt()
        except ConnError as estr:
            raise LoginError( estr )

        return getChal( sentence )



    def close( self ):

        try:
            self._send_quit()
        except Error:
            pass
        finally:
            self._logged = False
            self.drv.close()


    def _send_quit( self ):

        if self._logged:
            self.drv.writeSnt( '/quit' )
            self.drv.readSnt()


    def __del__( self ):

        self.close()






def _mkNullLogger():

    logger = getLogger( 'api_null_logger' )
    logger.addHandler( NullHandler() )

    return logger

