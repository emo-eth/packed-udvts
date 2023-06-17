from typing import (
    Optional,
    Union,
    TypeAlias,
    Literal as StringLiteral,
    Callable,
    Sequence,
)
from random import randint
from abc import ABC, abstractmethod

from sol_ast.enums import (
    Visibility,
    AssignmentOperator,
    BinaryOperator,
    StateMutability,
    Mutability,
    FunctionCallKind,
    LiteralKind,
    UnaryOperator,
    StorageLocation,
    FunctionKind,
    YulLiteralKind,
    AssemblyReferenceSuffix,
    InlineAssemblyFlag,
    ModifierInvocationKind,
    ContractKind,
)
from sol_ast.utils import line_join, wrap_block


class Unreachable(ValueError):
    pass


ElementaryOrRawTypeName: TypeAlias = "ElementaryTypeName"
UserDefinedTypeNameOrIdentifierPath: TypeAlias = Union[
    "UserDefinedTypeName", "IdentifierPath"
]
Expression: TypeAlias = Union[
    "Assignment",
    "BinaryOperation",
    "Conditional",
    "ElementaryTypeNameExpression",
    "FunctionCall",
    "FunctionCallOptions",
    "Identifier",
    "IndexAccess",
    "IndexRangeAccess",
    "Literal",
    "MemberAccess",
    "NewExpression",
    "TupleExpression",
    "UnaryOperation",
]

StructuredDocumentation: TypeAlias = str  # Union[str]


TypeName: TypeAlias = Union[
    "ArrayTypeName",
    "ElementaryTypeName",
    "FunctionTypeName",
    "Mapping",
    "UserDefinedTypeName",
]

YulCaseValue: TypeAlias = Union["YulLiteral", StringLiteral["default"]]


YulStatement: TypeAlias = Union[
    "YulAssignment",
    "YulBlock",
    "YulBreak",
    "YulContinue",
    "YulExpressionStatement",
    "YulLeave",
    "YulForLoop",
    "YulFunctionDefinition",
    "YulIf",
    "YulSwitch",
    "YulVariableDeclaration",
]

YulExpression: TypeAlias = Union["YulFunctionCall", "YulIdentifier", "YulLiteral"]

ExpressionOrVariableDeclarationStatement: TypeAlias = Union[
    "ExpressionStatement", "VariableDeclarationStatement"
]

Statement: TypeAlias = Union[
    "Block",
    "Break",
    "Continue",
    "DoWhileStatement",
    "EmitStatement",
    "ExpressionStatement",
    "ForStatement",
    "IfStatement",
    "InlineAssembly",
    "PlaceholderStatement",
    "Return",
    "RevertStatement",
    "TryStatement",
    "UncheckedBlock",
    "VariableDeclarationStatement",
    "WhileStatement",
]


IdentifierOrIdentifierPath: TypeAlias = Union["Identifier", "IdentifierPath"]


ContractDefinitionPart: TypeAlias = Union[
    "EnumDefinition",
    "ErrorDefinition",
    "EventDefinition",
    "FunctionDefinition",
    "ModifierDefinition",
    "StructDefinition",
    "StructDefinition",
    "UserDefinedValueTypeDefinition",
    "UsingForDirective",
    "VariableDeclaration",
]

SourceUnitPart: TypeAlias = Union[
    "PragmaDirective",
    "ImportDirective",
    "UsingForDirective",
    "VariableDeclaration",
    "EnumDefinition",
    "ErrorDefinition",
    "FunctionDefinition",
    "StructDefinition",
    "UserDefinedValueTypeDefinition",
    "ContractDefinition",
]


class AstId(int):
    pass


class SourceLocation:
    start: Optional[int]
    length: Optional[int]
    index: Optional[int]

    def __init__(
        self, start: Optional[int], length: Optional[int], index: Optional[int]
    ):
        self.start = start
        self.length = length
        self.index = index


class AstNode(ABC):
    id: AstId
    src: Optional[SourceLocation]
    parent: Optional["AstNode"]
    d: dict[int, "AstNode"] = {}

    def __init__(self):
        self.id = AstId(randint(0, 2**64))
        self.d[self.id] = self

    def accept(self, node: "AstNode") -> None:
        self.parent = node

    @abstractmethod
    def serialize(self) -> str:
        pass


class TypeDescriptions:
    type_identifier: Optional[str]
    type_string: Optional[str]


class ExprNode(AstNode):
    argument_types: list[TypeDescriptions]
    is_constant: bool
    is_l_value: bool
    is_pure: bool
    l_value_requested: bool
    type_descriptions: TypeDescriptions


class Identifier(AstNode):
    argument_types: list[TypeDescriptions]
    name: str
    overloaded_declarations: list[int]
    referenced_declaration: Optional[int]
    type_descriptions: TypeDescriptions


def DChecker(node: AstNode) -> None:
    if node.id not in node.d:
        raise Unreachable(f"Node {node.id} not in d")


class SymbolAlias:
    foreign: Identifier
    local: Optional[str]
    name_location: Optional[SourceLocation]

    def __init__(
        self,
        foreign: Identifier,
        local: Optional[str] = None,
        name_location: Optional[SourceLocation] = None,
    ):
        self.foreign = foreign
        self.local = local
        self.name_location = name_location

    def serialize(self) -> str:
        if self.local is None:
            return self.foreign.serialize()
        else:
            return f"{self.foreign.serialize()} as {self.local}"


class PragmaDirective(AstNode):
    literals: list[str]

    def __init__(self, literals: list[str]):
        super().__init__()
        self.literals = literals


class ImportDirective(AstNode):
    absolute_path: str
    file: str
    name_location: Optional[SourceLocation]
    scope: AstId
    source_unit: AstId
    symbol_aliases: list[SymbolAlias]
    unit_alias: str


class IdentifierPath(AstNode):
    name: str
    referenced_declaration: AstId


class FunctionIdentifierPath:
    function: IdentifierPath


class UserDefinedTypeName(AstNode):
    type_descriptions: TypeDescriptions


class Conditional(ExprNode):
    condition: "Expression"
    false_expression: "Expression"
    true_expression: "Expression"


class ElementaryTypeName(AstNode):
    type_descriptions: TypeDescriptions
    name: str
    state_mutability: Optional[StateMutability]


class ElementaryTypeNameExpression(ExprNode):
    type_name: ElementaryOrRawTypeName


class BinaryOperation(AstNode):
    common_type: TypeDescriptions
    lhs: "Expression"
    operator: BinaryOperator
    rhs: "Expression"


class Assignment(ExprNode):
    lhs: "Expression"
    operator: AssignmentOperator
    rhs: "Expression"

    def __init__(
        self, lhs: "Expression", operator: AssignmentOperator, rhs: "Expression"
    ):
        super().__init__()
        self.lhs = lhs
        self.operator = operator
        self.rhs = rhs

    def serialize(self) -> str:
        return f"{self.lhs.serialize()} {self.operator.value} {self.rhs.serialize()}"


class FunctionCall(ExprNode):
    arguments: list["Expression"]
    expression: "Expression"
    kind: FunctionCallKind
    names: list[str]
    type_descriptions: TypeDescriptions
    try_call: bool


class FunctionCallOptions(ExprNode):
    expression: "Expression"
    names: list[str]
    options: list["Expression"]


class IndexAccess(ExprNode):
    base_expression: "Expression"
    index_expression: Optional["Expression"]


class IndexRangeAccess(ExprNode):
    base_expression: "Expression"
    end_expression: Optional["Expression"]
    start_expression: Optional["Expression"]


class MemberAccess(ExprNode):
    expression: "Expression"
    member_name: str
    referenced_declaration: Optional[int]


class Literal(ExprNode):
    hex_value: str
    kind: LiteralKind
    subdenomination: Optional[str]
    value: Optional[str]


class NewExpression(ExprNode):
    type_name: "TypeName"


class TupleExpression(ExprNode):
    components: list["Expression"]
    is_inline_array: bool


class UnaryOperation(ExprNode):
    operator: UnaryOperator
    prefix: bool
    sub_expression: "Expression"


class ArrayTypeName(AstNode):
    type_descriptions: TypeDescriptions
    base_type: "TypeName"
    length: Optional[Expression]


class OverrideSpecifier(AstNode):
    overrides: list[UserDefinedTypeNameOrIdentifierPath]


class VariableDeclaration(AstNode):
    name: str
    name_location: Optional[SourceLocation]
    base_functions: list[int]
    constant: bool
    state_variable: bool
    documentation: Optional[StructuredDocumentation]
    function_selector: Optional[str]
    indexed: bool
    _mutability: Optional[Mutability]
    overrides: Optional[OverrideSpecifier]
    scope: AstId
    storage_location: StorageLocation
    type_descriptions: TypeDescriptions
    type_name: Optional["TypeName"]
    value: Optional[Expression]
    visibility: Visibility

    @property
    def mutability(self) -> Mutability:
        if self.mutability:
            return self.mutability
        if self.constant:
            return Mutability.Constant
        if self.state_variable:
            return Mutability.Mutable
        raise Unreachable()


class ParameterList:
    parameters: list[VariableDeclaration]


class FunctionTypeName(AstNode):
    type_descriptions: TypeDescriptions
    parameter_types: ParameterList
    return_parameter_types: ParameterList
    visibility: Visibility


class Mapping(AstNode):
    type_descriptions: TypeDescriptions
    key_type: "TypeName"
    value_type: "TypeName"


class UsingForDirective(AstNode):
    function_list: list[FunctionIdentifierPath]
    global_: bool
    library_name: Optional[UserDefinedTypeNameOrIdentifierPath]
    type_name: Optional[TypeName]


class SourceUnit(AstNode):
    absolute_path: Optional[str]
    exported_symbols: dict[str, list[AstId]]
    license: Optional[str]
    nodes: list["SourceUnitPart"]


class EnumValue(AstNode):
    name: str
    name_location: Optional[SourceLocation]


class EnumDefinition(AstNode):
    name: str
    name_location: Optional[SourceLocation]
    canonical_name: str
    members: list[EnumValue]


class ErrorDefinition(AstNode):
    name: str
    name_location: Optional[SourceLocation]
    documentation: Optional[StructuredDocumentation]
    error_selector: Optional[str]
    parameters: ParameterList


class EventDefinition(AstNode):
    name: str
    name_location: Optional[SourceLocation]
    anonymous: bool
    event_selector: Optional[str]
    documentation: Optional[StructuredDocumentation]
    parameters: ParameterList


class StmtNode(AstNode):
    documentation: Optional[str]


class Block(StmtNode):
    statements: Sequence["Statement"]

    def __init__(self, *statements: "Statement"):
        super().__init__()
        self.statements = statements

    def serialize(self) -> str:
        return line_join(wrap_block(self.statements))


class Break(StmtNode):
    pass


class Continue(StmtNode):
    pass


class DoWhileStatement(StmtNode):
    block: Block
    condition: Expression


class EmitStatement(StmtNode):
    event_call: FunctionCall


class ExpressionStatement(StmtNode):
    expression: Expression


class ForStatement(StmtNode):
    body: "Statement"
    condition: Optional[Expression]
    initialization_expression: Optional["ExpressionOrVariableDeclarationStatement"]
    loop_expression: Optional[ExpressionStatement]


class VariableDeclarationStatement(StmtNode):
    assignments: list[Optional[int]]
    declarations: list[Optional[VariableDeclaration]]
    initial_value: Optional[Expression]


class IfStatement(StmtNode):
    condition: Expression
    false_body: Optional["Statement"]
    true_body: "Statement"


class YulBlock(StmtNode):
    statements: Sequence["YulStatement"]

    def __init__(self, *statements: "YulStatement"):
        self.statements = statements

    def serialize(self) -> str:
        return line_join(wrap_block(self.statements))


class YulIdentifier(AstNode):
    name: str

    def __init__(self, name: str):
        self.name = name

    def serialize(self) -> str:
        return self.name


class YulKeyword(StmtNode):
    pass


class YulContinue(YulKeyword):
    pass


class YulBreak(YulKeyword):
    pass


class YulLeave(YulKeyword):
    pass


class YulLiteral(AstNode):
    hex_value: Optional[str]
    value: Optional[str]
    kind: YulLiteralKind
    type_name: Optional[str]


class YulAssignment(StmtNode):
    value: "YulExpression"
    variable_name: list[YulIdentifier]


class YulExpressionStatement(StmtNode):
    expression: "YulExpression"


class YulForLoop(StmtNode):
    body: YulBlock
    condition: "YulExpression"
    post: YulBlock
    pre: YulBlock


class YulTypedName(AstNode):
    name: str
    type_name: str


class YulFunctionDefinition(StmtNode):
    body: YulBlock
    name: str
    parameters: list[YulTypedName]
    return_variables: list[YulTypedName]


class YulIf(StmtNode):
    body: YulBlock
    condition: "YulExpression"


class YulCase(AstNode):
    body: YulBlock
    value: "YulCaseValue"


class YulSwitch(StmtNode):
    cases: list["YulCase"]
    expression: "YulExpression"


class YulVariableDeclaration(StmtNode):
    value: Optional["YulExpression"]
    variables: list[YulTypedName]


class YulFunctionCall(AstNode):
    arguments: list["YulExpression"]
    function_name: YulIdentifier

    def __init__(self, name: YulIdentifier, arguments: list["YulExpression"] = []):
        self.function_name = name
        self.arguments = arguments

    def serialize(self) -> str:
        return f"{self.function_name.name}({', '.join(arg.serialize() for arg in self.arguments)})"


def yulFunction(
    name: YulIdentifier, numArgs: int
) -> Callable[["YulExpression"], YulFunctionCall]:
    def f(*args: "YulExpression") -> YulFunctionCall:
        if len(args) != numArgs:
            raise ValueError(f"Expected {numArgs} arguments, got {len(args)}")
        return YulFunctionCall(arguments=list(args), name=name)

    return f


call = yulFunction(YulIdentifier("call"), 7)


class ExternalInlineAssemblyReference(AstNode):
    declaration: AstId
    offset: bool
    slot: bool
    length: bool
    value_size: AstId
    suffix: Optional[AssemblyReferenceSuffix]


class InlineAssembly(StmtNode):
    ast: YulBlock
    external_references: list[ExternalInlineAssemblyReference]
    flags: list[InlineAssemblyFlag]


class PlaceholderStatement(StmtNode):
    def serialize(self) -> str:
        return "_"

    pass


class Return(StmtNode):
    expression: Optional[Expression]
    function_return_parameters: AstId


class RevertStatement(StmtNode):
    error_call: FunctionCall


class TryCatchClause(AstNode):
    block: Block
    error_name: str
    parameters: list[ParameterList]


class TryStatement(StmtNode):
    clauses: list[TryCatchClause]
    external_call: FunctionCall


class UncheckedBlock(StmtNode):
    statements: list["Statement"]


class WhileStatement(StmtNode):
    body: "Statement"
    condition: Expression


class ModifierInvocation(AstNode):
    arguments: list[Expression]
    kind: Optional[ModifierInvocationKind]
    modifier_name: IdentifierOrIdentifierPath


class FunctionDefinition(AstNode):
    name: str
    name_location: Optional[SourceLocation]
    base_functions: list[int]
    body: Optional[Block]
    documentation: Optional[StructuredDocumentation]
    function_selector: Optional[str]
    implemented: bool
    modifiers: list[ModifierInvocation]
    overrides: Optional[OverrideSpecifier]
    parameters: ParameterList
    return_parameters: ParameterList
    scope: AstId
    visibility: Visibility
    _kind: Optional[FunctionKind]
    _state_mutability: Optional[StateMutability]
    is_virtual: bool
    is_constructor: bool
    is_declared_const: bool
    is_payable: bool

    @property
    def kind(self) -> FunctionKind:
        if self._kind:
            return self._kind
        if self.is_constructor:
            return FunctionKind.Constructor
        return FunctionKind.Function

    @property
    def state_mutability(self):
        if self._state_mutability:
            return self._state_mutability
        if self.is_payable:
            return StateMutability.Payable
        if self.is_declared_const:
            return StateMutability.View
        return StateMutability.Nonpayable


class StructDefinition(AstNode):
    name: str
    name_location: Optional[SourceLocation]
    canonical_name: str
    members: list[VariableDeclaration]
    scope: AstId
    visibility: Visibility


class UserDefinedValueTypeDefinition(AstNode):
    name: str
    name_location: Optional[SourceLocation]
    canonical_name: str
    underlying_type: TypeName


class InheritanceSpecifier(AstNode):
    arguments: list[Expression]
    base_name: UserDefinedTypeNameOrIdentifierPath


class ContractDefinition(AstNode):
    name: str
    name_location: Optional[SourceLocation]
    is_abstract: bool
    base_contracts: list[InheritanceSpecifier]
    canonical_name: Optional[str]
    contract_dependencies: list[int]
    kind: ContractKind
    documentation: Optional[StructuredDocumentation]
    fully_implemented: bool
    nodes: list["ContractDefinitionPart"]
    scope: AstId
    used_errors: list[int]
    used_events: list[int]
    internal_function_ids: dict[int, int]


class ModifierDefinition(AstNode):
    name: str
    name_location: Optional[SourceLocation]
    base_modifiers: list[int]
    body: Block
    documentation: Optional[StructuredDocumentation]
    overrides: Optional[OverrideSpecifier]
    parameters: ParameterList
    is_virtual: bool
    visibility: Visibility


# class SolidityExpression(str):
#     pass

# class YulExpression(SolidityExpression):
#     pass

# class Value(str):
#     pass

# class Variable(str):
#     pass

# class SolidityDeclaration(Variable):
#     pass

# class YulDeclaration(Variable):
#     pass

# class Member(SolidityExpression):
#     pass

# class Immutable(Member):
#     pass


# Expression = TypeVar("Expression", bound=SolidityExpression)
# Text = TypeVar("Text", bound=str)
# Var = TypeVar("Var", bound=Variable)

# def shl(a: str, b: str) -> YulExpression:
#     return YulExpression(f'shl({a}, {b})')

# def shr(a: str, b: str) -> YulExpression:
#     return YulExpression(f'shr({a}, {b})')

# def _or(a: str, b: str) -> YulExpression:
#     return YulExpression(f'or({a}, {b})')

# def _and(a: str, b: str) -> YulExpression:
#     return YulExpression(f'and({a}, {b})')

# def gt(a: str, b: str) -> YulExpression:
#     return YulExpression(f'gt({a}, {b})')

# def lt(a: str, b: str) -> YulExpression:
#     return YulExpression(f'lt({a}, {b})')

# def mul(a: str, b: str) -> YulExpression:
#     return YulExpression(f'mul({a}, {b})')

# def div(a: str, b: str) -> YulExpression:
#     return YulExpression(f'div({a}, {b})')

# def assign(a: Variable, b: Expression) -> Expression:
#     if isinstance(b, SolidityExpression):
#         return b.__class__(f'{a} = {b};')
#     else:
#         return b.__class__(f'{a} := {b}')

# def iszero(a: str) -> YulExpression:
#     return YulExpression(f'iszero({a})')

# def body(*exprs:SolidityExpression) -> SolidityExpression:
#     return SolidityExpression(line_joiner(*exprs))

# def assembly(*exprs: YulExpression) -> SolidityExpression:
#     return SolidityExpression(line_joiner("assembly {", *exprs, "}"))

# def unchecked(expr: SolidityExpression) -> SolidityExpression:
#     return SolidityExpression(line_joiner("unchecked {", expr, "}"))

# def line_joiner(*args: str) -> str:
#     return "\n".join(x for x in args if x)


# def contract(name: str, body:list[str]=[], inheritance: list[str] = []):
#     """Wrap lines in a contract"""
#     inheritance_str = f"is {', '.join(inheritance)}" if inheritance else ""
#     return line_joiner(f"contract {name} {inheritance_str} {{", *body, "}")

# def file(license:str, pragma: str, *contents)

# def library(name, *body):
#     """Wrap lines in a library"""
#     return line_joiner(f"library {name} {{", *body, "}")


# c = contract(
#     "MyCoolContract",
#     inheritance=["MyCoolInterface"],
#     "uint256 public myCoolNumber;"
# )
# print(c)
