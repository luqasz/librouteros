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
    Execution of a command errors.
    '''


class ConnError( LibError ):
    '''
    Connection related errors.
    '''
