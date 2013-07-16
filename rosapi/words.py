# -*- coding: UTF-8 -*-

class genericWord:

    def __init__( self, word ):
        self.word = word


    def __len__( self ):
        return len( self.word )


    def __str__( self ):
        return self.word


###################
# Key value words
###################

class KvWord( genericWord ):
    pass


class attributeWord( KvWord ):
    '''
    This class represent word that starts with '='
    Available for reading and writing
    '''

    def __repr__( self ):
        return '<attributeWord WORD={self.word!r}>'.format( self = self )


class apiAttributeWord( KvWord ):
    '''
    Class that represents an api attribute word.
    Available for reading and writing.
    Such word starts with '.'.
    '''


    def __repr__( self ):
        return '<apiAttributeWord WORD={self.word!r}>'.format( self = self )


class queryWord( KvWord ):
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


    def __repr__( self ):
        return '<queryWord WORD={self.word!r}>'.format( self = self )

###################
# No key value words
###################

class commandWord( genericWord ):
    '''
    Class that represents a command word.
    For example '/ip/service/print'
    '''


    def __repr__( self ):
        return '<commandWord WORD={self.word!r}>'.format( self = self )

class replyWord( genericWord ):
    '''
    Class that represents a reply word. This word starts with '!' character.
    For example: !tag, !done, !re, !fatal.
    This word is available for reading only.
    '''


    def __repr__( self ):
        return '<replyWord WORD={self.word!r}>'.format( self = self )


###################
# Unknown word type
###################

class unknownWord( genericWord ):
    '''
    This class represent a word that is an unknown type.
    Received on response to '/quit' command
    '''


    def __repr__( self ):
        return '<unknownWord WORD={self.word!r}>'.format( self = self )





def getWordType( word ):
    '''
    Return an object word class based on leading characters. 
    '''

    maping = {'=':attributeWord, '!': replyWord, '.':apiAttributeWord, '?':queryWord, '/':commandWord }
    return maping.get( word[0], unknownWord )

