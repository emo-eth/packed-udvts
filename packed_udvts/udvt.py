from itertools import chain

from packed_udvts.member import Member
from packed_udvts.region import Region
from typing import Iterable, Union, Literal
from dataclasses import dataclass
from math import ceil, log2
from typing import Optional

from sol_ast.ast import (
    Block,
    ContractDefinition,
    ElementaryTypeName,
    FunctionDefinition,
    FunctionIdentifierPath,
    Identifier,
    InlineAssembly,
    License,
    ParameterList,
    PragmaDirective,
    SourceUnit,
    UserDefinedTypeName,
    UserDefinedValueTypeDefinition,
    UsingForDirective,
    VariableDeclaration,
    VariableDeclarationStatement,
    YulAssignment,
    YulBlock,
    Literal as SolLiteral,
    YulExpression,
    YulIdentifier,
    yul_shr,
    yul_or,
    yul_shl,
    YulLiteral,
)
from sol_ast.enums import ContractKind, LiteralKind, StateMutability

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
    name: UserDefinedTypeName
    regions: list[Region]
    value_type: ElementaryTypeName

    def __init__(
        self,
        name: str,
        regions: list[Region],
        value_type: VALID_LITERAL_VALUE_TYPES,
    ):
        assert len(regions) > 0, "UDVTs must have at least one region"
        assert value_type in ["uint256", "bytes32"], "UDVTs must be uint256 or bytes32"
        self.name = UserDefinedTypeName(name=name)
        self.regions = regions
        self.value_type = ElementaryTypeName(value_type)

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
                Member(
                    name=f"index{i}",
                    width_bits=u.width_bits,
                    custom_typestr=u.name
                    if isinstance(u, UserDefinedValueType)
                    else None,
                )
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
    def type_declaration(self) -> UserDefinedValueTypeDefinition:
        """Get the type declaration for this UDVT"""
        return UserDefinedValueTypeDefinition(
            name=self.name.name, underlying_type=self.value_type
        )
        return f"type {self.name} is {self.value_type};"

    @property
    def using_declaration(self) -> UsingForDirective:
        """Get the using declaration for this UDVT"""
        return UsingForDirective(
            function_list=[FunctionIdentifierPath(self.lib_name.to_identifier_path())],
            type_name=self.name,
            global_=True,
        )

    def create_declaration(self, typesafe: bool = True) -> FunctionDefinition:
        """Get the declaration for this UDVT
        TODO: investigate the effect ordering of parameters has on bytecode"""
        initial_assigment = YulAssignment(
            YulIdentifier("self"), value=self.regions[0].assembly_representation
        )
        other_regions = []
        for r in self.regions[1:]:
            expression_to_shl_then_or: YulExpression = r.assembly_representation

            other_regions.append(
                YulAssignment(
                    YulIdentifier("self"),
                    value=yul_or(
                        YulIdentifier("self"),
                        yul_shl(
                            r.offset_bits_name.to_yul_identifier(),
                            expression_to_shl_then_or,
                        ),
                    ),
                )
            )
        # TODO: no bounds here?
        return FunctionDefinition(
            name=f"create{self.name}",
            parameters=ParameterList(
                *(m.get_shadowed_declaration(typesafe=typesafe) for m in self.regions)
            ),
            return_parameters=ParameterList(
                VariableDeclaration(name=Identifier("self"), type_name=self.name)
            ),
            state_mutability=StateMutability.Pure,
            body=Block(InlineAssembly(YulBlock(initial_assigment, *other_regions))),
        )

    def unpack_declaration(self, typesafe: bool = True) -> FunctionDefinition:
        """Get the unpack declaration for this UDVT
        TODO: investigate the effect ordering of return values has on bytecode"""
        return FunctionDefinition(
            name=f"unpack{self.name}",
            parameters=ParameterList(
                VariableDeclaration(name=Identifier("self"), type_name=self.name)
            ),
            return_parameters=ParameterList(
                *(m.get_shadowed_declaration(typesafe=typesafe) for m in self.regions)
            ),
            state_mutability=StateMutability.Pure,
            body=Block(
                InlineAssembly(
                    YulBlock(*(r._shift_and_unmask_statement() for r in self.regions))
                )
            ),
        )

    def library_declaration(self, typesafe: bool = True) -> ContractDefinition:
        """Get the library declaration for this UDVT"""
        constants_declarations: Iterable[VariableDeclarationStatement] = chain(
            (
                VariableDeclarationStatement(assignments=[v], initial_value=None)
                for r in self.regions
                for v in r.get_constant_declarations()
            )
        )

        return ContractDefinition(
            *constants_declarations,
            self.create_declaration(typesafe=typesafe),
            self.unpack_declaration(typesafe=typesafe),
            *(r.getter(udt_name=self.name, typesafe=typesafe) for r in self.regions),
            *(r.setter(udt_name=self.name, typesafe=typesafe) for r in self.regions),
            name=self.lib_name.name,
            kind=ContractKind.Library,
        )

    def render_file(self, typesafe: bool = True) -> SourceUnit:
        """Render the file for this UDVT"""
        return SourceUnit(
            PragmaDirective(["solidity", "^0.8.20"]),
            self.type_declaration,
            self.using_declaration,
            self.library_declaration(typesafe=typesafe),
            license=License("MIT"),
        )

    @property
    def var_name(self) -> Identifier:
        """Get the name of the variable for this UDVT"""
        return Identifier(self.name.name[0].lower() + self.name.name[1:])

    @property
    def declaration(self) -> VariableDeclaration:
        """Get the declaration for this UDVT"""
        return VariableDeclaration(type_name=self.name, name=self.var_name)

    @property
    def lib_name(self) -> Identifier:
        """Get the library name for this UDVT"""
        return Identifier(f"{self.name}Type")
