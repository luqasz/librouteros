# -*- coding: UTF-8 -*-

class GenericWord( str ):


    def __repr__( self ):
        return '<{clsname} \'{word}\'>'.format( clsname = self.__class__.__name__, word = self )


###################
# Key value words
###################


class AttrWord( GenericWord ):
    '''
    This class represent word that starts with '='
    Available for reading and writing.
    '''


    def __init__( self, word, key, value ):
        self.word = word
        self.key = key
        self.value = value


class ApiAttrWord( genericWord ):
    '''
    Class that represents an api attribute word.
    Available for reading and writing.
    Such word starts with '.'.
    '''


    def __init__( self, word, key, value ):
        self.word = word
        self.key = key
        self.value = value


###################
# No key value words
###################


class queryWord( genericWord ):
    '''
    Class that represents a query word.
    Query words start with '?' character.
    This word is available for writing only.
    '''


    def __eq__( self, other ):
        '''
        self == other
        '''
        other = self.typeCast( other )
        return queryWord( '?={0}={1}'.format( self.name, other ) )

    def __ne__( self, other ):
        '''
        self != other
        '''
        other = self.typeCast( other )
        if other:
            return queryWord( '?={0}={1}'.format( self.name, other ) )
        else:
            return queryWord( '?>{0}={1}'.format( self.name, other ) )

    def __lt__( self, other ):
        '''
        self < other
        '''
        other = self.typeCast( other )
        return '?<{0}={1}'.format( self.name, other )

    def __gt__( self, other ):
        '''
        self > other
        '''
        other = self.typeCast( other )
        return queryWord( '?>{0}={1}'.format( self.name, other ) )


class commandWord( genericWord ):
    '''
    Class that represents a command word.
    For example '/ip/service/print'
    This word is available for writing only.
    '''


class replyWord( genericWord ):
    '''
    Class that represents a reply word. This word starts with '!' character.
    For example: !tag, !done, !re, !fatal.
    This word is available for reading only.
    '''


###################
# Unknown word type
###################

class unknownWord( genericWord ):
    '''
    This class represent a word that is an unknown type.
    Received on response to '/quit' command
    '''


class WordProducer:
    pass


def mkAttrWord():
    pass

def mkApiAttrWord():
    pass



def getWordType( word ):
    '''
    Return an object word class based on leading characters. 
    '''

    maping = {'=':AttrWord, '!': replyWord, '.':ApiAttrWord, '?':queryWord, '/':commandWord }
    return maping.get( word[0], unknownWord )

