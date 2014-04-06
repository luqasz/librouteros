# -*- coding: UTF-8 -*-

class LibError( Exception ):
    '''
    This is a base exception for all other.
    '''


class LoginError( LibError ):
    '''
    Login attempt errors.
    '''


class CmdError( LibError ):
    '''
    Commend execution errors.
    '''


class ConnError( LibError ):
    '''
    Connection related errors.
    '''
