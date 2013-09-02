# -*- coding: UTF-8 -*-

from logging import getLogger, NullHandler

from rosapi.api import Api
from rosapi.drivers import ApiSocketDriver, ValCaster
from rosapi.connections import ReaderWriter, mk_plain_sk

def connect( host, username, password, port = 8728,
            timeout = 10, saddr = '', sport = 0,
            logger = None ):
    '''
    Simplified function to connect and log in to remote host.
    On success returns Api object.
    '''


    if not logger:
        logger = getLogger( 'rosapi' )
        logger.addHandler( NullHandler() )
    else:
        logger = logger

    sk = mk_plain_sk( host, port, timeout, saddr, sport )

    rwo = ReaderWriter( sk, logger )
    vc = ValCaster()
    drv = ApiSocketDriver( rwo, logger, vc )
    api = Api( drv, logger )

    api.login( username, password )

    return api
