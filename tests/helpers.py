#-*- coding: UTF-8 -*-

'''
module for unit testing functions
'''

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

def make_patches(inst, patches):
    '''
    Function to create patches in a given class instance.
    Make patches, start them, add cleanups

    patches
        iterable with 2 element tuples having:
            abbreviation of patched method. _mock will be appendted to abbreviated name.
            full path to patching element
    '''

    for name, element in patches:
        # create patch
        p = patch(element)
        # set attirbute
        setattr(inst, name + '_mock', p.start())
        # add cleanups
        inst.addCleanup(p.stop)
