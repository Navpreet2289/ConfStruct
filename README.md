# ConfStruct

![travis](https://travis-ci.org/kinegratii/ConfStruct.svg?branch=master)
[![PyPI version](https://badge.fury.io/py/ConfStruct.svg)](https://badge.fury.io/py/ConfStruct)

## Overview

### What can this project solve  ?

ConfStruct is a builder and parser between python dictionary and  "length-body" binary data.

When you send some configure values to a RTU device.You may not send all values in a time,
so these configure values in bytes stream is not in a fixed position.The probably structure may be described as the following table:

| Field       | PC1  | VL1  | V1   | PC2  | VL2  | V 2  | ...  | PC   | VL n | V n  |
| ----------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Byte Length | 1    | 1    | 2    | 1    | 1    | 4    | -    | 1    | 1    | 4    |
| Value       | 0x01 | 0x02 | -    | 0x02 | 0x04 | -    | -    | 0x0A | 0x04 | -    |

Note: PC = param code, VL = value length, V = value

For example, the following table is configure parameters supported for a GPRS RTU device.

| Field Name     | Code | Data Length In Bytes | Data type                | Description                     |
| -------------- | ---- | -------------------- | ------------------------ | ------------------------------- |
| Delay Restart  | 1    | 4                    | Unsigned 32-bit interger | Delay seconds to restart device |
| Server Address | 2    | 6                    | 4-byte IP + 2-byte port  | Server address to connect       |
| Awaken Period  | 3    | 2                    | Unsigned 16-bit interger | The interval of reporting data  |

The demo data `b'\x02\x06\xc0\xa8\x01\xc8\x27\xd8\x01\x02\x00\xb4'` sent by device can be split into several parts.every part is explained as the following table.

| Offset | Data                     | Description                              |
| ------ | ------------------------ | ---------------------------------------- |
| 0      | \x02                     | "Server Address" Field                   |
| 1      | \x06                     | The after 6 bytes (2-7) store real value |
| 2-7    | \xc0\xa8\x01\xc8\x27\xd8 | Parse to IP and  port                    |
| 8      | \x01                     | "Delay Restart" Field                    |
| 9      | \x02                     | The after 2 bytes(10-11) store real value |
| 10-11  | \x00\xb4                 | parse into a unsigned 32-bit interger : 180 |

So the data can be parsed to the `{server_address='192.168.1.200:10200', delayed_restart=180}` .

### How to solve using code

Use `ConfStruct` to describe the device config protocol.

```python
from conf_struct import ConfStruct, CField

class ServerAddressStruct:
    def parse(self, binary):
        ip0, ip1, ip2, ip3, port = struct.unpack('>4BH', binary)
        return '{0}.{1}.{2}.{3}:{4}'.format(ip0, ip1, ip2, ip3, port)

    def build(self, value):
        ip, port = value.split(':')
        ip_l = list(map(int, ip.split('.')))
        return struct.pack('>4BH', ip_l[0], ip_l[1], ip_l[2], ip_l[3], int(port))

class DeviceConfigStruct(ConfStruct):
    delayed_restart = CField(code=0x01, fmt='>H')
    server_address = CField(code=0x02, constructor=ServerAddressStruct())
    awaken_period = CField(code=0x03, fmt='>I')
```

Send config value to with `{server_address='192.168.1.200:10200', delayed_restart=180}` .

```
>>>  dcs = DeviceConfigStruct()
>>> dcs.build(server_address='192.168.1.200:10200', delayed_restart=180)
b'\x02\x06\xc0\xa8\x01\xc8\x27\xd8\x01\x02\x00\xb4'
>>> dcs.parse(b'\x03\x04\x00\x00\x0e\x10\x02\x06\xc0\xa8\x01\xc8\x27\xd8')
{'server_address':'192.168.1.200:10200', 'awaken_period': 3600}
```

## API - Field

This part contains all API references of `Field` including the fields options and field type.

### General field options

**code**

A *immutable* object representing the field type, this option is required for every field and must be unique.The `Field.code` can be a object as following *immutable type*.

- Integer type:`int` and `long`
- `tuple`

**label**

A human-reading string for the field.Default is None.

### Field types

#### StructField

`class StructField(code, fmt, encoding='utf8', label=None, **kwargs)`

A *abstract* class using `struct.Struct` as its constructor.You can not directly use this class.

**StructField.fmt**

A format string describe structures binary data.

**StructField.encoding**

The encoding name used for encoding and decoding between string and bytes.Default is utf8.

#### SingleField

`class SingleField(code, fmt, encoding='utf8', label=None, **kwargs)`

A field for a single value. All options are the same as `StructField`.

#### SequenceField

`class SingleField(code, fmt, encoding='utf8', label=None, **kwargs)`

A field for tuple.All options are the same as `StructField`.

The `SequenceField.build(value)` must be an iterable. And its `parse` method returns a tuple.

#### DictField

`class DictField(code, fmt, names, encoding='utf8', label=None, **kwargs)`

A field for a dictionary.

The `build` requires a dictionary parameter and the `parse` method returns a dict.

**DictField.names**

The key list for converting between `list` and `dict`.

#### ConstructorField

A field using custom constructor.

`class ConstructorField(code, constructor=None, label=None, **kwargs)`

**ConstructorField.constructor**

A interface object Implement `build` and `parse` method. 

```python
class Constructor(object):
    def buid(self, value):
        # return binary data
        pass
    def parse(self, binary):
        # return unpack result
        pass
```

[Construct](http://construct.readthedocs.io/en/latest/)  is a powerful declarative parser (and builder) for binary data.There are some classes Implement ing the same methods in the above way.These classes include:

- Byte,Short,Int etc.
- Struct
- Sequence
- Adapter

The above-mentioned demo code fragment can also rewrite with *Construct* library. 

```python
from construct import Struct, Adapter, Byte, Short, Int
from conf_struct import ConfStruct, CField

class ServerAddressAdapter(Adapter):
    def _encode(self, obj, context):
        ip, port = obj.split(":")
        port = int(port)
        return list(map(int, ip.split("."))) + [port // 256, port % 256]

    def _decode(self, obj, context):
        return "{0}.{1}.{2}.{3}:{4}".format(obj[0], obj[1], obj[2], obj[3], obj[4] * 256 + obj[5])


class DeviceConfigStruct(ConfStruct):
    delayed_restart = CField(code=0x01, constructor=Short)
    server_address = CField(code=0x02, constructor=ServerAddressAdapter(Byte[6]))
    awaken_period = CField(code=0x03, constructor=Int)
```

#### CField

This field is deprecated and will be removed in v1.0.0 .

## API - ConfStruct options

`COptions` is a inner class of ConfStruct contains options affecting build/parse process.

**COptions.code_fmt**

A format string for code field.Default is `>B`.

**COptions.length_fmt**

A format string of length field.Default is `>B`.

## Compatibility

The package has been tested in 2.7, 3.4, 3.5, 3.6 .

NOTE

- The result of `build` is not unique due to unordered dictionary below python3.6.

## LICENSE

This project is under MIT License.