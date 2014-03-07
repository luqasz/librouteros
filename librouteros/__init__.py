# -*- coding: UTF-8 -*-

from logging import getLogger, NullHandler
from socket import create_connection, error as sk_error, timeout as sk_timeout

from librouteros.exc import ConnError, CmdError, LoginError
from librouteros.drivers import SocketDriver, trapCheck, encPass
from librouteros.connections import ReaderWriter, Connection
from librouteros.datastructures import parsnt


_def_vals = { 'timeout' : 10, \
            'logger' : None, \
            'port' : 8728, \
            'password' : '' }


def connect( host, user, **kwargs ):
    '''
    Connect and login to routeros device.
    Upon success return a Connection class.

    host
        Hostname to connecto to. May be ipv4,ipv6,FQDN.
    user
        Username to login with.
    password
        Password to login with. Defaults to be empty.
    timout
        Socket timeout. Defaults to 10.
    port
        Destination port to be used. Defaults to 8728.
    logger
        Logger instance to be used. Defaults to an empty logging instance.
    '''

    passed = _def_vals.copy()
    passed.update( kwargs )

    try:
        sk = create_connection( ( host, passed['port'] ), passed['timeout'] )
    except ( sk_error, sk_timeout ) as e:
        raise ConnError( e )

    logger_instance = _mkNullLogger() if not passed['logger'] else passed['logger']
    rwo = ReaderWriter( sk )
    drv = SocketDriver( rwo, logger_instance )

    try:
        snt = _initLogin( drv )
    except ConnError as estr:
        drv.close()
        raise LoginError( estr )

    chal = parsnt(snt)['ret']
    encoded = encPass( chal, passed['password'] )

    try:
        _login( drv, user, encoded )
    except CmdError:
        drv.close()
        raise LoginError( 'wrong username and/or password' )

    return Connection( drv )




def _initLogin( drv ):
    '''
    Send an initial login.
    '''

    drv.writeSnt( '/login', () )
    return drv.readSnt()


def _login( drv, username, password ):

    drv.writeSnt( '/login', ( '=name=' + username, '=response=' + password ) )
    response = drv.readDone()
    trapCheck( response )


def _mkNullLogger():

    # this will always return same logger instance
    logger = getLogger( 'api_null_logger' )
    # ensure that logge has only 1 null handler.
    if len( logger.handlers ) == 0:
        logger.addHandler( NullHandler() )

    return logger

