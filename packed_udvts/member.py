# to suppor TYPE_CHECKING
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from packed_udvts.util import to_title_case
from math import ceil

if TYPE_CHECKING:
    from packed_udvts.udvt import UserDefinedValueType


@dataclass
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
    custom_typestr: Optional[str] = None
    # if a member should be multiplied by a power of two, this is the power of two
    expansion_bits: Optional[int] = None

    def __init__(
        self,
        name: str,
        width_bits: int,
        bytesN: Optional[int] = None,
        signed: bool = False,
        custom_typestr: Optional[str] = None,
        expansion_bits: Optional[int] = None,
    ):
        assert width_bits > 0, "width_bits must be positive"
        assert bytesN is None or bytesN > 0, "bytesN must be positive or None"
        if signed:
            assert bytesN is None, "signed members must not be bytesN types"
            assert (
                width_bits % 8 == 0
            ), "signed members must have a width divisible by 8 for compatibility with SIGNEXTEND"
        self.name = name
        self.width_bits = width_bits
        self.bytesN = bytesN
        self.signed = signed
        self.custom_typestr = custom_typestr
        if expansion_bits is not None:
            # TODO: signextend?
            assert expansion_bits >= 0, "expansion_bits must be non-negative"
            assert expansion_bits + width_bits <= 256, "expansion_bits too large"
        self.expansion_bits = expansion_bits

    @staticmethod
    def from_udvt(udvt: UserDefinedValueType, name: str) -> "Member":
        """Create a new member from a UDVT"""
        assert udvt.width_bits < 256, "Cannot create a member from a full-width UDVT"
        return Member(
            name=name,
            width_bits=udvt.width_bits,
            bytesN=None,  # never bytesN since only bytes32 is allowed which fails above assertion
            signed=False,  # this library only allows unsigned uints for UDVTs
            custom_typestr=udvt.name,
        )

    @property
    def title(self) -> str:
        """Get the title case name of this region"""
        return to_title_case(self.name)

    @property
    def shadowed_name(self) -> str:
        """Get the shadowed name of this region"""
        return f"_{self.name}"

    @property
    def safe_typestr(self) -> str:
        """Get the safe typestr of this region"""
        if self.bytesN is None:
            num_bytes = (self.width_bits + (self.expansion_bits or 0)) // 8
            recovered_bits = num_bytes * 8
            if recovered_bits == self.width_bits:
                num_bits = recovered_bits
            else:
                num_bits = (num_bytes + 1) * 8
            return f"{'' if self.signed else 'u'}int{num_bits}"
        return f"bytes{self.bytesN}"

    @property
    def ceil_bytes(self) -> int:
        """Get the number of whole bytes necessary to represent this member"""
        return ceil(self.width_bits / 8)

    @property
    def unsafe_typestr(self) -> str:
        """Get the typestr of this region"""
        if self.bytesN is None:
            return f"{'' if self.signed else 'u'}int256"
        return f"bytes32"

    @property
    def declaration(self) -> str:
        """Get the declaration of this member"""
        return f"{self.safe_typestr} {self.name}"

    @property
    def shadowed_declaration(self) -> str:
        """Get the shadowed declaration of this member"""
        return f"{self.safe_typestr} {self.shadowed_name}"

    @property
    def num_expansion_bits(self) -> Optional[int]:
        """Get the number of bits to expand this region by"""
        if self.bytesN:
            # eg: bytes4; width of 5:
            # 256 - 32 = 224
            return 256 - self.bytesN * 8
        return self.expansion_bits

    def typestr(self, typesafe: bool) -> str:
        """Get the typestr of this region"""
        if self.custom_typestr is not None:
            return self.custom_typestr
        if typesafe:
            return self.safe_typestr
        return self.unsafe_typestr

    def get_lower_bound(self) -> int:
        """Get the lower bound of this member"""
        if self.bytesN:
            raise ValueError("Cannot get lower bound of bytesN member")
        if not self.signed:
            return 0
        else:
            return -1 * (2 ** (self.width_bits - 1))

    def get_upper_bound(self) -> int:
        """Get the upper bound of this member"""
        if self.bytesN:
            raise ValueError("Cannot get upper bound of bytesN member")
        if not self.signed:
            return 2**self.width_bits - 1
        else:
            return 2 ** (self.width_bits - 1) - 1

    def get_truncated_bytesN_mask(self):
        """Get the mask to truncate bytesN members"""
        if self.bytesN is None:
            raise ValueError("Cannot get truncated bytesN mask of non-bytesN member")
        max_numeric_value = 2 ** (self.width_bits) - 1
        # shift upper_mask to the left by the number of expansion bits
        return max_numeric_value << self.num_expansion_bits

    def get_bounds(self, name: Optional[str] = None) -> str:
        if name is None:
            name = self.name
        if self.custom_typestr:
            raise ValueError("Cannot get bound string of UDVT")
        if self.bytesN is None:
            return f"{name} = {self.safe_typestr}(bound({name}, {hex(self.get_lower_bound())}, {hex(self.get_upper_bound())}));"
        return f"""
assembly {{
{name} := and({name}, {hex(self.get_truncated_bytesN_mask())})
}}"""
