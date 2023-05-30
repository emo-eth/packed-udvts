from packed_udvts.member import Member
from packed_udvts.region import Region
from typing import Union, Literal
from dataclasses import dataclass
from packed_udvts.constant_declaration import ConstantDeclaration
from math import ceil, log2
from typing import Optional

# for packed UDVTs, only allow bytes32 and unsigned integers
# bytesN are left-aligned, so right-aligned uints are preferable
VALID_LITERAL_VALUE_TYPES = Union[
    Literal["uint256"],
    Literal["bytes32"],
    Literal["uint8"],
    Literal["uint16"],
    Literal["uint32"],
    Literal["uint40"],
    Literal["uint48"],
    Literal["uint56"],
    Literal["uint64"],
    Literal["uint72"],
    Literal["uint80"],
    Literal["uint88"],
    Literal["uint96"],
    Literal["uint104"],
    Literal["uint112"],
    Literal["uint120"],
    Literal["uint128"],
    Literal["uint136"],
    Literal["uint144"],
    Literal["uint152"],
    Literal["uint160"],
    Literal["uint168"],
    Literal["uint176"],
    Literal["uint184"],
    Literal["uint192"],
    Literal["uint200"],
    Literal["uint208"],
    Literal["uint216"],
    Literal["uint224"],
    Literal["uint232"],
    Literal["uint240"],
    Literal["uint248"],
    Literal["uint256"],
]


@dataclass
class UserDefinedValueType:
    name: str
    regions: list[Region]
    value_type: VALID_LITERAL_VALUE_TYPES

    def __init__(
        self,
        name: str,
        regions: list[Region],
        value_type: VALID_LITERAL_VALUE_TYPES,
    ):
        assert len(regions) > 0, "UDVTs must have at least one region"
        assert value_type in ["uint256", "bytes32"], "UDVTs must be uint256 or bytes32"
        self.name = name
        self.regions = regions
        self.value_type = value_type

    @staticmethod
    def from_members(
        name: str,
        members: list[Member],
        value_type: VALID_LITERAL_VALUE_TYPES,
    ):
        regions = []
        offset = 0
        for m in members:
            regions.append(Region(member=m, offset_bits=offset))
            offset += m.width_bits
        assert offset <= 256, "Too many bits to pack into a single UDVT"
        return UserDefinedValueType(name=name, regions=regions, value_type=value_type)

    @staticmethod
    def packed_array_of(
        u: Union["UserDefinedValueType", Member], max_length: Optional[int] = None
    ) -> "UserDefinedValueType":
        # get the total number that can be packed into 256 bits
        number_to_pack = max_length or 256 // u.width_bits
        # get the number of remaining bits after packing
        remaining_bits = 256 - (u.width_bits * number_to_pack)
        # ensure there are enough remaining bits to pack the length; calculate the number of bits needed to pack the length
        length_width_bits = ceil(log2(number_to_pack))
        # decrement number_to_pack until length can fit into remaining bits
        while remaining_bits < length_width_bits:
            number_to_pack -= 1
            length_width_bits = ceil(log2(number_to_pack))
            remaining_bits = 256 - (u.width_bits * number_to_pack)

        # create first member of array UDVT, which is the length
        members = [Member(name="length", width_bits=length_width_bits, signed=False)]
        # extend with the packed members, each named index0, index1, etc.
        members.extend(
            [
                Member(name=f"index{i}", width_bits=u.width_bits, custom_typestr=u.name)
                for i in range(number_to_pack)
            ]
        )
        # create the array UDVT
        return UserDefinedValueType.from_members(
            name=f"{u.name}Array", members=members, value_type="uint256"
        )

    @property
    def width_bits(self):
        """Get the width of this UDVT in bits"""
        return (
            sum(r.member.width_bits for r in self.regions)
            if self.value_type != "bytes32"
            else 256
        )

    @property
    def type_declaration(self):
        """Get the type declaration for this UDVT"""
        return f"type {self.name} is {self.value_type};"

    @property
    def using_declaration(self):
        """Get the using declaration for this UDVT"""
        return f"using {self.name}Type for {self.name} global;"

    def create_declaration(self, typesafe: bool = True):
        """Get the declaration for this UDVT
        TODO: investigate the effect ordering of parameters has on bytecode"""
        initial = f"self := {self.regions[0].member.shadowed_name}"
        other_regions = []
        for r in self.regions[1:]:
            if r.member.bytesN is None:
                expression_to_shl_then_or = r.member.shadowed_name
            else:
                assert (
                    r.member.num_expansion_bits is not None
                ), "Member must have num_expansion_bits if not bytesN"
                expression_to_shl_then_or = (
                    f"shr({r.member.num_expansion_bits}, {r.member.shadowed_name})"
                )
            other_regions.append(
                f"self := or(self, shl({r.offset_bits_name}, {expression_to_shl_then_or}))"
            )
        remaining = "\n".join(other_regions)
        return f"""
function create{self.name}({', '.join(m.get_shadowed_declaration(typesafe=typesafe) for m in self.regions)}) internal pure returns ({self.name} self) {{
assembly {{
{initial}
{remaining}
}}
}}"""

    def unpack_declaration(self, typesafe: bool = True):
        """Get the unpack declaration for this UDVT
        TODO: investigate the effect ordering of return values has on bytecode"""
        assignments = []
        for r in self.regions:
            assignments.append(r._shift_and_unmask())
        assignment_strs = "\n".join(assignments)
        return f"""
function unpack{self.name}({self.name} self) internal pure returns ({', '.join(m.get_shadowed_declaration(typesafe=typesafe) for m in self.regions)}) {{
assembly {{
{assignment_strs}
}}
}}"""

    def library_declaration(self, typesafe: bool = True):
        """Get the library declaration for this UDVT"""
        constants_declarations: list[ConstantDeclaration] = []
        for r in self.regions:
            constants_declarations.extend(r.get_constant_declarations())
        constants_set = set(constants_declarations)
        constants_str = "\n".join(sorted(x.render() for x in constants_set))
        getters = "\n".join(
            x.getter(udt_name=self.name, typesafe=typesafe) for x in self.regions
        )
        setters = "\n".join(
            x.setter(udt_name=self.name, typesafe=typesafe) for x in self.regions
        )
        return f"""
library {self.lib_name} {{
{constants_str}

{self.create_declaration(typesafe=typesafe)}

{self.unpack_declaration(typesafe=typesafe)}

{getters}

{setters}
}}"""

    def render_file(self, typesafe: bool = True):
        """Render the file for this UDVT"""
        return f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

{self.type_declaration}

{self.using_declaration}

{self.library_declaration(typesafe=typesafe)}
"""

    @property
    def var_name(self):
        """Get the name of the variable for this UDVT"""
        return self.name[0].lower() + self.name[1:]

    @property
    def declaration(self):
        """Get the declaration for this UDVT"""
        return f"{self.name} {self.var_name}"

    @property
    def lib_name(self):
        """Get the library name for this UDVT"""
        return f"{self.name}Type"
