# -*- coding: UTF-8 -*-

class Response:
    '''
    A class that represents a read response. It may contain 1 or more sentences.
    Each sentence is a dictionary containing key, value pairs.
    '''


    def __init__( self, sentences, tag ):
        self.tag = tag
        self._sentences = tuple( sentences )


    def __contains__( self, sentence ):
        '''
        Method to test sentence membership
        '''

        return sentence in self._sentences

    def __getitem__( self, key ):
        return self._sentences[key]

    def __format__( self, option ):
        pass

    def __str__( self ):
        '''
        Return string representation of response
        '''

        return str( self._sentences )

    def __iter__( self ):
        '''
        Return iterator over response.
        Each element is a sentence.
        '''

        return iter( self._sentences )


    def __len__( self ):
        '''
        Return number of sentences in response.
        '''

        return len( self._sentences )


