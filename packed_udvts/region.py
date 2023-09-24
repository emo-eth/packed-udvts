from dataclasses import dataclass
from typing import Iterable, Optional, TypeVar

from packed_udvts.member import Member
from sol_ast.ast import (
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
    Statement,
    TypeName,
    VariableDeclaration,
    YulAssignment,
    YulBlock,
    YulExpression,
    YulStatement,
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
    Mutability,
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
    def width_bits(self) -> Literal:
        """Get the width of this member in bits"""
        return Literal(value=str(self.member.width_bits), kind=LiteralKind.Number)

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
    def width_bits_name(self) -> Identifier:
        """Get the name of the width bits for this member; it should return a string"""
        return Identifier(f"{self.member.name.upper()}_WIDTH_BITS")

    def compact_sign(self, value: YulExpression) -> YulExpression:
        """Compact the signed bit of this member"""
        # OR the masked value with the compacted signed bit
        return yul_or(
            yul_shl(
                # if it is, shift it all the way to the left of the member. if it's 0, this does nothing
                YulLiteral(str(self.member.width_bits - 1)),
                # if the member is signed, the 256th bit is set
                # this needs to be "compacted" down into the member's width
                # test if it is greater than end mask, ie, signed
                yul_gt(
                    value,
                    self.end_mask_name.to_yul_identifier(),
                ),
            ),
            # mask the signed bit out of the member
            yul_and(
                value,
                self.end_mask_name.to_yul_identifier(),
            ),
        )

    def compact_bits(self, value: YulExpression) -> YulExpression:
        """Compact the expansion bits of this member"""
        if self.expansion_bits_name is None:
            return value
        return yul_shr(
            self.expansion_bits_name.to_yul_identifier(),
            value,
        )

    @property
    def assembly_representation(self) -> YulExpression:
        """Get the assembly representation of this member"""
        if self.member.signed:
            return self.compact_sign(
                self.compact_bits(self.member.shadowed_name.to_yul_identifier())
            )
        else:
            return self.member.shadowed_name.to_yul_identifier()

    def get_shadowed_declaration(self, typesafe: bool = True) -> VariableDeclaration:
        """Get the shadowed declaration for this member"""
        return VariableDeclaration(
            type_name=self.member.typestr(typesafe), name=self.member.shadowed_name
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
                VariableDeclaration(type_name=udt_name, name=Identifier("self")),
                self.get_shadowed_declaration(typesafe),
            ),
            return_parameters=ParameterList(
                VariableDeclaration(type_name=udt_name, name=Identifier("updated"))
            ),
            visibility=Visibility.Internal,
            state_mutability=StateMutability.Pure,
            body=statements,
        )

    @property
    def typesafe_require(self) -> Iterable[Statement]:
        """Get the require statement for this member"""
        # TODO: very inefficient; optimize by reusing masked values
        initial_cast_statements: list[Statement] = []
        if self.member.bytesN is not None:
            if self.member.num_expansion_bits:
                initial_cast_statements: list[Statement] = [
                    ExpressionStatement(
                        VariableDeclaration(
                            ElementaryTypeName("uint256"), Identifier("cast")
                        )
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
                    VariableDeclaration(
                        ElementaryTypeName("uint256"), Identifier("cast")
                    )
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
                VariableDeclaration(type_name=udt_name, name=Identifier("self"))
            ),
            return_parameters=ParameterList(
                VariableDeclaration(
                    type_name=self.member.typestr(typesafe),
                    name=self.member.shadowed_name,
                )
            ),
            state_mutability=StateMutability.Pure,
            body=Block(self._shift_and_unmask_block()),
        )

    def _shift_and_unmask_block(self) -> InlineAssembly:
        """Get the assembly for shifting and unmasking this member"""
        return InlineAssembly(YulBlock(self._shift_and_unmask_statement()))

    def _shift_and_unmask_statement(self) -> YulStatement:
        expression_to_mask: YulExpression
        if self.offset_bits == 0:
            expression_to_mask = YulIdentifier("self")
        else:
            expression_to_mask = yul_shr(
                self.offset_bits_name.to_yul_identifier(), YulIdentifier("self")
            )
        rhs = yul_and(expression_to_mask, self.end_mask_name.to_yul_identifier())
        if self.member.num_expansion_bits:
            assert self.expansion_bits_name is not None
            rhs = yul_shl(self.expansion_bits_name.to_yul_identifier(), rhs)
        if self.member.signed and self.member.width_bits != 256:
            rhs = yul_signextend(YulLiteral(str(self.member.ceil_bytes - 1)), rhs)
        return YulAssignment(self.member.shadowed_name.to_yul_identifier(), value=rhs)

    def get_constant_declarations(self) -> list[VariableDeclaration]:
        """Get the constant declarations for this member"""
        return [
            x
            for x in [
                VariableDeclaration(
                    mutability=Mutability.Constant,
                    type_name=ElementaryTypeName("uint256"),
                    name=self.end_mask_name,
                    value=self.end_mask,
                ),
                VariableDeclaration(
                    mutability=Mutability.Constant,
                    type_name=ElementaryTypeName("uint256"),
                    name=self.not_mask_name,
                    value=self.not_mask,
                ),
                VariableDeclaration(
                    mutability=Mutability.Constant,
                    type_name=ElementaryTypeName("uint256"),
                    name=self.offset_bits_name,
                    value=Literal(str(self.offset_bits)),
                )
                if self.offset_bits
                else None,
                VariableDeclaration(
                    mutability=Mutability.Constant,
                    type_name=ElementaryTypeName("uint256"),
                    name=self.expansion_bits_name,
                    value=Literal(str(self.member.num_expansion_bits)),
                )
                if self.expansion_bits_name
                else None,
            ]
            if x
        ]
