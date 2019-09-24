def parseWord(word):
    """
    Split given attribute word to key, value pair.

    Values are casted to python equivalents.

    :param word: API word.
    :returns: Key, value pair.
    """
    mapping = {'yes': True, 'true': True, 'no': False, 'false': False}
    _, key, value = word.split('=', 2)
    try:
        value = int(value)
    except ValueError:
        value = mapping.get(value, value)
    return (key, value)



def pyCast(value):
    """Cast python equivalent to API."""
    mapping = {True: 'yes', False: 'no'}
    # this is necesary because 1 == True, 0 == False
    if type(value) == int:
        value = str(value)
    else:
        value = mapping.get(value, str(value))
    return value


def composeWord(key, value):
    """
    Create a attribute word from key, value pair.
    Values are casted to api equivalents.
    """
    return '={}={}'.format(key, pyCast(value))
