# coding=utf8

from __future__ import unicode_literals

import warnings

from .constructors import SingleConstructor, SequenceConstructor, DictionaryConstructor


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
    constructor_class = DictionaryConstructor

    def __init__(self, code, format, field_names, encoding='utf8', label=None, **kwargs):
        kwargs['field_names'] = field_names
        super(DictionaryField, self).__init__(code, format=format, encoding=encoding, label=label, **kwargs)


class ConstructorField(CFieldBase):
    def __init__(self, code, constructor=None, label=None, **kwargs):
        super(ConstructorField, self).__init__(code, constructor, label, **kwargs)
