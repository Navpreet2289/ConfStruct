# Guide

## Advance Topics

### Custom Code Options

`COptions` contains options for build and parse for binary structures.

###  Integrate with construct library

[Construct](http://construct.readthedocs.io/en/latest/)  is a powerful declarative parser (and builder) for binary data.There are some classes Implement ing the same methods in the above way.These classes include:

- Byte,Short,Int etc.
- Struct
- Sequence
- Adapter

The above-mentioned demo code fragment can also rewrite with *Construct* library. 

```python
from construct import Struct, Adapter, Byte, Short, Int
from conf_struct import ConfStruct, ConstructorField

class ServerAddressAdapter(Adapter):
    def _encode(self, obj, context):
        ip, port = obj.split(":")
        port = int(port)
        return list(map(int, ip.split("."))) + [port // 256, port % 256]

    def _decode(self, obj, context):
        return "{0}.{1}.{2}.{3}:{4}".format(obj[0], obj[1], obj[2], obj[3], obj[4] * 256 + obj[5])


class DeviceConfigStruct(ConfStruct):
    delayed_restart = ConstructorField(code=0x01, constructor=Short)
    server_address = ConstructorField(code=0x02, constructor=ServerAddressAdapter(Byte[6]))
    awaken_period = ConstructorField(code=0x03, constructor=Int)
```