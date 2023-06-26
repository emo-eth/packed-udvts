# to suppor TYPE_CHECKING
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from sol_ast.ast import (
    Assignment,
    ElementaryTypeName,
    ElementaryTypeNameExpression,
    FunctionCall,
    Identifier,
    InlineAssembly,
    Literal,
    TypeName,
    UserDefinedTypeName,
    VariableDeclaration,
    YulBlock,
    YulAssignment,
    YulLiteral,
    yul_and,
)
from packed_udvts.util import to_title_case
from math import ceil

from sol_ast.enums import (
    AssignmentOperator,
    FunctionCallKind,
    InlineAssemblyFlag,
    LiteralKind,
    YulLiteralKind,
)

if TYPE_CHECKING:
    from packed_udvts.udvt import UserDefinedValueType


@dataclass
class Member:
    # snake-case name of this member; will be converted to title case for the getter and setter
    # and upper-cased for constants
    name: str
    # width of this member in bits
    width_bits: int
    # if a bytesN type, the number of bytes
    bytesN: Optional[int] = None
    # if not bytesN, signed or unsigned
    signed: bool = False
    # if a member is itself a UDVT, this is the name of the UDVT
    custom_typestr: Optional[UserDefinedTypeName] = None
    # if a member should be multiplied by a power of two, this is the power of two
    expansion_bits: Optional[int] = None

    def __init__(
        self,
        name: str,
        width_bits: int,
        bytesN: Optional[int] = None,
        signed: bool = False,
        custom_typestr: Optional[UserDefinedTypeName] = None,
        expansion_bits: Optional[int] = None,
    ):
        assert width_bits > 0, "width_bits must be positive"
        assert bytesN is None or bytesN > 0, "bytesN must be positive or None"
        if signed:
            assert bytesN is None, "signed members must not be bytesN types"
            assert (
                width_bits % 8 == 0
            ), "signed members must have a width divisible by 8 for compatibility with SIGNEXTEND"
        self.name = name
        self.width_bits = width_bits
        self.bytesN = bytesN
        self.signed = signed
        self.custom_typestr = custom_typestr
        if expansion_bits is not None:
            # TODO: signextend?
            assert expansion_bits >= 0, "expansion_bits must be non-negative"
            assert expansion_bits + width_bits <= 256, "expansion_bits too large"
        self.expansion_bits = expansion_bits

    @staticmethod
    def from_udvt(udvt: UserDefinedValueType, name: str) -> "Member":
        """Create a new member from a UDVT"""
        assert udvt.width_bits < 256, "Cannot create a member from a full-width UDVT"
        return Member(
            name=name,
            width_bits=udvt.width_bits,
            bytesN=None,  # never bytesN since only bytes32 is allowed which fails above assertion
            signed=False,  # this library only allows unsigned uints for UDVTs
            custom_typestr=udvt.name,
        )

    @property
    def title(self) -> str:
        """Get the title case name of this region"""
        return to_title_case(self.name)

    @property
    def shadowed_name(self) -> Identifier:
        """Get the shadowed name of this region"""
        return Identifier(f"_{self.name}")

    @property
    def safe_typestr(self) -> ElementaryTypeName:
        """Get the safe typestr of this region
        TODO: udvt members?
        """
        if self.bytesN is None:
            num_bytes = (self.width_bits + (self.expansion_bits or 0)) // 8
            recovered_bits = num_bytes * 8
            if recovered_bits == self.width_bits:
                num_bits = recovered_bits
            else:
                num_bits = (num_bytes + 1) * 8
            return ElementaryTypeName(f"{'' if self.signed else 'u'}int{num_bits}")
        return ElementaryTypeName(f"bytes{self.bytesN}")

    @property
    def ceil_bytes(self) -> int:
        """Get the number of whole bytes necessary to represent this member"""
        return ceil(self.width_bits / 8)

    @property
    def unsafe_typestr(self) -> TypeName:
        """Get the typestr of this region"""
        if self.bytesN is None:
            return ElementaryTypeName(f"{'' if self.signed else 'u'}int256")
        return ElementaryTypeName(f"bytes32")

    @property
    def declaration(self) -> VariableDeclaration:
        """Get the declaration of this member"""
        return VariableDeclaration(type_name=self.safe_typestr, name=self.name)

    @property
    def shadowed_declaration(self) -> VariableDeclaration:
        """Get the shadowed declaration of this member"""
        return VariableDeclaration(
            type_name=self.safe_typestr, name=self.shadowed_name.name
        )

    @property
    def num_expansion_bits(self) -> Optional[int]:
        """Get the number of bits to expand this region by"""
        if self.bytesN:
            # eg: bytes4; width of 5:
            # 256 - 32 = 224
            return 256 - self.bytesN * 8
        return self.expansion_bits

    def typestr(self, typesafe: bool) -> TypeName:
        """Get the typestr of this region"""
        if self.custom_typestr is not None:
            return self.custom_typestr
        if typesafe:
            return self.safe_typestr
        return self.unsafe_typestr

    def get_lower_bound(self) -> Literal:
        """Get the lower bound of this member"""
        if self.bytesN:
            raise ValueError("Cannot get lower bound of bytesN member")
        if not self.signed:
            return Literal(str(0))
        else:
            return Literal(str(-1 * (2 ** (self.width_bits - 1))))

    def get_upper_bound(self) -> Literal:
        """Get the upper bound of this member"""
        if self.bytesN:
            raise ValueError("Cannot get upper bound of bytesN member")
        if not self.signed:
            x: int = 2**self.width_bits - 1
            return Literal(str(x))
        else:
            x: int = 2 ** (self.width_bits - 1) - 1
            return Literal(str(x))

    def get_truncated_bytesN_mask(self) -> Literal:
        """Get the mask to truncate bytesN members"""
        if self.bytesN is None:
            raise ValueError("Cannot get truncated bytesN mask of non-bytesN member")
        max_numeric_value: int = 2 ** (self.width_bits) - 1
        # shift upper_mask to the left by the number of expansion bits
        return Literal(str(max_numeric_value << (self.num_expansion_bits or 0)))

    def get_bounds(
        self, name: Optional[Identifier] = None
    ) -> Assignment | InlineAssembly:
        if name is None:
            name = Identifier(self.name)
        if self.custom_typestr:
            raise ValueError("Cannot get bound string of UDVT")
        if self.bytesN is None:
            return Assignment(
                lhs=name,
                rhs=FunctionCall(
                    expression=ElementaryTypeNameExpression(self.safe_typestr),
                    kind=FunctionCallKind.TypeConversion,
                    arguments=[
                        FunctionCall(
                            expression=Identifier(name="bound"),
                            kind=FunctionCallKind.FunctionCall,
                            arguments=[
                                name,
                                self.get_lower_bound(),
                                self.get_upper_bound(),
                            ],
                        )
                    ],
                ),
                operator=AssignmentOperator.Assign,
            )
        return InlineAssembly(
            ast=YulBlock(
                YulAssignment(
                    name.to_yul_identifier(),
                    value=yul_and(
                        name.to_yul_identifier(),
                        self.get_truncated_bytesN_mask().to_yul_literal(),
                    ),
                )
            )
        )
