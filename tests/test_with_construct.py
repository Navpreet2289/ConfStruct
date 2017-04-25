# coding=utf8

from __future__ import unicode_literals

import sys
import struct
import unittest

from construct import Adapter, Byte, Short, Sequence

from conf_struct import ConfStruct, CField

PY36 = sys.version_info[:2] >= (3, 6)


class ServerAddressStruct:
    def parse(self, binary):
        ip0, ip1, ip2, ip3, port = struct.unpack('>4BH', binary)
        return '{0}.{1}.{2}.{3}:{4}'.format(ip0, ip1, ip2, ip3, port)

    def build(self, value):
        ip, port = value.split(':')
        ip_l = list(map(int, ip.split('.')))
        return struct.pack('>4BH', ip_l[0], ip_l[1], ip_l[2], ip_l[3], int(port))


class ServerAddressAdapter(Adapter):
    def _encode(self, obj, context):
        ip, port = obj.split(":")
        port = int(port)
        return list(map(int, ip.split("."))) + [port // 256, port % 256]

    def _decode(self, obj, context):
        return "{0}.{1}.{2}.{3}:{4}".format(obj[0], obj[1], obj[2], obj[3], obj[4] * 256 + obj[5])


class DemoConfigStruct(ConfStruct):
    # The structures of value in the following fields are equal.
    val1 = CField(code=0x01, constructor=Short)
    val2 = CField(code=0x02, fmt='>H')

    # The structures of value in the following fields are equal.
    ip1 = CField(code=0x03, constructor=ServerAddressAdapter(Byte[6]))
    ip2 = CField(code=0x04, constructor=ServerAddressStruct())

    pos1 = CField(code=0x05, constructor=Sequence(Byte, Byte))


class BaseTestCase(unittest.TestCase):
    def test_with_base_struct(self):
        ms = DemoConfigStruct()
        binary_data = ms.build(val1=258, val2=258)
        if PY36:
            self.assertEqual(b'\x01\x02\x01\x02\x02\x02\x01\x02', binary_data)
        else:
            self.assertIn(binary_data, {
                b'\x01\x02\x01\x02\x02\x02\x01\x02',
                b'\x02\x02\x01\x02\x01\x02\x01\x02'
            })

    def test_with_adapter(self):
        ms = DemoConfigStruct()

        self.assertEqual(b'\x03\x06\xc0\xa8\x01\xc8\x27\xd8', ms.build(ip1='192.168.1.200:10200'))
        self.assertEqual(b'\x04\x06\xc0\xa8\x01\xc8\x27\xd8', ms.build(ip2='192.168.1.200:10200'))

        self.assertDictEqual(
            {'val1': 258, 'ip2': '192.168.1.200:10200'},
            ms.parse(b'\x01\x02\x01\x02\x04\x06\xc0\xa8\x01\xc8\x27\xd8')
        )
        
    def test_with_sequence(self):
        ms = DemoConfigStruct()
        self.assertEqual(ms.build(pos1=[1,2]), b'\x05\x02\x01\x02')
        self.assertEqual({'pos1': [3, 4]},ms.parse(b'\x05\x02\x03\x04'))


if __name__ == '__main__':
    unittest.main()
