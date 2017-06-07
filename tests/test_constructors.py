# coding=utf8

from __future__ import unicode_literals

import unittest

from conf_struct.constructors import CSingle, CSequence, CDictionary, CString, CListComposite, CComposite


class ConstructorTestCase(unittest.TestCase):
    def test_SingleConstructor(self):
        sc = CSingle(format='>B')
        self.assertEqual(b'\x23', sc.build(35))
        self.assertEqual(21, sc.parse(b'\x15'))

    def test_SequenceConstructor(self):
        sc1 = CSequence(format='>HH')
        self.assertEqual(b'\x00\x01\x00\x01', sc1.build((1, 1)))
        self.assertTupleEqual((1, 2), sc1.parse(b'\x00\x01\x00\x02'))

        # Mixed type
        sc2 = CSequence(format='>B3s')
        self.assertEqual(b'\x09123', sc2.build((9, '123')))
        self.assertEqual((9, '123'), sc2.parse(b'\x09123'))

    def test_DictionaryConstructor(self):
        dc = CDictionary(format='>HH', field_names='x y')
        self.assertEqual(b'\x00\x01\x00\x01', dc.build({'x': 1, 'y': 1}))
        self.assertDictEqual({'x': 1, 'y': 2}, dc.parse(b'\x00\x01\x00\x02'))

    def test_CString(self):
        cs = CString(byte_length=5)
        self.assertEqual(b'12345', cs.build('12345'))
        self.assertEqual('09872', cs.parse(b'09872'))

    def test_CListComposite(self):
        clc = CListComposite(CSingle(format='>B'), CSequence(format='>BB'))
        self.assertEqual(b'\x01\x02\x03', clc.build([1, (2, 3)]))
        self.assertTupleEqual((1, (2, 3)), clc.parse(b'\x01\x02\x03'))

    def test_CComposite(self):
        cc = CComposite(CSingle(format='>B'), CSequence(format='>BB'))
        self.assertEqual(b'\x01\x02\x03', cc.build([1, (2, 3)]))
        self.assertTupleEqual((1, (2, 3)), cc.parse(b'\x01\x02\x03'))
