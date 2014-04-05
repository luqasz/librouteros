# -*- coding: UTF-8 -*-

from librouteros.exc import CmdError, ConnError

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




def parsresp(sentences):
    '''
    Parse given response to set of dictionaries containing parsed sentences.

    :praam sentences: Iterable (tuple,list) with each element as a sentence
    '''

    response = map( parsnt, sentences )
    # filter out empty sentences
    filtered = filter( None, response )
    return tuple( filtered )


def mksnt( data ):
    '''
    Convert dictionary to attribute words.

    :param args: Dictionary with key value attributes.
    Those will be converted to attribute words.

    :returns: Tuple with attribute words.
    '''

    converted = map( mkattrwrd, data.items() )
    return tuple( converted )


def parsnt( snt ):
    '''
    Parse given sentence from attribute words to dictionary.
    Only retrieve words that start with '='.
    This method may return an empty dictionary.

    :param snt: Iterable sentence.
    :returns: Dictionary with attributes.
    '''

    attrs = ( word for word in snt if word.startswith( '=' ) )
    attrs = map( convattrwrd, attrs )

    return dict( attrs )


def mkattrwrd( kv ):
    '''
    Make an attribute word out of key value tuple. Values and keys are automaticly casted
    to api equivalents.

    :param kv: Two element tuple. First key, second value.
    '''

    key, value = kv
    casted_value = castValToApi( value )
    casted_key = castKeyToApi( key )

    return '={0}={1}'.format( casted_key, casted_value )


def convattrwrd( word ):
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



def trapCheck( snts ):
    '''
    Check for existance of !trap word. This word indicates that an error occured.
    At least one !trap word in any sentence triggers an error.
    Unfortunatelly mikrotik api may throw one or more errors as response.

    :param snts: Iterable with each sentence as tuple
    '''

    errmsgs = []

    for snt in snts:
        if '!trap' in snt:
            emsg = ' '.join( word for word in snt )
            errmsgs.append( emsg )

    if errmsgs:
        e = ', '.join( errmsgs )
        raise CmdError( e )


def raiseIfFatal( sentence ):
    '''
    Check if a given sentence contains error message. If it does then raise an exception.
    !fatal means that connection have been closed and no further transmission will work.
    '''

    if '!fatal' in sentence:
        error = ', '.join( word for word in sentence if word != '!fatal' )
        raise ConnError( error )

