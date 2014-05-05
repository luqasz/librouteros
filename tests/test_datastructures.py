# -*- coding: UTF-8 -*-

import unittest
try:
    from unittest.mock import MagicMock, patch, call
except ImportError:
    from mock import MagicMock, patch, call

from librouteros.datastructures import parsresp, parsnt, mksnt, mkattrwrd, convattrwrd, castKeyToApi, castKeyToPy, castValToPy, castValToApi, raiseIfFatal, trapCheck
from librouteros.exc import CmdError, ConnError



class TrapChecking(unittest.TestCase):


    def test_trap_in_sentences_raises(self):
        snts = ( '!trap', '=key=value' )
        self.assertRaises( CmdError, trapCheck, snts )


class RaiseIfFatal(unittest.TestCase):


    def test_raises_when_fatal(self):
        sentence = ('!fatal', 'connection terminated by remote hoost')
        self.assertRaises( ConnError,  raiseIfFatal, sentence )


    def test_does_not_raises_if_no_error(self):
        raiseIfFatal( 'some string without error' )


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



class AttributeWordConversion(unittest.TestCase):


    @patch('librouteros.datastructures.castKeyToPy')
    @patch('librouteros.datastructures.castValToPy')
    def test_returns_valid_tuple( self, key_mock, val_mock ):
        key_mock.side_effect = return_same
        val_mock.side_effect = return_same

        word = '=key=value'
        expected_result = ( 'key', 'value' )
        result = convattrwrd( word )

        self.assertEqual( result, expected_result )



class AttributeWordCreation(unittest.TestCase):


    @patch('librouteros.datastructures.castKeyToApi')
    @patch('librouteros.datastructures.castValToApi')
    def test_returns_valid_word( self, key_mock, val_mock ):
        key_mock.side_effect = return_same
        val_mock.side_effect = return_same

        call_tuple = ( 'key', 'value' )
        expected_result = '=key=value'
        result = mkattrwrd( call_tuple )

        self.assertEqual( result, expected_result )



class ApiSentenceCreation(unittest.TestCase):


    @patch('librouteros.datastructures.mkattrwrd')
    def test_calls_attribute_word_creation_method( self, mk_mock ):
        call_dict = { 'interface':'ether1', 'disabled':'false' }
        expected_calls = [ call(item) for item in call_dict.items() ]

        mksnt( call_dict )
        self.assertEqual( mk_mock.mock_calls, expected_calls )



class ApiResponseParsing(unittest.TestCase):


    def setUp(self):
        parsnt_patcher = patch('librouteros.datastructures.parsnt')
        self.parsnt_mock = parsnt_patcher.start()
        self.parsnt_mock.return_value = ()
        self.addCleanup(parsnt_patcher.stop)


    def test_filters_out_empty_sentences( self ):
        sentences = ( (), () )
        expected_result = ()
        result = parsresp( sentences )
        self.assertEqual( expected_result, result )


    def test_calls_api_sentence_parsing_method( self ):
        sentences = ( (1,2), (1,2) )
        expected_calls = [ call(elem) for elem in sentences ]

        parsresp( sentences )
        calls = self.parsnt_mock.mock_calls
        self.assertEqual( calls, expected_calls )



class ApiSentenceParsing(unittest.TestCase):


    def setUp(self):
        conv_patcher = patch('librouteros.datastructures.convattrwrd')
        self.conv_mock = conv_patcher.start()
        self.conv_mock.return_value = (1,2)
        self.addCleanup(conv_patcher.stop)


    def test_calls_tuple_creation_method(self):
        call_snt = ( '=disabled=false', '=interface=ether1' )

        parsnt( call_snt )
        call_list = [ call(elem) for elem in call_snt ]
        self.assertEqual( call_list, self.conv_mock.mock_calls )


    def test_filters_out_non_attribute_words(self):
        call_snt = ( '=disabled=false', '=interface=ether1', 'no_attr_word' )

        parsnt( call_snt )
        call_list = [ call(elem) for elem in call_snt[:2] ]
        self.assertEqual( call_list, self.conv_mock.mock_calls )
