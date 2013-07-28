# -*- coding: UTF-8 -*-

class Error( Exception ):
    '''
    This is a base exception for all other.
    '''




class ApiError( Error ):
    '''
    Exception raised when some internal api error occurred.
    This is a base class for other api related errors.
    '''


class LoginError( ApiError ):
    '''
    Exception raised when login attempt failed.
    '''


class CmdError( ApiError ):
    '''
    Exception raised when execution of a command has failed.
    '''

#     reason
#     cmd
#     tag




class ConnError( Error ):
    '''
    This exception is a base class for other connection related exceptions.
    '''


class RwError( ConnError ):
    '''
    Exception raised when i/o operation on socket failed.
    
    :ivar msg: Message string with detailed reason.
    '''
    def __init__( self, msg ):
        self.msg = msg




