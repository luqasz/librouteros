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


from binascii import unhexlify, hexlify
from hashlib import md5
from rosapi._exceptions import cmdError, apiError, loginError
import rosapi._rosapi
import socket
import logging

# global default logger. after importing rosapi it is possible to set this to some name.
# see _set_logger() for more info
parent_logger = None

def login( address, username, password, port = 8728, timeout = 10 ):
    """
    login to RouterOS via api
    takes:
        (string) address = may be fqdn or ip/ipv6 address
        (string) username = username to login
        (string) password = password to login
        (int) port = port to witch to login. defaults to 8728
        (int) timeout = socket timeout
    returns:
        rosapi class
    exceptions:
        loginError. raised when failed to log in
    """

    try:
        # try to open socket connection to given address and port with timeout
        sock = socket.create_connection( ( address, port ), timeout )
    except socket.error as estr:
        raise loginError( 'failed to login: {reason}'.format( reason = estr ) )


    # set up logger
    logger = _set_logger()

    api = _rosapi.rosapi( sock, logger = logger )
    api.write( '/login' )
    response = api.read( parse = False )
    # check for valid response.
    # response must contain !done (as frst reply word), =ret=32 characters long response hash (as second reply word))
    if len( response ) != 2 or len( response[1] ) != 37:
        raise loginError( 'did not receive challenge response' )

    # split response and get challenge response hash
    chal = response[1].split( '=', 2 )[2]
    # encode given password
    password = _pw_enc( chal, password )

    api.write( '/login', False )
    api.write( '=name=' + username, False )
    api.write( '=response=00' + password )
    response = api.read( parse = False )

    try:
        result = response[0]
    except IndexError:
        raise loginError( 'could not log in. unknown error' )
    else:
        if result == '!done':
            api._logged = True
            return api
        elif result == '!trap':
            raise loginError( 'wrong username and/or password' )
        else:
            raise loginError( 'unknown error {0}'.format( response ) )

def _pw_enc( chal, password ):
    '''
    Encode password to mikrotik format and return it.
    chal is challenge response generated every time /login is called
    password is password given to login
    '''
    chal = chal.encode( 'UTF-8', 'strict' )
    chal = unhexlify( chal )
    password = password.encode( 'UTF-8', 'strict' )
    md = md5()
    md.update( b'\x00' + password + chal )
    password = hexlify( md.digest() )
    password = password.decode( 'UTF-8', 'strict' )

    return password

def _set_logger():
    '''
    Prepare logging for rosapi. Defaults to suppress all logging
    '''
    if parent_logger:
        # create logger with parent
        logger = logging.getLogger( '{0}.rosapi'.format( parent_logger ) )
    else:
        # just create basic logger with our class name
        logger = logging.getLogger( 'rosapi' )
        # add null handler to suppress all messages
        logger.addHandler( logging.NullHandler() )

    return logger


__all__ = [k for k in list( locals().keys() ) if not k.startswith( '_' )]
