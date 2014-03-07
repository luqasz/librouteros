# -*- coding: UTF-8 -*-

from binascii import unhexlify, hexlify
from hashlib import md5

from librouteros.exc import CmdError, ConnError



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


def raiseIfFatal( sentence ):
    '''
    Check if a given sentence contains error message. If it does then raise an exception.
    !fatal means that connection have been closed and no further transmission will work.
    '''

    if '!fatal' in sentence:
        error = ', '.join( word for word in sentence if word != '!fatal' )
        raise ConnError( error )


def encPass( chal, password ):

    chal = chal.encode( 'UTF-8', 'strict' )
    chal = unhexlify( chal )
    password = password.encode( 'UTF-8', 'strict' )
    md = md5()
    md.update( b'\x00' + password + chal )
    password = hexlify( md.digest() )
    password = '00' + password.decode( 'UTF-8', 'strict' )

    return password


def log_snt( logger, sentence, direction ):

    dstrs = { 'write':'<---', 'read':'--->' }
    dstr = dstrs.get( direction )

    for word in sentence:
        logger.debug( '{0} {1!r}'.format( dstr, word ) )

    logger.debug( '{0} EOS'.format( dstr ) )






class SocketDriver:


    def __init__( self, conn, logger):
        self.conn = conn
        self.logger = logger


    def writeSnt( self, lvl, args ):

        snt = ( lvl, ) + args
        self.conn.writeSentence( snt )
        log_snt( self.logger, snt, 'write' )


    def readSnt( self ):

        snt = self.conn.readSentence()
        log_snt( self.logger, snt, 'read' )
        raiseIfFatal( snt )

        return snt


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

