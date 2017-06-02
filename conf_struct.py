# coding=utf8

from __future__ import unicode_literals

import struct

import six

__all__ = ['DefineException', 'ParseException', 'BuildException', 'ConfStruct', 'CField', 'COptions']


class DefineException(Exception):
    pass


class ParseException(Exception):
    pass


class BuildException(Exception):
    pass


class StructConstruct(object):
    def __init__(self, fmt):
        self.struct = struct.Struct(format=fmt)

    def build(self, value):
        return self.struct.pack(value)

    def parse(self, binary):
        value, = self.struct.unpack(binary)
        return value


class CField(object):
    def __init__(self, code, label=None, fmt=None, constructor=None):
        self.code = code
        self.label = label

        if fmt:
            self.constructor = StructConstruct(fmt)
        else:
            self.constructor = constructor

    def build(self, value):
        if self.constructor:
            return self.constructor.build(value)

    def parse(self, binary):
        if self.constructor:
            return self.constructor.parse(binary)


class COptions(object):
    code_fmt = '>B'
    length_fmt = '>B'

    def __init__(self, **kwargs):
        self.code_fmt = struct.Struct(self.code_fmt)
        self.length_fmt = struct.Struct(self.length_fmt)

    @property
    def size(self):
        return self.code_fmt.size + self.length_fmt.size

    @property
    def code_offset(self):
        return 0

    @property
    def length_offset(self):
        return self.code_fmt.size

    def pack(self, code, length):
        return self.code_fmt.pack(code) + self.length_fmt.pack(length)

    def unpack_code(self, buffer, offset):
        code, = self.code_fmt.unpack_from(buffer, offset)
        return code

    def unpack_length(self, buffer, offset):
        length, = self.length_fmt.unpack_from(buffer, offset)
        return length


class ConfStructMeta(type):
    def __new__(cls, name, bases, attrs):
        code_lookup = {}
        name_lookup = {}
        for name, field in six.iteritems(attrs):
            if isinstance(field, CField):
                if field.code in code_lookup:
                    raise DefineException('Duplicate code {} for {}'.format(field.code, name))
                field.name = name
                code_lookup[field.code] = field
                name_lookup[name] = field
        attrs['code_lookup'] = code_lookup
        attrs['name_lookup'] = name_lookup
        opts_cls = attrs.pop('Options', COptions)
        attrs['_opts'] = opts_cls()

        return type.__new__(cls, name, bases, attrs)


class ConfStruct(six.with_metaclass(ConfStructMeta)):
    @property
    def opts(self):
        return self._opts

    def parse(self, binary):
        values = {}
        index = 0
        total = len(binary) - self.opts.size
        while index <= total:
            code = self.opts.unpack_code(binary, offset=index)
            length = self.opts.unpack_length(binary, offset=index + self.opts.length_offset)
            value_binary = binary[index + self.opts.size:index + self.opts.size + length]
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
            index += length + self.opts.size
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
                binary += self.opts.pack(field.code, len(value_binary)) + value_binary
        return binary
