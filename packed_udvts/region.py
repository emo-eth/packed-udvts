from ast import Expression
from dataclasses import dataclass
from pyclbr import Function
from typing import Iterable, Optional

from numpy import block
from packed_udvts.member import Member
from packed_udvts.util import to_statements
from sol_ast.ast import (
    Assignment,
    BinaryOperation,
    Block,
    ElementaryTypeName,
    ExpressionStatement,
    FunctionCall,
    FunctionDefinition,
    Identifier,
    InlineAssembly,
    Literal,
    ParameterList,
    LineStatement,
    Statement,
    TypeName,
    VariableDeclaration,
    YulAssignment,
    YulBlock,
    YulExpression,
    yul_gt,
    yul_or,
    yul_and,
    YulIdentifier,
    yul_shl,
    yul_shr,
    yul_signextend,
    YulLiteral,
)
from sol_ast.enums import (
    BinaryOperator,
    FunctionCallKind,
    LiteralKind,
    StateMutability,
    Visibility,
)


@dataclass
class Region:
    member: Member
    # offset from the LEFT of the 256-bit word of this member
    offset_bits: int

    def __init__(self, member: Member, offset_bits: int):
        self.member = member
        self.offset_bits = offset_bits

    @property
    def end_mask(self) -> Literal:
        """Get the mask for this member, which will clear all bits above "width_bits"
        It should return a hex string starting with 0x and contain as many hex chars as necessary
        """
        # lol, lmao
        mask = int("1" * self.member.width_bits, 2)
        return Literal(value=hex(mask), kind=LiteralKind.HexNumber)

    @property
    def end_mask_name(self) -> Identifier:
        """Get the name of the mask for this member, which will clear all bits above "width_bits"
        It should return a string
        """
        return Identifier(f"_{self.member.width_bits}_BIT_END_MASK")

    @property
    def not_mask(self) -> Literal:
        """Get the 256-bit not-mask for this member; it should have 0 bits where the member is, and 1 bits everywhere else
        It should return a hex string starting with 0x and contain 64 hex characters"""
        # lol, lmao
        mask = int(
            "1" * (256 - self.offset_bits - self.member.width_bits)
            + "0" * self.member.width_bits
            + "1" * self.offset_bits,
            2,
        )
        return Literal(value=hex(mask), kind=LiteralKind.HexNumber)

    @property
    def not_mask_name(self) -> Identifier:
        """Get the name of the 256-bit not-mask for this member; it should have 0 bits where the member is, and 1 bits everywhere else
        It should return a string
        """
        return Identifier(f"{self.member.name.upper()}_NOT_MASK")

    @property
    def offset_bits_name(self) -> Identifier:
        """Get the name of the offset for this member; it should return a string"""
        return Identifier(f"{self.member.name.upper()}_OFFSET")

    @property
    def expansion_bits_name(self) -> Optional[Identifier]:
        """Get the name of the expansion bits for this member; it should return a string"""
        if self.member.num_expansion_bits is None:
            return None
        return Identifier(f"{self.member.name.upper()}_EXPANSION_BITS")

    @property
    def assembly_representation(self) -> YulExpression:
        """Get the assembly representation of this member"""
        if self.member.signed:
            # if the member is signed, the 256th bit is set
            # this needs to be "compacted" down into the member's width
            # first test if it is greater than end mask, ie, signed
            signed_test = yul_gt(
                self.member.shadowed_name.to_yul_identifier(),
                self.end_mask_name.to_yul_identifier(),
            )
            # if it is, shift it all the way to the left of the member. if it's 0, this does nothing
            compact_signed_bit = yul_shl(
                YulLiteral(str(self.member.width_bits - 1)), signed_test
            )
            # mask the signed bit out of the member
            masked_value = yul_and(
                self.member.shadowed_name.to_yul_identifier(),
                self.end_mask_name.to_yul_identifier(),
            )
            # OR the masked value with the compacted signed bit
            return yul_or(compact_signed_bit, masked_value)

        else:
            return self.member.shadowed_name.to_yul_identifier()

    def get_shadowed_declaration(self, typesafe: bool = True) -> VariableDeclaration:
        """Get the shadowed declaration for this member"""
        return VariableDeclaration(
            type_name=self.member.typestr(typesafe), name=self.member.shadowed_name.name
        )

    def setter(self, udt_name: TypeName, typesafe: bool = True) -> FunctionDefinition:
        """Get the function body for the setter for this member"""
        if self.member.num_expansion_bits is not None:
            assert self.expansion_bits_name is not None
            value_expression = yul_shr(
                self.expansion_bits_name.to_yul_identifier(),
                self.member.shadowed_name.to_yul_identifier(),
            )
        else:
            if self.member.signed and self.member.width_bits != 256:
                # mask signed values and use signextend later
                value_expression = yul_and(
                    self.member.shadowed_name.to_yul_identifier(),
                    self.end_mask_name.to_yul_identifier(),
                )
            else:
                value_expression = self.member.shadowed_name.to_yul_identifier()
        if self.offset_bits:
            rhs = yul_shl(self.offset_bits_name.to_yul_identifier(), value_expression)
        else:
            rhs = value_expression
        masked_lhs = yul_and(
            YulIdentifier("self"), self.not_mask_name.to_yul_identifier()
        )
        updated_assignment = YulAssignment(
            YulIdentifier("updated"), value=yul_or(masked_lhs, rhs)
        )
        inline_assembly = InlineAssembly(YulBlock(updated_assignment))
        if typesafe:
            statements = Block(*self.typesafe_require, inline_assembly)
        else:
            statements = Block(inline_assembly)
        return FunctionDefinition(
            name=f"set{self.member.title}",
            parameters=ParameterList(
                VariableDeclaration(type_name=udt_name, name="self"),
                self.get_shadowed_declaration(typesafe),
            ),
            return_parameters=ParameterList(
                VariableDeclaration(type_name=udt_name, name="updated")
            ),
            visibility=Visibility.Internal,
            state_mutability=StateMutability.Pure,
            body=statements,
        )
        return f"""
function set{self.member.title}({udt_name} self, {self.member.typestr(typesafe)} {self.member.shadowed_name}) internal pure returns ({udt_name} updated) {{
{self.typesafe_require if typesafe and not self.member.custom_typestr else ""}
assembly {{
updated := or({masked_lhs}, {rhs})
}}
}}"""

    @property
    def typesafe_require(self) -> Iterable[Statement]:
        """Get the require statement for this member"""
        # TODO: very inefficient; optimize by reusing masked values
        initial_cast_statements: list[Statement] = []
        if self.member.bytesN is not None:
            if self.member.num_expansion_bits:
                initial_cast_statements = [
                    ExpressionStatement(
                        VariableDeclaration(ElementaryTypeName("uint256"), "cast")
                    ),
                    InlineAssembly(
                        YulBlock(
                            YulAssignment(
                                YulIdentifier("cast"),
                                value=yul_shr(
                                    YulLiteral(str(self.member.num_expansion_bits)),
                                    self.member.shadowed_name.to_yul_identifier(),
                                ),
                            )
                        )
                    ),
                ]
                require_predicate = BinaryOperation(
                    Identifier("cast"),
                    BinaryOperator.LessThanOrEqual,
                    self.end_mask_name,
                )
            else:
                return []
        elif self.member.signed:
            initial_cast_statements = [
                ExpressionStatement(
                    VariableDeclaration(ElementaryTypeName("uint256"), "cast")
                ),
                InlineAssembly(
                    YulBlock(
                        YulAssignment(
                            YulIdentifier("cast"),
                            value=yul_and(
                                self.member.shadowed_name.to_yul_identifier(),
                                self.end_mask_name.to_yul_identifier(),
                            ),
                        )
                    )
                ),
            ]
            require_predicate = BinaryOperation(
                Identifier("cast"),
                BinaryOperator.LessThanOrEqual,
                # shift right to account for signed bit
                BinaryOperation(self.end_mask_name, BinaryOperator.Shr, Literal("1")),
            )
        else:
            require_predicate = BinaryOperation(
                self.member.shadowed_name,
                BinaryOperator.LessThanOrEqual,
                self.end_mask_name,
            )
        return initial_cast_statements + [
            ExpressionStatement(
                FunctionCall(
                    Identifier("require"),
                    kind=FunctionCallKind.FunctionCall,
                    arguments=[
                        require_predicate,
                        Literal(
                            f"{self.member.name} value too large", LiteralKind.String
                        ),
                    ],
                )
            )
        ]

    def getter(self, udt_name: TypeName, typesafe: bool = True) -> FunctionDefinition:
        """Get the function body for the getter for this member"""
        return FunctionDefinition(
            name=f"get{self.member.title}",
            parameters=ParameterList(
                VariableDeclaration(type_name=udt_name, name="self")
            ),
            return_parameters=ParameterList(
                VariableDeclaration(
                    type_name=self.member.typestr(typesafe),
                    name=self.member.shadowed_name.name,
                )
            ),
            state_mutability=StateMutability.Pure,
            body=Block(self._shift_and_unmask()),
        )

    def _shift_and_unmask(self) -> InlineAssembly:
        """Get the assembly for shifting and unmasking this member"""
        expression_to_mask: YulExpression
        if self.offset_bits == 0:
            expression_to_mask = YulIdentifier("self")
        else:
            expression_to_mask = yul_shr(
                self.offset_bits_name.to_yul_identifier(), YulIdentifier("self")
            )
        masked_expression = yul_and(
            expression_to_mask, self.end_mask_name.to_yul_identifier()
        )
        if self.member.num_expansion_bits:
            assert self.expansion_bits_name is not None
            rhs = yul_shl(
                self.expansion_bits_name.to_yul_identifier(), masked_expression
            )
        else:
            if self.member.signed and self.member.width_bits != 256:
                rhs = yul_signextend(
                    YulLiteral(str(self.member.ceil_bytes - 1)), masked_expression
                )
            else:
                rhs = masked_expression
        assignment = YulAssignment(
            self.member.shadowed_name.to_yul_identifier(), value=rhs
        )
        return InlineAssembly(YulBlock(assignment))

    def get_constant_declarations(self) -> list[VariableDeclaration]:
        """Get the constant declarations for this member"""
        return [
            x
            for x in [
                VariableDeclaration(
                    constant=True,
                    type_name=ElementaryTypeName("uint256"),
                    name=self.end_mask_name.name,
                    value=self.end_mask,
                ),
                VariableDeclaration(
                    constant=True,
                    type_name=ElementaryTypeName("uint256"),
                    name=self.not_mask_name.name,
                    value=self.not_mask,
                ),
                VariableDeclaration(
                    constant=True,
                    type_name=ElementaryTypeName("uint256"),
                    name=self.offset_bits_name.name,
                    value=Literal(str(self.offset_bits)),
                )
                if self.offset_bits
                else None,
                VariableDeclaration(
                    constant=True,
                    type_name=ElementaryTypeName("uint256"),
                    name=self.expansion_bits_name.name,
                    value=Literal(str(self.member.num_expansion_bits)),
                )
                if self.expansion_bits_name
                else None,
            ]
            if x
        ]
