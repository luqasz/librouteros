# -*- coding: UTF-8 -*-

import unittest
from mock import MagicMock, patch

from librouteros.api import Api
from librouteros.drivers import SocketDriver

class TalkMethd(unittest.TestCase):


    def setUp(self):
        parsresp_patcher = patch('librouteros.api.parsresp')
        mksnt_patcher = patch('librouteros.api.mksnt')
        trapCheck_patcher = patch('librouteros.api.trapCheck')

        self.parsresp_mock = parsresp_patcher.start()
        self.mksnt_mock = mksnt_patcher.start()
        self.trapCheck_mock = trapCheck_patcher.start()

        self.addCleanup(parsresp_patcher.stop)
        self.addCleanup(mksnt_patcher.stop)
        self.addCleanup(trapCheck_patcher.stop)

        drv = MagicMock( spec = SocketDriver )
        self.api = Api( drv )


    def test_calls_mksnt(self):
        lvl = '/ip/address'
        self.api.talk( lvl )
        self.mksnt_mock.assert_called_once_with( {} )


    def test_calls_writeSnt(self):
        lvl = '/ip/address'
        self.mksnt_mock.return_value = ()
        self.api.talk( lvl )
        self.api.drv.writeSnt.assert_called_once_with( lvl, () )


    def test_calls_readdone(self):
        lvl = '/ip/address'
        self.api.talk( lvl )
        self.api.drv.readDone.assert_called_once_with()


    def test_calls_trapCheck(self):
        lvl = '/ip/address'
        self.api.drv.readDone.return_value = '123'
        self.api.talk( lvl )
        self.trapCheck_mock.assert_called_once_with( '123' )


    def test_calls_parsresp(self):
        lvl = '/ip/address'
        self.api.drv.readDone.return_value = '123'
        self.api.talk( lvl )
        self.parsresp_mock.assert_called_once_with( '123' )
