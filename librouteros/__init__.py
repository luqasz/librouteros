# -*- coding: UTF-8 -*-

'''
from librouteros import connect
api = connect( '1.1.1.1', 'admin', 'password' )
api.run('/ip/address/print')

For more information please visit
https://github.com/uqasz/librouteros
'''


from logging import getLogger, NullHandler
from socket import create_connection, error as sk_error, timeout as sk_timeout
from binascii import unhexlify, hexlify
from hashlib import md5

from librouteros.exc import ConnError, CmdError, LoginError
from librouteros.connections import ReaderWriter
from librouteros.api import Api


__version__ = '1.1.0'


def connect( host, user, pw, **kwargs ):
    '''
    Connect and login to routeros device.
    Upon success return a Connection class.

    host
        Hostname to connecto to. May be ipv4,ipv6,FQDN.
    user
        Username to login with.
    pw
        Password to login with. Defaults to be empty.
    timout
        Socket timeout. Defaults to 10.
    port
        Destination port to be used. Defaults to 8728.
    logger
        Logger instance to be used. Defaults to an empty logging instance.
    saddr
        Source address to bind to.
    '''

    def_vals = { 'timeout' : 10, \
                'logger' : None, \
                'port' : 8728, \
                'saddr' : '' }

    arguments = def_vals.copy()
    arguments.update( kwargs )

    try:
        sk = create_connection( ( host, arguments['port'] ), arguments['timeout'], ( arguments['saddr'], 0 ) )
    except ( sk_error, sk_timeout ) as e:
        raise ConnError( e )

    api, rwo = _mkobj( sk, arguments['logger'] )

    try:
        chal = _initlogin( api )
        encoded = _encpw( chal, pw )
        api.run( '/login', {'name':user, 'response':encoded} )
    except ( ConnError, CmdError ) as estr:
        rwo.close()
        raise LoginError( estr )

    return api


def _mkobj(sk, logger):
    '''
    Assemble objects and return them.
    '''

    logger = _mkNullLogger() if not logger else logger
    rwo = ReaderWriter( sk, logger )
    api = Api( rwo )

    return (api, rwo)


def _initlogin( api ):
    '''
    Send initial login and return challenge response.
    '''

    snt = api.run( '/login' )
    return snt[0]['ret']



def _encpw( chal, password ):

    chal = chal.encode( 'UTF-8', 'strict' )
    chal = unhexlify( chal )
    password = password.encode( 'UTF-8', 'strict' )
    md = md5()
    md.update( b'\x00' + password + chal )
    password = hexlify( md.digest() )
    password = '00' + password.decode( 'UTF-8', 'strict' )

    return password


def _mkNullLogger():

    # this will always return same logger instance
    logger = getLogger( 'api_null_logger' )
    # ensure that logge has only 1 null handler.
    if len( logger.handlers ) == 0:
        logger.addHandler( NullHandler() )

    return logger

