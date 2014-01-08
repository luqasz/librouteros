#!/usr/bin/python3

import unittest

if __name__ == "__main__":
    all_tests = unittest.TestLoader().discover('unit_tests', pattern='*.py')
    unittest.TextTestRunner(verbosity=3).run(all_tests)
