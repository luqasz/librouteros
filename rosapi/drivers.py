# -*- coding: UTF-8 -*-


class ApiSocketDriver:


    def __init__( self ):
        pass








class KVDataParser:


    def castValToPython( self, value ):
        '''
        Cast value into python type
        No float casting available
        '''
        try:
            casted = int( value )
        except ValueError:
            casted = self.py_mapping.get( value, value )
        return casted


    def castValToApi( self, value ):
        '''
        Cast from python type into api equivalent
        No float casting available
        '''
        casted = self.api_mapping.get( value, str( value ) )
        return casted


class KVDataParser_3_x( KVDataParser ):


    def __init__( self ):
        self.py_mapping = {'yes': True, 'no': False, '': None}
        self.api_mapping = { True:'yes' , False:'no' , None:''}


class KVDataParser_4_x( KVDataParser ):


    def __init__( self ):
        self.api_mapping = { True:'true' , False:'false' , None:''}
        self.py_mapping = {'true': True, 'false': False, '': None}

