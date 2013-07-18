# -*- coding: UTF-8 -*-

from words import genericWord, ApiAttrWord

class genericSentence:
    '''
    A generic class that represents a sentence.
    '''


    def _set_tag( self, value ):
        pass


    def _get_tag( self ):
        pass


    tag = property( _get_tag, _set_tag )


    def __init__( self ):
        '''
        Each element in _words is a word object.
        '''
        self._words = []


    def __isub__( self, word ):
        '''
        Method to remove word object from sentence.
        sentence -= word
        
        This method may raise ValueError if word object is not present in the sentence
        '''
        self._words.remove( word )
        return self


    def __iadd__( self, word ):
        '''
        Method to remove word object from sentence.
        sentence += word
        '''
        self._words.append( word )
        return self


    def __contains__( self, word ):
        '''
        Method to test word membership. Word may be an object, or string. 
        If string then exact words as strings must match.
        
        :param word: word object or string
        '''
        if isinstance( word, genericWord ):
            return word in self._words
        elif isinstance( word, str ):
            return word in [str( word ) for word in self]


    def __len__( self ):
        '''
        Return length of sentence. How many word objects in sentence.
        '''

        return len( self._words )


    def __iter__( self ):
        '''
        Returns iterator from list.
        '''

        return iter( self._words )


class readableSentence( genericSentence ):
    '''
    Class that represents read sentence.
    '''


    def __repr__( self ):
        return '<readableSentence WORDS={self._words!r}, TAG={self.tag!r}>'.format( self = self )


class writeableSentence( genericSentence ):
    '''
    Class that represents sentence to write.
    '''


    def __init__( self, cmd_word ):
        '''
        Each element in _words is a word object.
        Every sentence to write must begin with a command word.
        '''
        self._words = [cmd_word]


    def __repr__( self ):
        return '<writeSentence WORDS={self._words!r}, TAG={self.tag!r}>'.format( self = self )

