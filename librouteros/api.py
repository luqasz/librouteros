# -*- coding: UTF-8 -*-

from librouteros.drivers import trapCheck

class Api:


    def __init__( self, drv ):
        self.drv = drv


    def talk( self, cmd, args = dict() ):

        args = self.drv.mkApiSnt( args )
        self.drv.writeSnt( cmd, args )
        response = self.drv.readDone()
        trapCheck( response )
        parsed = self.drv.parseResp( response )

        return parsed

