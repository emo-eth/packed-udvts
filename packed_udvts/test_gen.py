from itertools import chain
from packed_udvts.udvt import UserDefinedValueType
from packed_udvts.region import Region
from packed_udvts.util import to_statements
from sol_ast.ast import (
    Block,
    ContractDefinition,
    FunctionCall,
    FunctionDefinition,
    Identifier,
    ImportDirective,
    InheritanceSpecifier,
    License,
    Literal,
    MemberAccess,
    ParameterList,
    Expression,
    PragmaDirective,
    SourceUnit,
    SymbolAlias,
    UserDefinedTypeName,
    VariableDeclaration,
    VariableDeclarationStatement,
)
from sol_ast.enums import (
    ContractKind,
    FunctionCallKind,
    LiteralKind,
    Visibility,
)


class TestGen:
    udvt: UserDefinedValueType

    def __init__(self, udvt: UserDefinedValueType):
        self.udvt = udvt

    def call_get(
        self,
        target: Identifier,
        region: Region,
        terminal: bool = False,
    ):
        getter_name = f"get{region.member.title}"
        return FunctionCall(
            expression=MemberAccess(
                expression=target,
                member_name=getter_name,
            ),
            kind=FunctionCallKind.FunctionCall,
        )

    def call_set(self, region: Region, value: Expression) -> FunctionCall:
        return FunctionCall(
            expression=MemberAccess(
                expression=self.udvt.var_name, member_name=f"set{region.member.title}"
            ),
            arguments=[value],
            kind=FunctionCallKind.FunctionCall,
        )

    def updated_udvt_var_name(self) -> Identifier:
        return Identifier(f"updated{self.udvt.var_name.fmt().title()}")

    def update_region(
        self,
        region: Region,
        value: Expression,
        redeclare: bool = False,
    ) -> VariableDeclarationStatement:
        lhs = [self.updated_udvt_var_name()]
        if redeclare:
            lhs = [
                VariableDeclaration(self.udvt.name, name=self.updated_udvt_var_name())
            ]

        return VariableDeclarationStatement(
            assignments=lhs,
            initial_value=self.call_set(region, value),
        )

    def assert_eq(self, lhs: Expression, rhs: Expression, msg: str) -> FunctionCall:
        return FunctionCall(
            expression=Identifier("assertEq"),
            kind=FunctionCallKind.FunctionCall,
            arguments=[lhs, rhs, Literal(msg, kind=LiteralKind.String)],
        )

    def fuzz_get_set_region(self, region: Region) -> FunctionDefinition:
        updated_member_var_name = Identifier(f"updated{region.member.title}")
        updated_declaration = VariableDeclaration(
            region.member.safe_typestr, updated_member_var_name
        )

        # TODO: fuzz on member.width_bits, bound to 2**member.width_bits, then expand and cast to appropriate type
        all_region_bounds = chain(
            (r.member.get_bounds() for r in self.udvt.regions),
            (region.member.get_bounds(updated_member_var_name),),
        )

        declaration = VariableDeclarationStatement(
            assignments=[
                VariableDeclaration(type_name=self.udvt.name, name=self.udvt.var_name)
            ],
            initial_value=FunctionCall(
                expression=MemberAccess(
                    expression=Identifier(self.udvt.lib_name.name),
                    member_name=f"create{self.udvt.name}",
                ),
                kind=FunctionCallKind.FunctionCall,
                arguments=[r.member.identifier for r in self.udvt.regions],
                names=[r.member.shadowed_name for r in self.udvt.regions],
            ),
        )
        initial_getter_asserts = (
            self.assert_eq(
                self.call_get(self.udvt.var_name, r),
                r.member.identifier,
                f"getter for {r.member.name} failed",
            )
            for r in self.udvt.regions
        )
        update_region = self.update_region(
            region, updated_member_var_name, redeclare=True
        )

        post_update_non_updated_asserts = (
            self.assert_eq(
                self.call_get(self.updated_udvt_var_name(), r),
                r.member.identifier,
                f"getter for {r.member.name} failed post-update",
            )
            for r in self.udvt.regions
            if r != region
        )
        post_update_asserts = chain(
            post_update_non_updated_asserts,
            (
                self.assert_eq(
                    self.call_get(self.updated_udvt_var_name(), region),
                    updated_member_var_name,
                    f"getter for updated region {region.member.name} failed post-update",
                ),
            ),
        )

        return FunctionDefinition(
            f"testGetSet{region.member.title}",
            visibility=Visibility.Public,
            parameters=ParameterList(
                *(r.member.declaration for r in self.udvt.regions), updated_declaration
            ),
            body=Block(
                *to_statements(
                    *all_region_bounds,
                    declaration,
                    *initial_getter_asserts,
                    update_region,
                    *post_update_asserts,
                )
            ),
        )

    def generate(self) -> SourceUnit:
        functions = (self.fuzz_get_set_region(r) for r in self.udvt.regions)
        pragma = PragmaDirective(literals=["solidity", "^0.8.20"])

        test_import = ImportDirective(
            absolute_path=f"forge-std/Test.sol",
            file="",
            symbol_aliases=[SymbolAlias(foreign=Identifier("Test"))],
        )
        lib_and_udvt_import = ImportDirective(
            absolute_path=f"src/lib/{self.udvt.lib_name}.sol",
            file="",
            symbol_aliases=[
                SymbolAlias(foreign=Identifier(self.udvt.lib_name.name)),
                SymbolAlias(foreign=Identifier(self.udvt.name.name)),
            ],
        )

        contract_def = ContractDefinition(
            *functions,
            name=f"{self.udvt.name.fmt()}Test",
            base_contracts=[
                InheritanceSpecifier(base_name=UserDefinedTypeName("Test")),
            ],
            kind=ContractKind.Contract,
        )
        return SourceUnit(
            pragma,
            test_import,
            lib_and_udvt_import,
            contract_def,
            license=License("MIT"),
        )
