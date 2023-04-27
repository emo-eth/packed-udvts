from dataclasses import dataclass
from typing import Optional
from packed_udvts.member import Member


@dataclass
class Region:
    member: Member
    # offset from the LEFT of the 256-bit word of this member
    offset_bits: int

    def __init__(self, member: Member, offset_bits: int):
        self.member = member
        self.offset_bits = offset_bits

    @property
    def end_mask(self) -> str:
        """Get the mask for this member, which will clear all bits above "width_bits"
        It should return a hex string starting with 0x and contain as many hex chars as necessary
        """
        # lol, lmao
        mask = int("1" * self.member.width_bits, 2)
        return hex(mask)

    @property
    def end_mask_name(self) -> str:
        """Get the name of the mask for this member, which will clear all bits above "width_bits"
        It should return a string
        """
        return f"{self.member.name.upper()}_END_MASK"

    @property
    def not_mask(self) -> str:
        """Get the 256-bit not-mask for this member; it should have 0 bits where the member is, and 1 bits everywhere else
        It should return a hex string starting with 0x and contain 64 hex characters"""
        # lol, lmao
        mask = int(
            "1" * (256 - self.offset_bits - self.member.width_bits)
            + "0" * self.member.width_bits
            + "1" * self.offset_bits,
            2,
        )
        return hex(mask)

    @property
    def not_mask_name(self) -> str:
        """Get the name of the 256-bit not-mask for this member; it should have 0 bits where the member is, and 1 bits everywhere else
        It should return a string
        """
        return f"{self.member.name.upper()}_NOT_MASK"

    @property
    def offset_bits_name(self) -> str:
        """Get the name of the offset for this member; it should return a string"""
        return f"{self.member.name.upper()}_OFFSET"

    def get_shadowed_declaration(self, typesafe: bool = True):
        """Get the shadowed declaration for this member"""
        return f"{self.member.typestr(typesafe)} {self.member.shadowed_name}"

    def setter(self, udt_name: str, typesafe: bool = True) -> str:
        """Get the function body for the setter for this member"""
        if self.member.num_expansion_bits:
            compression = f"value := shr({self.member.num_expansion_bits}, value)"
        else:
            compression = "// no compression necessary"
        return f"""
function set{self.member.title}({udt_name} self, {self.member.typestr(typesafe)} value) internal pure returns ({udt_name} updated) {{
    require(value <= {self.end_mask_name}, "{self.member.name} value too large");
    assembly {{
        {compression}
        let masked := and(self, {self.not_mask_name})
        updated := or(masked, shl({self.offset_bits}, value))
    }}
}}"""

    def getter(self, udt_name: str, typesafe: bool = True) -> str:
        """Get the function body for the getter for this member"""
        return f"""
function get{self.member.title}({udt_name} self) internal pure returns ({self.member.typestr(typesafe)} {self.member.shadowed_name}) {{
    assembly {{
{self._shift_and_unmask(self.offset_bits,self.member.num_expansion_bits)}
    }}
}}"""

    def _shift_and_unmask(self, offset_bits: int, expansion_bits: Optional[int]) -> str:
        """Get the assembly for shifting and unmasking this member"""
        if offset_bits == 0:
            shift = "// no shift necessary"
        else:
            shift = f"self := shr({offset_bits}, self)"
        if not expansion_bits:
            if self.member.signed and self.member.width_bits != 256:
                param = self.member.whole_bytes - 1
                expansion = f"{self.member.shadowed_name} := signextend({param}, {self.member.shadowed_name})"
            else:
                expansion = "// no expansion or sign extension necessary"
        else:
            expansion = f"{self.member.shadowed_name} := shl({expansion_bits}, {self.member.shadowed_name})"
        return f"""
        {shift}
        {self.member.shadowed_name} := and(self, {self.end_mask_name})
        {expansion}
"""
