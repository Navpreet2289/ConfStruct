# coding=utf8

from __future__ import unicode_literals

import sys
import struct
import unittest

from conf_struct import ConfStruct, CField, DefineException, DefineException

PY36 = sys.version_info[:2] >= (3, 6)


class ServerAddressStruct:
    def parse(self, binary):
        ip0, ip1, ip2, ip3, port = struct.unpack('>4BH', binary)
        return '{0}.{1}.{2}.{3}:{4}'.format(ip0, ip1, ip2, ip3, port)

    def build(self, value):
        ip, port = value.split(':')
        ip_l = list(map(int, ip.split('.')))
        return struct.pack('>4BH', ip_l[0], ip_l[1], ip_l[2], ip_l[3], int(port))


class DeviceConfStruct(ConfStruct):
    delayed_restart = CField(code=0x01, fmt='>H')
    server_address = CField(code=0x02, constructor=ServerAddressStruct())
    awaken_period = CField(code=0x03, fmt='>I')


class ConfDefineTestCase(unittest.TestCase):
    def test_duplicate_code(self):
        with self.assertRaises(DefineException):
            class DuplicateCodeConf(ConfStruct):
                name1 = CField(code=0x01, fmt='>H')
                name2 = CField(code=0x01, fmt='>B')


class ConfTestCase(unittest.TestCase):
    def test_base(self):
        dcs = DeviceConfStruct()

        binary_data = dcs.build(delayed_restart=180, awaken_period=3600)
        if PY36:
            self.assertEqual(b'\x01\x02\x00\xb4\x03\x04\x00\x00\x0e\x10', binary_data)
        else:
            self.assertIn(binary_data, {
                b'\x01\x02\x00\xb4\x03\x04\x00\x00\x0e\x10',
                b'\x03\x04\x00\x00\x0e\x10\x01\x02\x00\xb4'
            })

        test_binary = b'\x01\x02\x00\xB4\x03\x04\x00\x00\x0e\x10'
        data = dcs.parse(test_binary)
        self.assertDictEqual({'delayed_restart': 180, 'awaken_period': 3600}, data)

        test_binary2 = b'\x03\x04\x00\x00\x0e\x10\x01\x02\x00\xb4'
        data2 = dcs.parse(test_binary2)
        self.assertDictEqual({'delayed_restart': 180, 'awaken_period': 3600}, data2)

    def test_custom_constructor(self):
        dcs = DeviceConfStruct()

        binary_data = dcs.build(server_address='192.168.1.200:10200')
        self.assertEqual(
            b'\x02\x06\xc0\xa8\x01\xc8\x27\xd8',
            binary_data
        )

        test_binary = b'\x02\x06\xc0\xa8\x01\xc8\x27\xd8'
        data = dcs.parse(test_binary)
        self.assertDictEqual({'server_address': '192.168.1.200:10200'}, data)

    def test_mixed(self):
        dcs = DeviceConfStruct()

        # Build test
        binary_data = dcs.build(delayed_restart=180, awaken_period=3600, server_address='192.168.1.200:10200')
        if PY36:
            self.assertEqual(b'\x01\x02\x00\xb4\x03\x04\x00\x00\x0e\x10\x02\x06\xc0\xa8\x01\xc8\x27\xd8', binary_data)
        else:
            self.assertIn(binary_data, {
                b'\x01\x02\x00\xb4\x02\x06\xc0\xa8\x01\xc8\x27\xd8\x03\x04\x00\x00\x0e\x10',
                b'\x01\x02\x00\xb4\x03\x04\x00\x00\x0e\x10\x02\x06\xc0\xa8\x01\xc8\x27\xd8',
                b'\x02\x06\xc0\xa8\x01\xc8\x27\xd8\x01\x02\x00\xb4\x03\x04\x00\x00\x0e\x10',
                b'\x02\x06\xc0\xa8\x01\xc8\x27\xd8\x03\x04\x00\x00\x0e\x10\x01\x02\x00\xb4',
                b'\x03\x04\x00\x00\x0e\x10\x01\x02\x00\xb4\x02\x06\xc0\xa8\x01\xc8\x27\xd8',
                b'\x03\x04\x00\x00\x0e\x10\x02\x06\xc0\xa8\x01\xc8\x27\xd8\x01\x02\x00\xb4'
            })

        # Parse test
        test_binary = b'\x02\x06\xc0\xa8\x01\xc8\x27\xd8\x03\x04\x00\x00\x0e\x10\x01\x02\x00\xb4'
        data = dcs.parse(test_binary)
        self.assertDictEqual({
            'server_address': '192.168.1.200:10200',
            'delayed_restart': 180,
            'awaken_period': 3600
        }, data)


if __name__ == '__main__':
    unittest.main()
