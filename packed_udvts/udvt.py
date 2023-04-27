from packed_udvts.member import Member
from packed_udvts.region import Region
from typing import Union, Literal
from dataclasses import dataclass
from packed_udvts.util import to_title_case, to_camel_case


@dataclass
class UserDefinedValueType:
    name: str
    regions: list[Region]
    value_type: Union[Literal["uint256"], Literal["bytes32"]]

    def __init__(
        self,
        name: str,
        regions: list[Region],
        value_type: Union[Literal["uint256"], Literal["bytes32"]],
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
        value_type: Union[Literal["uint256"], Literal["bytes32"]],
    ):
        regions = []
        offset = 0
        for m in members:
            regions.append(Region(member=m, offset_bits=offset))
            offset += m.width_bits
        assert offset <= 256, "Too many bits to pack into a single UDVT"
        return UserDefinedValueType(name=name, regions=regions, value_type=value_type)

    @property
    def type_declaration(self):
        """Get the type declaration for this UDVT"""
        return f"type {self.name} is {self.value_type};"

    @property
    def using_declaration(self):
        """Get the using declaration for this UDVT"""
        return f"using {self.name}Type for {self.name} global;"

    def create_declaration(self, typesafe: bool = True):
        """Get the declaration for this UDVT"""
        initial = f"self := {self.regions[0].member.shadowed_name}"
        other_regions = []
        for r in self.regions[1:]:
            if r.member.bytesN is not None:
                expression_to_shl_then_or = r.member.shadowed_name
            else:
                expression_to_shl_then_or = (
                    f"shr({r.member.num_expansion_bits}, {r.member.shadowed_name})"
                )
            other_regions.append(f"shl({r.offset_bits}, {expression_to_shl_then_or})")
        remaining = "\n".join(other_regions)
        return f"""
function create{self.name}({', '.join(m.get_shadowed_declaration(typesafe=typesafe) for m in self.regions)}) internal pure returns ({self.name} self) {{
    assembly {{
        {initial}
        {remaining}  
    }}
}}
"""

    def unpack_declaration(self, typesafe: bool = True):
        """Get the unpack declaration for this UDVT"""
        assignments = []
        total_offset_bits = 0
        for r in self.regions:
            adjusted_offset_bits = r.offset_bits - total_offset_bits
            total_offset_bits += adjusted_offset_bits
            assignments.append(
                r._shift_and_unmask(total_offset_bits, r.member.num_expansion_bits)
            )

        return f"""
function unpack{self.name}({self.name} self) internal pure returns ({', '.join(m.get_shadowed_declaration(typesafe=typesafe) for m in self.regions)}) {{
    assembly {{
        
    }}
}}
        """
