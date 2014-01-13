# -*- coding: UTF-8 -*-

from binascii import unhexlify, hexlify
from hashlib import md5

from librouteros.exc import CmdError, LoginError
from librouteros.datastructures import typeCheck



def sntTrapParse( snt ):

    #discard all api attribute words and reply words
    error_message = ' '.join( word for word in snt if word[0] not in ( '!', '.' ) )

    return error_message


def trapCheck( snts ):
    '''
    Check for existance of !trap word. This word indicates that an error occured.
    At least one !trap word in any sentence triggers an error.
    Unfortunatelly mikrotik api may throw one or more errors as response.

    :param snts: Iterable with each sentence as tuple
    '''

    error_messages = []

    for sentence in snts:
        if '!trap' in sentence:
            error_message = sntTrapParse( sentence )
            error_messages.append( error_message )

    if error_messages:
        msg = ', '.join( error_messages )
        raise CmdError( msg )


def getChal(sentence):
    '''
    Extract challenge argument from sentence.

    :returns: Challenge argument
    '''
    # get challenge key + value as one element tuple
    chal = tuple( word for word in sentence if word.startswith( '=ret=' ) )
    # get the first element
    try:
        chal = chal[0]
    except IndexError:
        raise LoginError( 'could not read challenge argument' )

    # extract chall argument from key value pair
    # =ret=xxxxxx
    return chal[5:]


def encPass( chal, password ):

    chal = chal.encode( 'UTF-8', 'strict' )
    chal = unhexlify( chal )
    password = password.encode( 'UTF-8', 'strict' )
    md = md5()
    md.update( b'\x00' + password + chal )
    password = hexlify( md.digest() )
    password = '00' + password.decode( 'UTF-8', 'strict' )

    return password






class ApiSocketDriver:


    def __init__( self, conn, data_struct ):
        self.conn = conn
        self.data_struct = data_struct


    def mkApiSnt( self, data ):

        typeCheck( data, self.data_struct.data_type )
        return self.data_struct.mkApiSnt( data )


    def parseResp( self, response ):

        return self.data_struct.parseApiResp( response )


    def writeSnt( self, lvl, args = tuple() ):

        snt = ( lvl, ) + args
        self.conn.writeSentence( snt )


    def readSnt( self ):

        return self.conn.readSentence()


    def readDone( self ):
        '''
        Read as long as !done is received.

        :returns: Read sentences as tuple.
        '''

        snts = []

        while True:

            snt = self.readSnt()
            snts.append( snt )

            if '!done' in snt:
                break

        return tuple( snts )


    def close( self ):

        self.conn.close()

