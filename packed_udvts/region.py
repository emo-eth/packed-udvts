from dataclasses import dataclass
from packed_udvts.util import to_title_case


@dataclass
class Region:
    # name of this member in the solidity struct
    name: str
    # width of this member in bits
    width_bits: int
    # offset from the LEFT of the 256-bit word of this member
    offset_bits: int

    def not_mask(self) -> str:
        """Get the 256-bit not-mask for this member; it should have 0 bits where the member is, and 1 bits everywhere else
        It should return a hex string starting with 0x and contain 64 hex characters"""
        # lol, lmao
        mask = int(
            "1" * (256 - self.offset_bits - self.width_bits)
            + "0" * self.width_bits
            + "1" * self.offset_bits,
            2,
        )
        return hex(mask)

    def end_mask(self) -> str:
        """Get the mask for this member, which will clear all bits above "width_bits"
        It should return a hex string starting with 0x and contain as many hex chars as necessary
        """
        # lol, lmao
        mask = int("1" * self.width_bits, 2)
        return hex(mask)

    def end_mask_name(self) -> str:
        """Get the name of the mask for this member, which will clear all bits above "width_bits"
        It should return a string
        """
        return f"{self.name.upper()}_END_MASK"

    def not_mask_name(self) -> str:
        """Get the name of the 256-bit not-mask for this member; it should have 0 bits where the member is, and 1 bits everywhere else
        It should return a string
        """
        return f"{self.name.upper()}_NOT_MASK"

    def offset_bits_name(self) -> str:
        """Get the name of the offset for this member; it should return a string"""
        return f"{self.name.upper()}_OFFSET"

    def setter(self, udt_name: str) -> str:
        """Get the function body for the setter for this member"""
        return f"""
function set{to_title_case(self.name)}({udt_name} self, uint256 value) internal pure returns ({udt_name} updated) {{
    require(value <= {self.end_mask_name()}, "{self.name} value too large");
    assembly {{
        let masked := and(self, {self.not_mask_name()})
        updated := or(masked, shl({self.offset_bits}, value))
    }}
}}"""
