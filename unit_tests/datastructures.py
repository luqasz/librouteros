# -*- coding: UTF-8 -*-

import unittest
from mock import MagicMock

from librouteros.datastructures import ValCaster, KeyCaster, DictData


class TestValCasterMappingFromApi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.vc = ValCaster()

    def test_int_mapping(self):
        self.assertEqual( self.vc.castValToPy( '1' ) , 1 )

    def test_yes_mapping(self):
        self.assertEqual( self.vc.castValToPy( 'yes' ) , True )

    def test_no_mapping(self):
        self.assertEqual( self.vc.castValToPy( 'no' ) , False )

    def test_ture_mapping(self):
        self.assertEqual( self.vc.castValToPy( 'true' ) , True )

    def test_false_mapping(self):
        self.assertEqual( self.vc.castValToPy( 'false' ) , False )

    def test_None_mapping(self):
        self.assertEqual( self.vc.castValToPy( '' ) , None )

    def test_string_mapping(self):
        self.assertEqual( self.vc.castValToPy( 'string' ) , 'string' )

    def test_float_mapping(self):
        self.assertEqual( self.vc.castValToPy( '22.2' ) , '22.2' )


class TestValCasterMappingFromPython(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.vc = ValCaster()

    def test_None_mapping(self):
        self.assertEqual( self.vc.castValToApi( None ) , '' )

    def test_int_mapping(self):
        self.assertEqual( self.vc.castValToApi( 22 ) , '22' )

    def test_float_mapping(self):
        self.assertEqual( self.vc.castValToApi( 22.2 ) , '22.2' )

    def test_string_mapping(self):
        self.assertEqual( self.vc.castValToApi( 'string' ) , 'string' )

    def test_True_mapping(self):
        self.assertEqual( self.vc.castValToApi( True ) , 'yes' )

    def test_False_mapping(self):
        self.assertEqual( self.vc.castValToApi( False ) , 'no' )




class TestKeyCasterFromApi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.kc = KeyCaster()

    def test_no_dotkey_mapping(self):
        self.assertEqual( self.kc.castKeyToPy( 'key' ), 'key' )

    def test_dotkey_mapping(self):
        self.assertEqual( self.kc.castKeyToPy( '.key' ), 'KEY' )


class TestKeyCasterFromPython(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.kc = KeyCaster()

    def test_no_dotkey_mapping(self):
        self.assertEqual( self.kc.castKeyToApi( 'key' ), 'key' )

    def test_uppercase_key_mapping(self):
        self.assertEqual( self.kc.castKeyToApi( 'KEY' ), '.key' )



def return_same( something ):
    return something



class TestDictData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        kc = MagicMock( spec = KeyCaster )
        kc.castKeyToPy.side_effect = return_same
        kc.castKeyToApi.side_effect = return_same

        vc = MagicMock( spec = ValCaster )
        vc.castValToPy.side_effect = return_same
        vc.castValToApi.side_effect = return_same

        cls.dd = DictData( vc, kc )


    def test_mkKvTuple_returns_valid_tuple( self ):
        word = '=key=value'
        expected_result = ( 'key', 'value' )
        result = self.dd.mkKvTuple( word )

        self.assertEqual( result, expected_result )


    def test_mkAttrWord_returns_valid_word( self ):
        call_tuple = ( 'key', 'value' )
        expected_result = '=key=value'
        result = self.dd.mkAttrWord( call_tuple )

        self.assertEqual( result, expected_result )


    def test_mkApiSnt_returns_valid_sentence( self ):
        expected_result = ( '=disabled=false', '=interface=ether1' )
        call_dict = { 'interface':'ether1', 'disabled':'false' }
        result = self.dd.mkApiSnt( call_dict )
        # comparison must be done on sets. order of words doesn't matter
        # content must match
        self.assertEqual( set( result ), set( expected_result ) )


    def test_parseApiSnt_returns_valid_dictionary(self):
        call_sentence = ( '=disabled=false', '=interface=ether1' )
        expected_result = { 'interface':'ether1', 'disabled':'false' }
        result = self.dd.parseApiSnt( call_sentence )
        # comparison must be done on sets. order of words doesn't matter
        # content must match
        self.assertEqual( set( result.items() ), set( expected_result.items() ) )


    def test_parseApiResp_returns_parsed_tuple_with_dictionaries( self ):
        snt1 = ( '=disabled=false', '=interface=ether1' )
        snt2 = ( '=address=1.2.3.4', '=key=value' )
        sentences = ( snt1, snt2 )
        snt1_parsed = { 'disabled':'false', 'interface':'ether1' }
        snt2_parsed = { 'address':'1.2.3.4', 'key':'value' }
        expected_result = ( set( snt1_parsed.items() ), set( snt2_parsed.items() ) )

        result = self.dd.parseApiResp( sentences )
        result = tuple( set(d.items()) for d in result )
        self.assertEqual( result, expected_result )


    def test_parseApiResp_filters_out_empty_sentences( self ):
        sentences = ( (), () )
        expected_result = ()
        result = self.dd.parseApiResp( sentences )
        self.assertEqual( expected_result, result )

