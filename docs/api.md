

[TOC]

# API (Beta)

This document contains all API reference for *Constructor* / *Field* / *Structure*.

- *Constructor* : A basic unit of builder/parser between python objects and binary data.
- *Field*:A wrapper of *Constructor*.
- *Structure*: A structure for a specified solution like "length-body".

*Constructor* and *Field*  implement the interface `ConstructorMixin`:

```python
class ConstructorMixin(object):
    def build(self, value):
        raise NotImplementedError()

    def parse(self, binary):
        raise NotImplementedError()
```

But *Structure* has a lot difference.

```python
class ConstructorMixin(object):
    def build(self, **kwargs):
        raise NotImplementedError()

    def parse(self, binary):
        raise NotImplementedError()
```



## Constructor

*Constructor* is a builder/parser between python objects and binary data.All class has a short alias named like `CXxx`.

### StructureConstructor

`class StructureConstructor(format, encoding='utf8', **kwargs)`

A *abstract* constructor using `struct.Struct` to pack/unpack.

**StructureConstructor.format**

A format string describe the structure of binary data. See [Format String](https://docs.python.org/3/library/struct.html#format-strings) for more detail.

**StructureConstructor.encoding**

The encoding name used for encoding and decoding between string and bytes.Default is utf8.

### CSingle

`class CSingle(format, encoding='utf8', **kwargs)`

A constructor for number type (int/long/float), text type.

### CSequence

`class CSequence(format, encoding='utf8', **kwargs)` 

A constructor for tuple and list, every element must be a valid type in `CSingle`.Mixed type such as `format='>4BH'` is also supported.

### CDictionary

`class CDictionary(format, field_names, encoding='utf8', **kwargs)`

A constructor for dictionary, it is a subclass of `CSequence`.

**CDictionary.field_names**

A list or string contains keys to describe the order of these values.See `collections.namedtuple` for more detail.



## Field Options

This part contains all API references of `Field` including the fields options and field type.

### General field options

**code**

A *immutable* object representing the field type, this option is required for every field and must be unique.The `Field.code` can be a object as following *immutable type*.

- Integer type:`int` and `long`
- `tuple`

**label**

A human-reading string for the field.Default is None.

## Field Types

### StructField

`class StructField(code, format, encoding='utf8', label=None, **kwargs)`

A *abstract* class using `struct.Struct` as its constructor.You can not directly use this class.

**StructField.format**

A format string describe the structure of binary data.

**StructField.encoding**

The encoding name used for encoding and decoding between string and bytes.Default is utf8.

### SingleField

`class SingleField(code, format, encoding='utf8', label=None, **kwargs)`

A field using `CSingle` with its constructor.

### SequenceField

`class SingleField(code, format, encoding='utf8', label=None, **kwargs)`

A field using `CSequence` with its constructor.

### DictionaryField

`class DictionaryField(code, format, names, encoding='utf8', label=None, **kwargs)`

A field using `CDictionary` with its constructor.

### ConstructorField

A field using custom constructor.

`class ConstructorField(code, constructor=None, label=None, **kwargs)`

**ConstructorField.constructor**

A interface object Implement `ConstructorMixin`.

### ~~CField~~

*NOTE:This field is deprecated and will be removed in v1.0 .You should use more specific Fields such as the above subclass fields.*

## ConfStructure

### Structure Model

> NOTE:The old alias `ConfStruct` is deprecated and will be removed in v1.0 .

`ConfStructure` is a declarative class to describe the structure of a protocol.

### Options

`COptions` is a inner class of ConfStruct contains options affecting build/parse process.

**COptions.code_format**

A format string for code field.Default is `>B`.

**COptions.length_format**

A format string of length field.Default is `>B`.