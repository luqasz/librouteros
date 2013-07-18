# -*- coding: UTF-8 -*-


class ApiSocketDriver:


    def __init__( self ):
        pass


    def mkSnt( self, cmd_word, args ):
        pass


    def parseSnt( self, sentence ):
        pass


    def sendAndReceive( self, sentence ):
        '''
        Write sentence and read as long as EOR (end of response).
        EOR is a combination of two words. Either !done or !fatal and a EOS
        Passed sentence is a writeableSentence object.
        
        Returns list of read sentences.
        '''

        sentences = []
        self.writeSentence( sentence )
        while True:
            read_sentence = self.readSentence()
            sentences.append( read_sentence )
            if '!done' in read_sentence:
                return sentences






class KVDataParser:


    def castValToPython( self, value ):
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


class KVDataParser_3_x( KVDataParser ):


    def __init__( self ):
        self.py_mapping = {'yes': True, 'no': False, '': None}
        self.api_mapping = { True:'yes' , False:'no' , None:''}


class KVDataParser_4_x( KVDataParser ):


    def __init__( self ):
        self.api_mapping = { True:'true' , False:'false' , None:''}
        self.py_mapping = {'true': True, 'false': False, '': None}

