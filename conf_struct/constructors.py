# coding=utf8

from __future__ import unicode_literals

import sys
import operator
import struct
from functools import reduce
from collections import namedtuple

import six

PY36 = sys.version_info[0:2] >= (3, 6)


# ----------Basic interface----------

class ConstructorMixin(object):
    def build(self, value):
        raise NotImplementedError()

    def parse(self, binary):
        raise NotImplementedError()


# --------- Composite Constructors----------
class CComposite(ConstructorMixin):
    def __init__(self, *args, **kwargs):
        field_names = kwargs.pop('field_names', None)
        if args and kwargs:
            raise TypeError('Can not both use args and kwargs')
        if args:
            field_names = ['field_{}'.format(i) for i, _ in enumerate(args)]
            self.constructors = self._build_fields(field_names, *args)
        else:
            if PY36:
                field_names = list(kwargs.keys())
                self.constructors = self._build_fields(field_names, **kwargs)
            elif not field_names:
                raise ValueError('You must set field_name in python3.6')

        self.size_list = list(map(operator.attrgetter('byte_size'), self.constructors))
        self.byte_size = sum(self.size_list)

    def _build_fields(self, field_names, *args, **kwargs):
        c = namedtuple('_Field', field_names)
        if args:
            return c(*args)
        else:
            return c(**kwargs)

    def build(self, value):
        data = [c.build(v) for c, v in zip(self.constructors, value)]
        s = b''.join(data)
        return s

    def parse(self, binary):
        binary_list = [0] * len(self.size_list)
        i = 0
        for j, s in enumerate(self.size_list):
            binary_list[j] = binary[i:i + s]
            i += s
        return tuple([c.parse(b) for c, b in zip(self.constructors, binary_list)])


class CListComposite(ConstructorMixin):
    def __init__(self, *constructors):
        self.constructors = constructors
        self.size_list = list(map(operator.attrgetter('byte_size'), constructors))
        self.byte_size = sum(self.size_list)

    def build(self, value):
        data = [c.build(v) for c, v in zip(self.constructors, value)]
        s = reduce(operator.add, data, b'')  # Note:Can not use sum due to integer
        return s

    def parse(self, binary):
        binary_list = [0] * len(self.size_list)
        i = 0
        for j, s in enumerate(self.size_list):
            binary_list[j] = binary[i:i + s]
            i += s
        return tuple([c.parse(b) for c, b in zip(self.constructors, binary_list)])


# ---------- Leaf Constructors----------

class StructureConstructorMixin(ConstructorMixin):
    def build(self, value):
        return self._build(value)

    def parse(self, binary):
        return self._parse(binary)

    def _build(self, value):
        pass

    def _parse(self, binary):
        pass

    # Public API
    def pre_build(self, value):
        return value

    def post_parse(self, value):
        return value


class StructureConstructor(StructureConstructorMixin):
    def __init__(self, format, encoding='utf8', **kwargs):
        self.struct = struct.Struct(format=format)
        self.byte_size = self.struct.size
        # self.multiple = _SINGLE_FORMAT_RE.match(format) is None
        self.encoding = encoding

    def _ensure_bytes(self, value):
        if isinstance(value, six.text_type):
            return value.encode(encoding=self.encoding)
        else:
            return value

    def _ensure_string(self, value):
        if isinstance(value, six.binary_type):
            return value.decode(encoding=self.encoding)
        else:
            return value


# ----------Basic Constructors----------

class CSingle(StructureConstructor):
    def _build(self, value):
        value = self.pre_build(value)
        value = self._ensure_bytes(value)
        return self.struct.pack(value)

    def _parse(self, binary):
        value, = self.struct.unpack(binary)
        value = self._ensure_string(value)
        value = self.post_parse(value)
        return value


class CSequence(StructureConstructor):
    def _build(self, value):
        value = self.pre_build(value)
        value = tuple(map(self._ensure_bytes, value))
        return self.struct.pack(*value)

    def _parse(self, binary):
        values = self.struct.unpack(binary)
        values = tuple(map(self._ensure_string, values))
        values = self.post_parse(values)
        return values


class CDictionary(CSequence):
    def __init__(self, format, field_names, encoding='utf8', **kwargs):
        super(CDictionary, self).__init__(format=format, encoding=encoding, **kwargs)
        self.field_names = field_names
        self._list2dict_class = namedtuple('List2Dict', field_names=field_names)

    def _build(self, value):
        value = self.pre_build(value)
        data_list = self._list2dict_class(**value)
        value = tuple(map(self._ensure_bytes, data_list))
        return self.struct.pack(*value)

    def _parse(self, binary):
        values = self.struct.unpack(binary)
        values = tuple(map(self._ensure_string, values))
        nd = self._list2dict_class(*values)
        values = self.post_parse(nd._asdict())
        return values


# ----------Common Constructors ----------

class CString(CSingle):
    def __init__(self, byte_length, encoding='utf8', **kwargs):
        format = '>{}s'.format(byte_length)
        super(CString, self).__init__(format=format, encoding=encoding, **kwargs)


# Short Alias

SingleConstructor = CSingle
SequenceConstructor = CSequence
DictionaryConstructor = CDictionary
