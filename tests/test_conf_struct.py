# coding=utf8

from __future__ import unicode_literals

import sys
import struct
import unittest

from conf_struct import ConfStruct, DefineException, COptions, SequenceField, SingleField, DictionaryField, \
    ConstructorField

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
    delayed_restart = SingleField(code=0x01, format='>H')
    server_address = ConstructorField(code=0x02, constructor=ServerAddressStruct())
    awaken_period = SingleField(code=0x03, format='>I')


class ConfDefineTestCase(unittest.TestCase):
    def test_duplicate_code(self):
        with self.assertRaises(DefineException):
            class DuplicateCodeConf(ConfStruct):
                name1 = SingleField(code=0x01, format='>H')
                name2 = SingleField(code=0x01, format='>B')


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
        result = {
            b'\x01\x02\x00\xb4\x02\x06\xc0\xa8\x01\xc8\x27\xd8\x03\x04\x00\x00\x0e\x10',
            b'\x01\x02\x00\xb4\x03\x04\x00\x00\x0e\x10\x02\x06\xc0\xa8\x01\xc8\x27\xd8',
            b'\x02\x06\xc0\xa8\x01\xc8\x27\xd8\x01\x02\x00\xb4\x03\x04\x00\x00\x0e\x10',
            b'\x02\x06\xc0\xa8\x01\xc8\x27\xd8\x03\x04\x00\x00\x0e\x10\x01\x02\x00\xb4',
            b'\x03\x04\x00\x00\x0e\x10\x01\x02\x00\xb4\x02\x06\xc0\xa8\x01\xc8\x27\xd8',
            b'\x03\x04\x00\x00\x0e\x10\x02\x06\xc0\xa8\x01\xc8\x27\xd8\x01\x02\x00\xb4'
        }
        if PY36:
            self.assertEqual(b'\x01\x02\x00\xb4\x03\x04\x00\x00\x0e\x10\x02\x06\xc0\xa8\x01\xc8\x27\xd8', binary_data)
        else:
            self.assertIn(binary_data, result)

        for test_binary in result:
            data = dcs.parse(test_binary)
            self.assertDictEqual({
                'server_address': '192.168.1.200:10200',
                'delayed_restart': 180,
                'awaken_period': 3600
            }, data)


# -----------Custom Options Test Cases--------------------

class MetaOptionStruct(ConfStruct):
    a1 = SingleField(code=0x00, format='>H')
    a2 = SingleField(code=0x01, format='>I')

    class Options(COptions):
        code_format = '>H'
        length_format = '>H'


class MetaOptionTestCase(unittest.TestCase):
    def test_parse_build(self):
        mos = MetaOptionStruct()
        self.assertEqual(b'\x00\x00\x00\x02\x00\x01', mos.build(a1=1))
        self.assertDictEqual({'a1': 4}, mos.parse(b'\x00\x00\x00\x02\x00\x04'))


# --------------- String and multiple element features------------------------------------

class AdvanceConfStruct(ConfStruct):
    c1 = SingleField(code=1, format='4s')
    c2 = SingleField(code=2, format='4s')
    c3 = SequenceField(code=3, format='>BB')
    c4 = SequenceField(code=4, format='>BB')
    c5 = DictionaryField(code=5, format='>BB', field_names=['x', 'y'])


class BTestCase(unittest.TestCase):
    def test_fields(self):
        acs = AdvanceConfStruct()
        self.assertEqual({'c1': 'bbbb'}, acs.parse(b'\x01\x04bbbb'))
        self.assertEqual(b'\x02\x04abcd', acs.build(c2='abcd'))
        self.assertEqual(b'\x03\x02\x02\x03', acs.build(c3=(2, 3)))
        self.assertEqual({'c2': 'bbbb'}, acs.parse(b'\x02\x04bbbb'))
        self.assertEqual(b'\x04\x02\x02\x03', acs.build(c4=(2, 3)))
        self.assertEqual(b'\x05\x02\x01\x02', acs.build(c5={'x': 1, 'y': 2}))
        self.assertEqual({'c5': {'x': 2, 'y': 4}}, acs.parse(b'\x05\x02\02\x04'))


if __name__ == '__main__':
    unittest.main()
