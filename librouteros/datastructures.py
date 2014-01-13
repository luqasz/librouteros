# -*- coding: UTF-8 -*-


to_py_mapping = {'yes': True, \
                   'true': True, \
                   'no': False, \
                   'false': False, \
                   '': None}

to_api_mapping = { True:'yes', \
                    False:'no', \
                    None:''}


def castValToPy( value ):

    try:
        casted = int( value )
    except ValueError:
        casted = to_py_mapping.get( value, value )
    return casted


def castValToApi( value ):

    casted = to_api_mapping.get( value, str( value ) )
    return casted



def castKeyToPy( key ):
    '''
    Any key that starts with . will be converted to uppercase.
    '''
    if key[0] == '.':
        return key[1:].upper()
    else:
        return key


def castKeyToApi( key ):
    '''
    Any key that is uppercase will be converted to lowercase and a . will be prefixed.
    '''
    if key.isupper():
        return '.' + key.lower()
    else:
        return key


def typeCheck( data, expected ):

    if not isinstance( data, expected ):
        raise TypeError('provided data type is not {TYPE}'.format( TYPE = expected ))



class DictData:
    '''
    This class represents dictionary data structure methods.
    '''

    def __init__(self):
        self.data_type = dict


    def parseApiResp(self, sentences):
        '''
        Parse given response to set of dictionaries containing parsed sentences.

        :praam sentences: Iterable (tuple,list) with each element as a sentence
        '''

        response = map( self.parseApiSnt, sentences )
        # filter out empty sentences
        filtered = filter( None, response )
        return tuple( filtered )


    def mkApiSnt( self, data ):
        '''
        Convert dictionary to attribute words.

        :param args: Dictionary with key value attributes.
        Those will be converted to attribute words.

        :returns: Tuple with attribute words.
        '''

        converted = map( self.mkAttrWord, data.items() )
        return tuple( converted )


    def parseApiSnt( self, snt ):
        '''
        Parse given sentence from attribute words to dictionary.
        Only retrieve words that start with '='.
        This method may return an empty dictionary.

        :param snt: Iterable sentence.
        :returns: Dictionary with attributes.
        '''

        attrs = ( word for word in snt if word.startswith( '=' ) )
        attrs = map( self.mkKvTuple, attrs )

        return dict( attrs )


    def mkAttrWord( self, kv ):
        '''
        Make an attribute word. Values and keys are automaticly casted
        to api equivalents.

        :param kv: Two element tuple. First key, second value.
        '''

        key, value = kv
        casted_value = castValToApi( value )
        casted_key = castKeyToApi( key )

        return '={0}={1}'.format( casted_key, casted_value )


    def mkKvTuple( self, word ):
        '''
        Make an key value tuple out of attribute word. Values and keys
        are automaticly casted to python equivalents.

        :param word: Attribute word.
        '''

        splitted = word.split( '=', 2 )
        key = splitted[1]
        casted_key = castKeyToPy( key )
        value = splitted[2]
        casted_value = castValToPy( value )

        return ( casted_key, casted_value )


