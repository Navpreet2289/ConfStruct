# coding=utf8

from __future__ import unicode_literals

import struct

import six

__all__ = ['DefineException', 'ParseException', 'BuildException', 'CField', 'ConfStruct']


class DefineException(Exception):
    pass


class ParseException(Exception):
    pass


class BuildException(Exception):
    pass


class CField(object):
    def __init__(self, code, label=None, fmt=None, constructor=None):
        self.code = code
        self.label = label

        if fmt:
            self.struct = struct.Struct(format=fmt)
        else:
            self.struct = None
        self.constructor = constructor

    def build(self, value):
        return self._build(value)

    def parse(self, binary):
        return self._parse(binary)

    def _build(self, value):
        if self.struct:
            return self.struct.pack(value)
        elif self.constructor:
            return self.constructor.build(value)
        else:
            return None

    def _parse(self, binary):
        if self.struct:
            value, = self.struct.unpack(binary)
            return value
        elif self.constructor:
            return self.constructor.parse(binary)
        else:
            return None


class ConfStructMeta(type):
    def __new__(cls, name, bases, attrs):
        code_lookup = {}
        name_lookup = {}
        for name, field in six.iteritems(attrs):
            if isinstance(field, CField):
                if field.code in code_lookup:
                    raise DefineException('Duplicate code {} for {} in {}'.format(field.code, name, cls.__name__))
                field.name = name
                code_lookup[field.code] = field
                name_lookup[name] = field
        attrs['code_lookup'] = code_lookup
        attrs['name_lookup'] = name_lookup
        return type.__new__(cls, name, bases, attrs)


class ConfStruct(six.with_metaclass(ConfStructMeta)):
    def parse(self, binary):
        values = {}
        index = 0
        total = len(binary) - 2
        while index <= total:
            code, length = struct.unpack('>BB', binary[index:index + 2])
            value_binary = binary[index + 2:index + 2 + length]
            if len(value_binary) == length:
                field = self.code_lookup.get(code)
                if field:
                    value = field.parse(value_binary)
                    if value is None:
                        func = getattr(self, 'parse_{}'.format(field.name), None)
                        if func:
                            value = func(value_binary)
                    if value:
                        values[field.name] = value
                else:
                    raise ParseException('Invalid code {}'.format(code))
            else:
                raise ParseException('No enough binary, expect {} but {}'.format(length, len(value_binary)))
            index += length + 2
        return values

    def build(self, **kwargs):
        binary = b''
        for name, value in kwargs.items():
            value_binary = None
            field = self.name_lookup.get(name)
            if field:
                value_binary = field.build(value)
                if value_binary is None:
                    func = getattr(self, 'build_' + field.name, None)
                    if func:
                        value_binary = func(value)
            if value_binary:
                binary += struct.pack('>BB', field.code, len(value_binary)) + value_binary
        return binary
