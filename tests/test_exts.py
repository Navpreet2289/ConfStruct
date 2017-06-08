# coding=utf8

from __future__ import unicode_literals

import unittest

from conf_struct.exts import CIPv4, CIPv4Port


class ExtTestCase(unittest.TestCase):
    def test_basic(self):
        ci = CIPv4()
        self.assertEqual(b'\xc0\xa8\x01\xc8', ci.build('192.168.1.200'))
        self.assertEqual('192.168.1.200', ci.parse(b'\xc0\xa8\x01\xc8'))

        cip = CIPv4Port()
        self.assertEqual(b'\xc0\xa8\x01\xc8\x27\xd8', cip.build('192.168.1.200:10200'))
        self.assertEqual('192.168.1.200:10200', cip.parse(b'\xc0\xa8\x01\xc8\x27\xd8'))
