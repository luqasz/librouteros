# -*- coding: UTF-8 -*-


def dictdiff( wanted, present, split_keys=tuple(), split_char=',' ):
    '''
    Compare two dictionaries and return items from wanted not listed in present.
    If split_keys and split_char is provided, additional comparison is made based on provided keys.

    wanted
        Dictionary with wanted items.
    present
        Dictionary with present items.
    split_keys
        Iterable with key names to split values from.
    split_char
        Character used to split keys by.
    '''

    difference = dict( set( wanted.items() ) - set( present.items() ) )

    for key in split_keys:
        welem = wanted.get( key, '' )
        pelem = present.get( key, '' )
        difference[ key ] = diffstr( welem, pelem, split_char )

    return difference


def diffstr( welem, pelem, splchr ):
    '''
    Compare two strings and return items from welem not present in pelem.
    Items from pelem,welem are splitted by splchr and compared.
    Returns string joined by splchr.


    welem
        String containing desired elements.
    pelem
        String containing present elements.
    splchr
        Split character to split welem and pelem by.
    '''

    wanted = welem.split( splchr )
    present = pelem.split( splchr )
    diff = set( wanted ) - set( present )

    return splchr.join( diff )

