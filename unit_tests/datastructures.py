# -*- coding: UTF-8 -*-

import unittest
from mock import patch, MagicMock, call

from librouteros.datastructures import DictData, castKeyToApi, castKeyToPy, castValToPy, castValToApi, typeCheck


class TestValCastingFromApi(unittest.TestCase):


    def test_int_mapping(self):
        self.assertEqual( castValToPy( '1' ) , 1 )

    def test_yes_mapping(self):
        self.assertEqual( castValToPy( 'yes' ) , True )

    def test_no_mapping(self):
        self.assertEqual( castValToPy( 'no' ) , False )

    def test_ture_mapping(self):
        self.assertEqual( castValToPy( 'true' ) , True )

    def test_false_mapping(self):
        self.assertEqual( castValToPy( 'false' ) , False )

    def test_None_mapping(self):
        self.assertEqual( castValToPy( '' ) , None )

    def test_string_mapping(self):
        self.assertEqual( castValToPy( 'string' ) , 'string' )

    def test_float_mapping(self):
        self.assertEqual( castValToPy( '22.2' ) , '22.2' )


class TestValCastingFromPython(unittest.TestCase):


    def test_None_mapping(self):
        self.assertEqual( castValToApi( None ) , '' )

    def test_int_mapping(self):
        self.assertEqual( castValToApi( 22 ) , '22' )

    def test_float_mapping(self):
        self.assertEqual( castValToApi( 22.2 ) , '22.2' )

    def test_string_mapping(self):
        self.assertEqual( castValToApi( 'string' ) , 'string' )

    def test_True_mapping(self):
        self.assertEqual( castValToApi( True ) , 'yes' )

    def test_False_mapping(self):
        self.assertEqual( castValToApi( False ) , 'no' )




class TestKeyCastingFromApi(unittest.TestCase):


    def test_no_dotkey_mapping(self):
        self.assertEqual( castKeyToPy( 'key' ), 'key' )

    def test_dotkey_mapping(self):
        self.assertEqual( castKeyToPy( '.key' ), 'KEY' )


class TestKeyCastingFromPython(unittest.TestCase):


    def test_no_dotkey_mapping(self):
        self.assertEqual( castKeyToApi( 'key' ), 'key' )

    def test_uppercase_key_mapping(self):
        self.assertEqual( castKeyToApi( 'KEY' ), '.key' )



def return_same( something ):
    return something



class KeyValueTupleCreation(unittest.TestCase):


    def setUp(self):
        self.dd = DictData()


    @patch('librouteros.datastructures.castKeyToPy')
    @patch('librouteros.datastructures.castValToPy')
    def test_mkKvTuple_returns_valid_tuple( self, key_mock, val_mock ):
        key_mock.side_effect = return_same
        val_mock.side_effect = return_same

        word = '=key=value'
        expected_result = ( 'key', 'value' )
        result = self.dd.mkKvTuple( word )

        self.assertEqual( result, expected_result )



class AttributeWordCreation(unittest.TestCase):


    def setUp(self):
        self.dd = DictData()


    @patch('librouteros.datastructures.castKeyToApi')
    @patch('librouteros.datastructures.castValToApi')
    def test_mkAttrWord_returns_valid_word( self, key_mock, val_mock ):
        key_mock.side_effect = return_same
        val_mock.side_effect = return_same

        call_tuple = ( 'key', 'value' )
        expected_result = '=key=value'
        result = self.dd.mkAttrWord( call_tuple )

        self.assertEqual( result, expected_result )


    def test_data_type_attribute_existance(self):
        self.assertIs( self.dd.data_type, dict )



class ApiSentenceCreation(unittest.TestCase):


    def setUp(self):
        self.dd = DictData()
        self.dd.mkAttrWord = MagicMock()


    def test_calls_attribute_word_creation_method( self ):
        call_dict = { 'interface':'ether1', 'disabled':'false' }
        expected_calls = [ call(item) for item in call_dict.items() ]

        self.dd.mkApiSnt( call_dict )
        self.assertEqual( self.dd.mkAttrWord.mock_calls, expected_calls )



class ApiResponseParsing(unittest.TestCase):


    def setUp(self):
        self.dd = DictData()
        self.dd.parseApiSnt = MagicMock( return_value = () )


    def test_filters_out_empty_sentences( self ):
        sentences = ( (), () )
        expected_result = ()
        result = self.dd.parseApiResp( sentences )
        self.assertEqual( expected_result, result )


    def test_calls_api_sentence_parsing_method( self ):
        sentences = ( (1,2), (1,2) )
        expected_calls = [ call(elem) for elem in sentences ]

        self.dd.parseApiResp( sentences )
        calls = self.dd.parseApiSnt.mock_calls
        self.assertEqual( calls, expected_calls )


class TypeCheck(unittest.TestCase):


    def test_raises_if_wrong_data_type(self):
        self.assertRaises( TypeError, typeCheck, ( dict(), tuple ) )

    def test_does_not_raise_if_valid(self):
        typeCheck( dict(), dict )


class ApiSentenceParsing(unittest.TestCase):


    def setUp(self):
        self.dd = DictData()
        self.dd.mkKvTuple = MagicMock( return_value = (1,2) )


    def test_calls_tuple_creation_method(self):
        call_snt = ( '=disabled=false', '=interface=ether1' )

        self.dd.parseApiSnt( call_snt )
        call_list = [ call(elem) for elem in call_snt ]
        self.assertEqual( call_list, self.dd.mkKvTuple.mock_calls )


    def test_filters_out_non_attribute_words(self):
        call_snt = ( '=disabled=false', '=interface=ether1', 'no_attr_word' )

        self.dd.parseApiSnt( call_snt )
        call_list = [ call(elem) for elem in call_snt[:2] ]
        self.assertEqual( call_list, self.dd.mkKvTuple.mock_calls )
