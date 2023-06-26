from packed_udvts.member import Member
from packed_udvts.region import Region
from dataclasses import dataclass
from sol_ast.ast import (
    SourceUnit,
    UserDefinedValueTypeDefinition,
    ElementaryTypeName,
    UsingForDirective,
    TypeName,
    UserDefinedTypeName,
    IdentifierPath,
    ContractDefinition,
    ContractKind,
)


@dataclass
class UDTLibrary:
    udt_name: str
    regions: list[Region]

    def from_members(self):
        definition = UserDefinedValueTypeDefinition(
            name=self.udt_name, underlying_type=ElementaryTypeName("uint256")
        )
        lib_name = f"{self.udt_name}Library"
        return SourceUnit(
            definition,
            UsingForDirective(
                library_name=IdentifierPath(lib_name),
                type_name=definition.user_defined_type_name(),
            ),
            ContractDefinition(name=lib_name, kind=ContractKind.Library),
        )
        pass
