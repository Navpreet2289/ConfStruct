# coding=utf8

from __future__ import unicode_literals

import struct
from collections import namedtuple

import six


class ConstructorMixin(object):
    def build(self, value):
        raise NotImplementedError()

    def parse(self, binary):
        raise NotImplementedError()


class StructureConstructorMixin(ConstructorMixin):
    def build(self, value):
        return self._build(self._encode(value))

    def parse(self, binary):
        return self._decode(self._parse(binary))

    def _build(self, value):
        pass

    def _parse(self, binary):
        pass

    def _encode(self, value):
        return value

    def _decode(self, value):
        return value


class StructureConstructor(StructureConstructorMixin):
    def __init__(self, format, encoding='utf8', **kwargs):
        self.struct = struct.Struct(format=format)
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


class SingleConstructor(StructureConstructor):
    def _build(self, value):
        return self.struct.pack(value)

    def _parse(self, binary):
        value, = self.struct.unpack(binary)
        return value

    def _encode(self, value):
        return self._ensure_bytes(value)

    def _decode(self, value):
        return self._ensure_string(value)


class SequenceConstructor(StructureConstructor):
    def _build(self, value):
        return self.struct.pack(*value)

    def _parse(self, binary):
        values = self.struct.unpack(binary)
        return values

    def _encode(self, value):
        return tuple(map(self._ensure_bytes, value))

    def _decode(self, value):
        return tuple(map(self._ensure_string, value))


class DictionaryConstructor(SequenceConstructor):
    def __init__(self, format, field_names, encoding='utf8', **kwargs):
        super(DictionaryConstructor, self).__init__(format=format, encoding=encoding, **kwargs)
        self.field_names = field_names
        self._list2dict_class = namedtuple('List2Dict', field_names=field_names)

    def _encode(self, value):
        data_list = self._list2dict_class(**value)
        return super(DictionaryConstructor, self)._encode(data_list)

    def _decode(self, value):
        data_list = super(DictionaryConstructor, self)._decode(value)
        nd = self._list2dict_class(*data_list)
        return nd._asdict()
