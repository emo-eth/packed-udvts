from dataclasses import dataclass
from typing import Optional
from packed_udvts.util import to_title_case


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

    def __init__(
        self,
        name: str,
        width_bits: int,
        bytesN: Optional[int] = None,
        signed: bool = False,
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
            num_bytes = self.width_bits // 8
            recovered_bits = num_bytes * 8
            if recovered_bits == self.width_bits:
                num_bits = recovered_bits
            else:
                num_bits = (num_bytes + 1) * 8
            return f"{'' if self.signed else 'u'}int{num_bits}"
        return f"bytes{self.bytesN}"

    @property
    def whole_bytes(self) -> int:
        """Get the number of whole bytes in this region"""
        return self.width_bits // 8 or 1

    @property
    def unsafe_typestr(self) -> str:
        """Get the typestr of this region"""
        if self.bytesN is None:
            return f"{'' if self.signed else 'u'}int256"
        return f"bytes32"

    @property
    def num_expansion_bits(self) -> Optional[int]:
        """Get the number of bits to expand this region by, if a bytesN type"""
        if self.bytesN is None:
            return None
        # eg: bytes4; width of 5:
        # 256 - 32 = 224
        return 256 - self.bytesN * 8

    def typestr(self, typesafe: bool) -> str:
        """Get the typestr of this region"""
        if typesafe:
            return self.safe_typestr
        return self.unsafe_typestr
