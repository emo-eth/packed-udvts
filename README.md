# packed-udvts

This is a very experimental Python library for generating libaries for efficient bitpacking with [user-defined value types](https://docs.soliditylang.org/en/latest/types.html#user-defined-value-types) in Solidity.

# Member

A `Member` is the basic unit of a `UserDefinedValueType`. Its simplified declaration is as follows:

```python
dataclass
class Member:
    # snake-case name of this member; will be converted to title case for the getter and setter
    # and upper-cased for constants
    name: str
    # width of this member in bits
    width_bits: int
    # if a bytesN type, the number of bytes
    bytesN: Optional[int] = None
    # if not bytesN, signed or unsigned
    signed: bool = False
    # if a member is itself a UDVT, this is the name of the UDVT
    custom_typestr: Optional[UserDefinedTypeName] = None
    # if a member should be multiplied by a power of two, this is the power of two
    expansion_bits: Optional[int] = None
```

# Region

A region is a wrapper around a `Member` object, which additionally stores an `offset` (from the left) within the `UserDefinedValueType`. Using this offset, it is responsible for generating relevant constants and functions for packing and unpacking the member.

# UserDefinedValueType

A `UserDefinedValueType` is the top-level abstraction, and includes helper functions such as the static `UserDefinedValueType.from_members(members: list[Member], name: str)` method, which can be used to generate a `UserDefinedValueType` from a list of `Member` objects (by first converting them into `Region` objects).

It also includes the method `render_file(typesafe:bool=True)` which is used to generate a Solidity file containing the generated library.

# TestGen

The `TestGen` class takes a `UserDefinedValueType` and generates a Solidity file containing tests for the generated library. It is used to ensure that the generated library is correct.
