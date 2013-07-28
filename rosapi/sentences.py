# -*- coding: UTF-8 -*-

from words import ApiAttrWord
from exc import ApiError


class readableSentence:
    '''
    Class that represents read sentence.
    '''


    def __init__( self, words = [] ):
        '''
        Each element in _words is a word object.
        '''

        self._words = list( words )


    def __iadd__( self, word ):
        '''
        Method to add word object to sentence.
        sentence += word
        '''

        if self.tag and isinstance( word, ApiAttrWord ):
            raise ApiError( 'can not add more than one tag to sentence' )

        self._words.append( word )
        return self


    def __iter__( self ):
        '''
        Returns iterator.
        '''

        return iter( self._words )


    def __len__( self ):
        '''
        Return length of sentence. How many word objects in sentence.
        '''

        return len( self._words )


    def __repr__( self ):
        return '<readableSentence WORDS={self._words!r}>'.format( self = self )


class writeableSentence:
    '''
    Class that represents sentence to write.
    '''


    def __init__( self, cmd_word ):
        '''
        Each element in _words is a word object.
        Every sentence to write must begin with a command word.
        '''
        self._words = [cmd_word]


    def __iadd__( self, word ):
        '''
        Method to add word object to sentence.
        sentence += word
        '''

        if isinstance( word, ApiAttrWord ):
            raise ApiError( 'can not add more than one tag to sentence' )

        self._words.append( word )
        return self


    def __iter__( self ):
        '''
        Returns iterator.
        As first word command word is set.
        '''

        return iter( self._words )


    def __len__( self ):
        '''
        Return length of sentence. How many word objects in sentence.
        '''

        return len( self._words )


    def __repr__( self ):
        return '<writeableSentence WORDS={self._words!r}>'.format( self = self )
