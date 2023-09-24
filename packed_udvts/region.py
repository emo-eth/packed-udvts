from dataclasses import dataclass
from typing import Iterable, Optional, cast


from packed_udvts.member import Member
from sol_ast.ast import (
    Block,
    ElementaryTypeName,
    FunctionCall,
    FunctionDefinition,
    Identifier,
    IfStatement,
    InlineAssembly,
    Literal,
    ParameterList,
    RevertStatement,
    Statement,
    TypeName,
    VariableDeclaration,
    VariableDeclarationStatement,
    YulAssignment,
    YulBlock,
    YulExpression,
    YulStatement,
    YulVariableDeclaration,
    yul_gt,
    yul_or,
    yul_and,
    YulIdentifier,
    yul_shl,
    yul_shr,
    yul_signextend,
    YulLiteral,
    yul_iszero,
    Expression,
)
from sol_ast.enums import (
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
        if not self.member.signed:
            return value
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
        elif self.expansion_bits_name is not None:
            return self.compact_bits(self.member.shadowed_name.to_yul_identifier())
        else:
            return self.member.shadowed_name.to_yul_identifier()

    def get_shadowed_declaration(self, typesafe: bool = True) -> VariableDeclaration:
        """Get the shadowed declaration for this member"""
        return VariableDeclaration(
            type_name=self.member.typestr(typesafe), name=self.member.shadowed_name
        )

    def setter(self, udt_name: TypeName, typesafe: bool = True) -> FunctionDefinition:
        """Get the function body for the setter for this member"""
        value_expression = self.member.shadowed_name.to_yul_identifier()
        if self.member.num_expansion_bits is not None:
            assert self.expansion_bits_name is not None
            value_expression = yul_shr(
                self.expansion_bits_name.to_yul_identifier(),
                value_expression,
            )
        if self.member.signed and self.member.width_bits != 256:
            # mask signed values and use signextend later
            value_expression = yul_and(
                self.compact_sign(value_expression),
                self.end_mask_name.to_yul_identifier(),
            )

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
    def empty_mask(self) -> Literal:
        """Get the mask for the bits that should be empty given the number of shift bits"""
        if not self.member.expansion_bits:
            raise ValueError("Cannot get empty mask for non-expanded member")
        return Literal(
            value=hex(int("1" * self.member.expansion_bits, 2)),
            kind=LiteralKind.HexNumber,
        )

    @property
    def empty_mask_name(self) -> Optional[Identifier]:
        """Get the name of the mask for the bits that should be empty given the number of shift bits"""
        if not self.member.expansion_bits or self.member.bytesN:
            return None
        return Identifier(f"{self.member.name.upper()}_EMPTY_MASK")

    def check_empty_region(self, value: YulExpression) -> Optional[YulExpression]:
        """Get the assembly for checking if the empty bits are empty"""
        if self.empty_mask_name is None:
            return None
        return yul_iszero(
            yul_iszero(
                (
                    yul_and(
                        value,
                        self.empty_mask_name.to_yul_identifier(),
                    )
                )
            )
        )

    def check_signed_fits(self, value: YulExpression) -> YulExpression:
        """Get the assembly for checking if the bits are compacted without the sign bit"""
        return yul_gt(value, self.end_mask_name.to_yul_identifier())

    def compacted(self):
        bit_compacted = self.compact_bits(self.member.shadowed_name.to_yul_identifier())
        sign_compacted = self.compact_sign(bit_compacted)
        return sign_compacted

    @property
    def typesafe_require(self) -> Iterable[Statement]:
        """Get the require statement for this member"""
        # TODO: very inefficient; optimize by reusing masked values
        err_buf_declaration = self.err_buf_declaration()
        buffer_check = self.buffer_check()
        error = Literal("Unsafe value", LiteralKind.String)
        assertion = self.assert_buffer()
        return [err_buf_declaration, buffer_check, assertion]

    def assert_buffer(self) -> Statement:
        return self.assertion(
            Identifier("err"),
            FunctionCall(
                Identifier("UnsafeValue"),
                kind=FunctionCallKind.FunctionCall,
                arguments=[],
            ),
        )

    def assertion(self, predicate: Expression, error: Expression) -> Statement:
        return IfStatement(predicate, Block(RevertStatement(cast(FunctionCall, error))))

    def err_buf_declaration(self) -> VariableDeclarationStatement:
        return VariableDeclarationStatement(
            assignments=[
                VariableDeclaration(
                    type_name=ElementaryTypeName("bool"), name=Identifier("err")
                )
            ],
            initial_value=None,
        )

    def buffer_check(self) -> Statement:
        if self.member.bytesN is not None and self.expansion_bits_name:
            return self.signed_check_err_predicate()
        elif self.member.signed:
            return self.signed_check_err_predicate()
        elif self.expansion_bits_name:
            return self.expanded_check_err_predicate()
        else:
            return self.standard_check_err_predicate()

    def signed_check_err_predicate(self) -> Statement:
        return InlineAssembly(YulBlock(*self.signed_check_assembly()))

    def expanded_check_err_predicate(self) -> Statement:
        err_name = YulIdentifier("err")
        check = self.check_empty_region(self.member.shadowed_name.to_yul_identifier())
        if check is None:
            raise ValueError("Cannot check expansion of non-expanded member")
        err_assign = YulAssignment(err_name, value=check)

        return InlineAssembly(YulBlock(err_assign))

    def standard_check_err_predicate(self) -> Statement:
        err_name = YulIdentifier("err")
        return InlineAssembly(
            YulBlock(
                YulAssignment(
                    err_name,
                    value=yul_gt(
                        self.member.shadowed_name.to_yul_identifier(),
                        self.not_mask_name.to_yul_identifier(),
                    ),
                )
            )
        )

    def signed_check_assembly(self) -> list[YulStatement]:
        if not (self.member.signed or self.member.bytesN):
            raise ValueError("Cannot check sign of unsigned member")

        empty_check: Optional[YulExpression] = self.check_empty_region(
            self.member.shadowed_name.to_yul_identifier()
        )
        compacted_val = self.compact_bits(self.member.shadowed_name.to_yul_identifier())
        # TODO: figure out how to pass compacted value down the line to avoid recomputing
        var = YulIdentifier("compacted")
        declaration = YulVariableDeclaration(var, value=compacted_val)
        sign_check = self.check_signed_fits(var)
        err = YulIdentifier("err")

        if empty_check is not None:
            err_value = yul_or(empty_check, sign_check)
        else:
            err_value = sign_check
        err_assignment = YulAssignment(err, value=err_value)

        return [declaration, err_assignment]

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
                VariableDeclaration(
                    mutability=Mutability.Constant,
                    type_name=ElementaryTypeName("uint256"),
                    name=self.empty_mask_name,
                    value=self.empty_mask,
                )
                if self.empty_mask_name
                else None,
            ]
            if x
        ]
