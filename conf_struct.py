# coding=utf8

from __future__ import unicode_literals

import struct
import warnings

import six

__all__ = ['DefineException', 'ParseException', 'BuildException', 'ConfStruct', 'CField', 'COptions']


# ---------- Exceptions ----------

class DefineException(Exception):
    pass


class ParseException(Exception):
    pass


class BuildException(Exception):
    pass


# ---------- Constructors  ----------

class ConstructorBase(object):
    def __init__(self, format, encoding='utf8', **kwargs):
        self.struct = struct.Struct(format=format)
        self.encoding = encoding

    def build(self, value):
        pass

    def parse(self, binary):
        pass

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


class SingleConstructor(ConstructorBase):
    def build(self, value):
        return self.struct.pack(self._ensure_bytes(value))

    def parse(self, binary):
        value, = self.struct.unpack(binary)
        return self._ensure_string(value)


class SequenceConstructor(ConstructorBase):
    def build(self, value):
        value = list(map(self._ensure_bytes, value))
        return self.struct.pack(*value)

    def parse(self, binary):
        values = self.struct.unpack(binary)
        values = list(map(self._ensure_string, values))
        return values


class DictConstructor(ConstructorBase):
    def __init__(self, format, encoding='utf8', **kwargs):
        super(DictConstructor, self).__init__(format=format, encoding=encoding, **kwargs)
        self.names = kwargs.get('names')

    def build(self, value):
        value = [value.get(n) for n in self.names]
        value = list(map(self._ensure_bytes, value))
        return self.struct.pack(*value)

    def parse(self, binary):
        values = self.struct.unpack(binary)
        values = list(map(self._ensure_string, values))
        return dict(zip(self.names, values))


# ---------- Fields ----------
class CFieldBase(object):
    def __init__(self, code, constructor=None, label=None, **kwargs):
        self.code = code
        self.constructor = constructor
        self.label = label

    @property
    def has_constructor(self):
        return self.constructor is not None

    def build(self, value):
        if self.has_constructor:
            return self.constructor.build(value)

    def parse(self, binary):
        if self.has_constructor:
            return self.constructor.parse(binary)


class CField(CFieldBase):
    def __init__(self, code, constructor=None, label=None, format=None, encoding='utf8', multiple=False, **kwargs):
        warnings.warn('The class CField is deprecated and will be removed in v1.0.0', DeprecationWarning)
        format = format or kwargs.get('fmt')
        if format:
            if multiple:
                constructor = SequenceConstructor(format=format, encoding=encoding, **kwargs)
            else:
                constructor = SingleConstructor(format=format, encoding=encoding, **kwargs)
        super(CField, self).__init__(code, constructor, label, **kwargs)


class StructField(CFieldBase):
    constructor_class = None

    def __init__(self, code, format, encoding='utf8', label=None, **kwargs):
        constructor = self.constructor_class(format=format, encoding=encoding, **kwargs)
        super(StructField, self).__init__(code, constructor=constructor, label=label)


class SingleField(StructField):
    constructor_class = SingleConstructor


class SequenceField(StructField):
    constructor_class = SequenceConstructor


class DictionaryField(SequenceField):
    constructor_class = DictConstructor

    def __init__(self, code, format, names, encoding='utf8', label=None, **kwargs):
        kwargs['names'] = names
        super(DictionaryField, self).__init__(code, format=format, encoding=encoding, label=label, **kwargs)
        self.names = names


class ConstructorField(CFieldBase):
    def __init__(self, code, constructor=None, label=None, **kwargs):
        super(ConstructorField, self).__init__(code, constructor, label, **kwargs)


# ---------- Options ----------

class COptions(object):
    code_format = '>B'
    length_format = '>B'

    def __init__(self, **kwargs):
        self.code_format = struct.Struct(self.code_format)
        self.length_format = struct.Struct(self.length_format)

    @property
    def size(self):
        return self.code_format.size + self.length_format.size

    @property
    def code_offset(self):
        return 0

    @property
    def length_offset(self):
        return self.code_format.size

    def pack(self, code, length):
        return self.code_format.pack(code) + self.length_format.pack(length)

    def unpack_code(self, buffer, offset):
        code, = self.code_format.unpack_from(buffer, offset)
        return code

    def unpack_length(self, buffer, offset):
        length, = self.length_format.unpack_from(buffer, offset)
        return length


# ---------- ConfStruct ----------

class ConfStructMeta(type):
    def __new__(cls, name, bases, attrs):
        code_lookup = {}
        name_lookup = {}
        for name, field in six.iteritems(attrs):
            if isinstance(field, CFieldBase):
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
        if len(binary) != 0 and total <= 0:
            raise ParseException('No enough binary')
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
