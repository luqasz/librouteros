# -*- coding: UTF-8 -*-

class Error( Exception ):
    '''
    This is a base exception for all other.
    '''




class ApiError( Error ):
    '''
    Api related errors.
    This is a base class for other api related errors.
    '''


class LoginError( ApiError ):
    '''
    Login attempt errors.
    '''


class CmdError( ApiError ):
    '''
    Execution of a command errors.
    '''




class ConnError( Error ):
    '''
    Connection related errors.
    This is a base class for other connection related exceptions.
    '''


class RwTimeout( ConnError ):
    '''
    Exception raised when timeout is reached while
    reading/writing to/from socket.
    '''


class RwError( ConnError ):
    '''
    Exception raised when i/o operation on socket failed.
    '''


class ConnClosed( ConnError ):
    '''
    Exception raised when connection is unexpectedly closed.
    While reading sentence !fatal word is received.
    '''
