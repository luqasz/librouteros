#-*- coding: UTF-8 -*-

import unittest
from mock import MagicMock, patch

from logging import Logger, NullHandler
import librouteros as lr
from librouteros.exc import LibError

class NullLoggerTests(unittest.TestCase):

    def setUp(self):
        self.nl = lr._mkNullLogger()

    def test_creates_logger_instance(self):
        self.assertIsInstance( self.nl, Logger )

    def test_has_only_1_handler(self):
        self.assertEqual( len( self.nl.handlers ), 1 )

    def test_has_null_handler(self):
        self.assertIsInstance( self.nl.handlers[0], NullHandler )


class InitLoginTests(unittest.TestCase):


    def setUp(self):
        self.drv = MagicMock()


    def test_init_login_procedure(self):
        lr._initLogin( self.drv )
        self.drv.writeSnt.assert_called_once_with( '/login', () )
        self.drv.readDone.assert_called_once()


class LoginTests(unittest.TestCase):


    def setUp(self):
        self.drv = MagicMock()


    @patch('librouteros.trapCheck')
    def test_login_procedure(self, trap_mock):
        self.drv.readDone.return_value = 'string'
        lr._login( self.drv, 'username', 'pw' )
        self.drv.writeSnt.assert_called_once_with( '/login', ('=name=username', '=response=pw') )
        self.drv.readDone.assrt_called_once()
        trap_mock.assert_called_once_with('string')
