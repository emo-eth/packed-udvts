from dataclasses import dataclass
from typing import Optional
from packed_udvts.member import Member
from packed_udvts.constant_declaration import ConstantDeclaration


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
        return f"_{self.member.width_bits}_BIT_END_MASK"

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

    @property
    def expansion_bits_name(self) -> Optional[str]:
        """Get the name of the expansion bits for this member; it should return a string"""
        if self.member.num_expansion_bits is None:
            return None
        return f"{self.member.name.upper()}_EXPANSION_BITS"

    @property
    def assembly_representation(self) -> str:
        """Get the assembly representation of this member"""
        if self.member.signed:
            # if the member is signed, the 256th bit is set
            # this needs to be "compacted" down into the member's width
            # first test if it is greater than end mask, ie, signed
            signed_test = f"gt({self.member.shadowed_name}, {self.end_mask_name})"
            # if it is, shift it all the way to the left of the member. if it's 0, this does nothing
            compact_signed_bit = f"shl({self.member.width_bits-1}, {signed_test})"
            # mask the signed bit out of the member
            masked_value = f"and({self.member.shadowed_name}, {self.end_mask_name})"
            # OR the masked value with the compacted signed bit
            return f"or({compact_signed_bit}, {masked_value})"

        else:
            return self.member.shadowed_name

    def get_shadowed_declaration(self, typesafe: bool = True):
        """Get the shadowed declaration for this member"""
        return f"{self.member.typestr(typesafe)} {self.member.shadowed_name}"

    def setter(self, udt_name: str, typesafe: bool = True) -> str:
        """Get the function body for the setter for this member"""
        if self.member.num_expansion_bits:
            value_expression = (
                f"shr({self.expansion_bits_name}, {self.member.shadowed_name})"
            )
        else:
            if self.member.signed and self.member.width_bits != 256:
                # mask signed values and use signextend later
                value_expression = (
                    f"and({self.member.shadowed_name}, {self.end_mask_name})"
                )
            else:
                value_expression = self.member.shadowed_name
        if self.offset_bits:
            rhs = f"shl({self.offset_bits_name}, {value_expression})"
        else:
            rhs = value_expression
        masked_lhs = f"and(self, {self.not_mask_name})"
        return f"""
function set{self.member.title}({udt_name} self, {self.member.typestr(typesafe)} {self.member.shadowed_name}) internal pure returns ({udt_name} updated) {{
{self.typesafe_require if typesafe and not self.member.custom_typestr else ""}
assembly {{
updated := or({masked_lhs}, {rhs})
}}
}}"""

    @property
    def typesafe_require(self) -> str:
        """Get the require statement for this member"""
        # TODO: very inefficient; optimize by reusing masked values
        if self.member.bytesN is not None:
            if self.member.num_expansion_bits:
                preamble = f"""
uint256 cast;
assembly {{
cast := shr({self.member.num_expansion_bits}, {self.member.shadowed_name})
}}
    """
            else:
                preamble = ""
            lhs = "true"
        elif self.member.signed:
            preamble = f"""
uint256 cast;
assembly {{
cast := and({self.member.shadowed_name}, {self.end_mask_name})
}}
"""
            lhs = f"cast <= {self.end_mask_name}"
        else:
            preamble = ""
            lhs = f"{self.member.shadowed_name} <= {self.end_mask_name}"
        return f'{preamble}require({lhs}, "{self.member.name} value too large");'

    def getter(self, udt_name: str, typesafe: bool = True) -> str:
        """Get the function body for the getter for this member"""
        return f"""
function get{self.member.title}({udt_name} self) internal pure returns ({self.member.typestr(typesafe)} {self.member.shadowed_name}) {{
assembly {{
{self._shift_and_unmask()}
}}
}}"""

    def _shift_and_unmask(self) -> str:
        """Get the assembly for shifting and unmasking this member"""
        if self.offset_bits == 0:
            expression_to_mask = "self"
        else:
            expression_to_mask = f"shr({self.offset_bits_name}, self)"
        masked_expression = f"and({expression_to_mask}, {self.end_mask_name})"
        if self.member.num_expansion_bits:
            rhs = f"shl({self.expansion_bits_name}, {masked_expression})"
        else:
            if self.member.signed and self.member.width_bits != 256:
                rhs = f"signextend({self.member.ceil_bytes - 1}, {masked_expression})"
            else:
                rhs = masked_expression
        assignment = f"{self.member.shadowed_name} := {rhs}"
        return f"""{assignment}"""

    def get_constant_declarations(self) -> list[ConstantDeclaration]:
        """Get the constant declarations for this member"""
        return [
            x
            for x in [
                ConstantDeclaration(name=self.end_mask_name, value=self.end_mask),
                ConstantDeclaration(
                    name=self.not_mask_name,
                    value=self.not_mask,
                ),
                ConstantDeclaration(
                    name=self.offset_bits_name, value=str(self.offset_bits)
                )
                if self.offset_bits
                else None,
                ConstantDeclaration(
                    name=self.expansion_bits_name,
                    value=str(self.member.num_expansion_bits),
                )
                if self.expansion_bits_name
                else None,
            ]
            if x
        ]
