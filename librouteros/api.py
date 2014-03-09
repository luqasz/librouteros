# -*- coding: UTF-8 -*-

from librouteros.drivers import trapCheck
from librouteros.datastructures import mksnt, parsresp



class Api:


    def __init__( self, drv ):
        self.drv = drv


    def talk( self, cmd, args = dict() ):
        '''
        Run any 'non interactive' command. Returns parsed response.

        cmd Command word eg. /ip/address/print.
        args Dictionary with key, value pairs.
        '''

        args = mksnt( args )
        self.drv.writeSnt( cmd, args )
        response = self.drv.readDone()
        trapCheck( response )
        parsed = parsresp( response )

        return parsed

