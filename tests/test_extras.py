# -*- coding: UTF-8 -*-

import unittest

from librouteros.extras import dictdiff, diffstr

class DiffComputations(unittest.TestCase):

    def test_diffs_dictionaries_returning_only_desired_items(self):
        wanted = {'name':'public', 'write':True, 'integer':1}
        present = {'name':'public', 'write':False, 'integer':1}
        retval = dictdiff( wanted, present )
        desired = { 'write':True }
        self.assertEqual( retval, desired )

    def test_diffs_dictionaries_with_iterable_strings_inside(self):
        wanted = {'name':'public', 'write':'1,2,3', 'integer':1}
        present = {'name':'public', 'write':'3,4,5', 'integer':1}
        retval = dictdiff( wanted, present, split_keys=('write', ), split_char=',' )
        desired = { 'write':'1,2' }
        self.assertEqual( retval, desired )

    def test_diffs_dictionaries_with_iterable_strings_not_listed_in_present_dict(self):
        wanted = {'name':'public', 'write':'1,2,3', 'integer':1}
        present = {'name':'public', 'integer':1}
        retval = dictdiff( wanted, present, split_keys=('write',), split_char=',' )
        desired = { 'write':'1,3,2' }
        self.assertEqual( retval, desired )

    def test_computes_difference_between_two_strings(self):
        e1 = '1,2,3'
        e2 = '1'
        retval = diffstr( e1, e2, ',' )
        self.assertEqual( retval, '3,2' )
