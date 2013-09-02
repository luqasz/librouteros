# -*- coding: UTF-8 -*-

from rosapi.exc import ConnClosed, CmdError
from socket import SHUT_RDWR, error as sock_error


class ApiSocketDriver:


    def __init__( self, conn, logger, val_caster ):
        self.valCaster = val_caster
        self.logger = logger
        self.conn = conn


    def mkSnt( self, cmd_word, args ):
        '''
        Construct a sentence to write.

        :param cmd_word: Command word.

        :param args: Dictionary with key value attributes.
        Those will be converted to attribute words.

        :returns: Iterable with words.
        '''

        snt = map( self.mkAttrWord, args.items() )
        snt = ( cmd_word, ) + tuple(snt)
        return snt


    def parseSnt( self, snt ):
        '''
        Parse given sentence. Only retrieve words that start with '='.
        This method may return an empty dictionary.

        :param snt: Iterable sentence.
        :returns: Dictionary with attributes.
        '''

        attrs = ( word for word in snt if word.startswith( '=' ) )
        attrs = map( self.mkKvTuple, attrs )

        return dict( attrs )


    def mkAttrWord( self, kv ):
        '''
        Make an attribute word. Values are automaticly casted
        to api equivalents. Uppercase keys are lowered and a
        leading '.' is added.

        :param kv: Two element tuple. First key, second value.
        '''

        key, value = kv
        key = key if not key.isupper() else '.' + key.lower()
        value = self.valCaster.castValToApi( value )

        return '={0}={1}'.format( key, value )


    def mkKvTuple( self, word ):
        '''
        Make an key value tuple out of attribute word. Values
        are automaticly casted to python equivalents. keys that
        start with '.' are converted to uppercase and a leading '.'
        is removed.

        :param word: Attribute word.
        '''

        splitted = word.split( '=', 2 )
        key = splitted[1]
        key = key if not key.startswith( '.' ) else key[1:].upper()
        value = splitted[2]
        value = self.valCaster.castValToPy( value )

        return ( key, value )


    def writeSnt( self, snt ):
        '''
        Write sentence to connection.

        :param snt: Iterable with words.
        '''

        for word in snt:
            self.logger.info( '<--- {word!s}'.format( word = word ) )

        self.logger.info( '<--- EOS' )

        self.conn.writeSnt( snt )


    def readSnt( self ):
        '''
        Read sentence from connection.

        :returns: Iterable with words.
        '''

        snt = self.conn.readSnt()

        for word in snt:
            self.logger.info( '---> {word!s}'.format( word = word ) )

        self.logger.info( '---> EOS' )

        if '!fatal' in snt:
            # !fatal means that connection have been closed.
            # Remove !fatal from sentence
            estr = ', '.join( word for word in snt if word != '!fatal' )
            self.close()
            raise ConnClosed( estr )

        if '!trap' in snt:
            snt = self.parseSnt( snt )
            estr = ', '.join( '{0}={1!r}'.format( k, v ) for k, v in snt.items() )
            raise CmdError( estr )

        return snt


    def readDone( self ):
        '''
        Read as long as !done is received.

        :returns: Iterable with sentences
        '''

        snts = []
        errors = []

        while True:

            try:
                snt = self.readSnt()
            except CmdError as e:
                errors.append( e )
            else:
                if '!done' in snt:
                    break
                else:
                    snts.append( snt )

        if errors:
            estr = ', '.join( errors )
            raise CmdError( estr )

        return snts


    def close( self ):
        '''
        Close the socket.
        '''

        self.logger.debug('Driver closing socket.')

        if self.conn.sock._closed:
            return
        # shutdown socket
        try:
            self.conn.sock.shutdown( SHUT_RDWR )
        except sock_error:
            pass
        finally:
            self.conn.sock.close()



class ValCaster:

    def __init__( self ):
        self.py_mapping = {'yes': True, \
                           'true': True, \
                           'no': False, \
                           'false': False, \
                           '': None}
        self.api_mapping = { True:'yes', \
                            False:'no', \
                            None:''}


    def castValToPy( self, value ):
        '''
        Cast value into python type
        No float casting available
        '''

        try:
            casted = int( value )
        except ValueError:
            casted = self.py_mapping.get( value, value )
        return casted


    def castValToApi( self, value ):
        '''
        Cast from python type into api equivalent
        No float casting available
        '''

        casted = self.api_mapping.get( value, str( value ) )
        return casted
