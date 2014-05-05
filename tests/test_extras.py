# -*- coding: UTF-8 -*-

import unittest
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from librouteros.extras import dictdiff, strdiff

class DiffComputations(unittest.TestCase):

    def test_diffs_dictionaries_returning_only_desired_items(self):
        wanted = {'name':'public', 'write':True, 'integer':1}
        present = {'name':'public', 'write':False, 'integer':1}
        retval = dictdiff( wanted, present )
        desired = { 'write':True }
        self.assertEqual( retval, desired )

    @patch('librouteros.extras.strdiff')
    def test_calls_diffstr_when_plit_keys_are_specified(self, strdiff_mock):
        wanted = {'name':'public', 'write':'1,2,3', 'integer':1}
        present = {'name':'public', 'write':'3,4,5', 'integer':1}
        dictdiff( wanted, present, split_keys=('write', ), split_char=',' )
        strdiff_mock.assert_called_once_with( '1,2,3', '3,4,5', ',' )

    @patch('librouteros.extras.strdiff')
    def test_call_diffstr_when_split_key_absent_in_prsesnt(self, strdiff_mock):
        wanted = {'name':'public', 'write':'1,2,3', 'integer':1}
        present = {'name':'public', 'integer':1}
        dictdiff( wanted, present, split_keys=('write',), split_char=',' )
        strdiff_mock.assert_called_once_with( '1,2,3', '', ',' )

    def test_computes_difference_between_two_strings(self):
        retval = strdiff( '1,2,3', '1', ',' )
        desired = ','.join( {'3','2'} )
        self.assertEqual( retval, desired )
