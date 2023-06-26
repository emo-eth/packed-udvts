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
from sol_ast.utils import line_join, wrap_block, NodeDictChecker, StatementChecker
from functools import partial


class Unreachable(ValueError):
    pass


ElementaryOrRawTypeName: TypeAlias = "ElementaryTypeName"
UserDefinedTypeNameOrIdentifierPath: TypeAlias = Union[
    "UserDefinedTypeName", "IdentifierPath"
]
Expression: TypeAlias = Union[
    "Assignment",
    "BinaryOperation",
    "TernaryConditional",
    "ElementaryTypeNameExpression",
    "FunctionCall",
    # "FunctionCallOption",
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

YulExpression: TypeAlias = Union[
    "YulFunctionCall",
    "YulIdentifier",
    "YulLiteral",
]

ExpressionOrVariableDeclarationStatement: TypeAlias = Union[
    "ExpressionStatement", "VariableDeclarationStatement"
]

StatementType: TypeAlias = Union[
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

BlockType: TypeAlias = Union[
    "Block",
    "UncheckedBlock",
    "InlineAssembly",
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


class AstNode(metaclass=NodeDictChecker):
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
    def fmt(self) -> str:
        pass


class TypeDescriptions:
    """TODO: idk what that is"""

    type_identifier: Optional[str]
    type_string: Optional[str]


class ExprNode(AstNode):
    """Base class for all expression nodes"""

    argument_types: list[TypeDescriptions]
    is_constant: bool
    is_l_value: bool
    is_pure: bool
    l_value_requested: bool
    type_descriptions: Optional[TypeDescriptions]


class Identifier(AstNode):
    argument_types: list[TypeDescriptions]
    name: str
    overloaded_declarations: list[int]
    referenced_declaration: Optional[int]
    type_descriptions: Optional[TypeDescriptions]

    def __init__(
        self,
        name: str,
        referenced_declaration: Optional[int] = None,
        overloaded_declarations: list[int] = [],
        type_descriptions: Optional[TypeDescriptions] = None,
        argument_types: list[TypeDescriptions] = [],
    ):
        super().__init__()
        self.name = name
        self.referenced_declaration = referenced_declaration
        self.overloaded_declarations = overloaded_declarations
        self.type_descriptions = type_descriptions
        self.argument_types = argument_types

    def to_yul_identifier(self) -> "YulIdentifier":
        return YulIdentifier(self.name)

    def to_identifier_path(self) -> "IdentifierPath":
        return IdentifierPath(self.name)

    def fmt(self) -> str:
        return self.name


class SymbolAlias(AstNode):
    """SymbolAlias is an alias to an imported symbol, which may declare a local name for it, e.g.:
    import { foo as bar, baz } from "baz" - "foo as bar"  and "baz" are both SymbolAlias nodes.
    "foo" and "baz" are the "foreign" Identifiers, "bar" is the "local" name
    """

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

    def fmt(self) -> str:
        if self.local is None:
            return self.foreign.fmt()
        else:
            return f"{self.foreign.fmt()} as {self.local}"


class PragmaDirective(AstNode):
    literals: list[str]

    def __init__(self, literals: list[str]):
        super().__init__()
        self.literals = literals

    def fmt(self) -> str:
        return f"pragma {self.literals[0]} {self.literals[1]}"


class ImportDirective(AstNode):
    absolute_path: str
    file: str
    name_location: Optional[SourceLocation]
    scope: AstId
    source_unit: AstId
    symbol_aliases: list[SymbolAlias]
    unit_alias: str

    def __init__(
        self,
        absolute_path: str,
        file: str,
        name_location: Optional[SourceLocation] = None,
        scope: Optional[AstId] = None,
        source_unit: Optional[AstId] = None,
        symbol_aliases: list[SymbolAlias] = [],
        unit_alias: str = "",
    ):
        super().__init__()
        self.absolute_path = absolute_path
        self.file = file
        self.name_location = name_location
        self.scope = scope or AstId(randint(0, 2**64))
        self.source_unit = source_unit or AstId(randint(0, 2**64))
        self.symbol_aliases = symbol_aliases
        self.unit_alias = unit_alias

    def fmt(self) -> str:
        from_clause = (
            f'{{{", ".join([s.fmt() for s in self.symbol_aliases])} from}}'
            if self.symbol_aliases
            else ""
        )
        return f"import {from_clause} {self.absolute_path};"


class IdentifierPath(AstNode):
    name: str
    referenced_declaration: Optional[AstId]

    def __init__(self, name: str, referenced_declaration: Optional[AstId] = None):
        super().__init__()
        self.name = name
        self.referenced_declaration = referenced_declaration

    def fmt(self) -> str:
        return self.name


class FunctionIdentifierPath:
    function: IdentifierPath

    def __init__(self, function: IdentifierPath):
        self.function = function

    def fmt(self) -> str:
        return self.function.fmt()


class UserDefinedTypeName(AstNode):
    type_descriptions: Optional[TypeDescriptions]
    contract_scope: Optional[str]
    name: str
    path_node: Optional[IdentifierPath]
    referenced_declaration: Optional[AstId]

    def __init__(
        self,
        name: str,
        type_descriptions: Optional[TypeDescriptions] = None,
        contract_scope: Optional[str] = None,
        path_node: Optional[IdentifierPath] = None,
        referenced_declaration: Optional[AstId] = None,
    ):
        super().__init__()
        self.name = name
        self.type_descriptions = type_descriptions
        self.contract_scope = contract_scope
        self.path_node = path_node
        self.referenced_declaration = referenced_declaration

    def fmt(self) -> str:
        return self.name


class TernaryConditional(ExprNode):
    condition: "Expression"
    false_expression: "Expression"
    true_expression: "Expression"

    def __init__(
        self,
        condition: "Expression",
        false_expression: "Expression",
        true_expression: "Expression",
    ):
        super().__init__()
        self.condition = condition
        self.false_expression = false_expression
        self.true_expression = true_expression

    def fmt(self) -> str:
        return f"{self.condition.fmt()} ? {self.true_expression.fmt()} : {self.false_expression.fmt()}"


class ElementaryTypeName(AstNode):
    type_descriptions: Optional[TypeDescriptions]
    name: str
    state_mutability: Optional[StateMutability]

    def __init__(
        self,
        name: str,
        type_descriptions: Optional[TypeDescriptions] = None,
        state_mutability: Optional[StateMutability] = None,
    ):
        super().__init__()
        self.name = name
        self.type_descriptions = type_descriptions
        self.state_mutability = state_mutability

    def fmt(self) -> str:
        if self.state_mutability is None:
            return self.name
        else:
            return f"{self.name} {self.state_mutability.value}"


class ElementaryTypeNameExpression(ExprNode):
    type_name: ElementaryOrRawTypeName

    def __init__(self, type_name: ElementaryOrRawTypeName):
        super().__init__()
        self.type_name = type_name

    def fmt(self) -> str:
        return self.type_name.fmt()


class BinaryOperation(AstNode):
    common_type: Optional[TypeDescriptions]
    lhs: "Expression"
    operator: BinaryOperator
    rhs: "Expression"

    def __init__(
        self,
        lhs: "Expression",
        operator: BinaryOperator,
        rhs: "Expression",
        common_type: Optional[TypeDescriptions] = None,
    ):
        super().__init__()
        self.lhs = lhs
        self.operator = operator
        self.rhs = rhs
        self.common_type = common_type

    def fmt(self) -> str:
        return f"({self.lhs.fmt()}) {self.operator.value} {self.rhs.fmt()}"


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

    def fmt(self) -> str:
        return f"{self.lhs.fmt()} {self.operator.value} {self.rhs.fmt()}"


class FunctionCallOption(AstNode):
    name: str
    value: "Expression"

    def __init__(self, name: str, value: "Expression"):
        self.name = name
        self.value = value

    def fmt(self) -> str:
        return f"{self.name}: {self.value.fmt()}"


class FunctionCall(ExprNode):
    arguments: list["Expression"]
    expression: "Expression"
    kind: FunctionCallKind
    names: list[str]
    options: list[FunctionCallOption]
    type_descriptions: Optional[TypeDescriptions]
    try_call: bool

    def __init__(
        self,
        expression: "Expression",
        kind: FunctionCallKind,
        arguments: list["Expression"] = [],
        names: list[str] = [],
        options: list[FunctionCallOption] = [],
        type_descriptions: Optional[TypeDescriptions] = None,
        try_call: bool = False,
    ):
        super().__init__()
        if names is not None:
            assert arguments is not None and len(arguments) == len(
                names
            ), "names and arguments must have the same length"
        self.arguments = arguments
        self.expression = expression
        self.kind = kind
        self.names = names
        self.options = options
        self.type_descriptions = type_descriptions
        self.try_call = try_call

    def fmt(self) -> str:
        options_str = ""
        if self.options:
            options_str = f'{{{", ".join([option.fmt() for option in self.options])}}}'

        if self.names is None:
            args_str = f"({', '.join([arg.fmt() for arg in self.arguments])})"
        else:
            args_str = f"{{{', '.join(f'{name}: {arg.fmt()}' for name, arg in zip(self.names, self.arguments))}}}"
        return f"{self.expression.fmt()}{options_str}({args_str})"


# class FunctionCallOptions(ExprNode):
#     expression: "Expression"
#     names: list[str]
#     options: list["Expression"]

#     def __init__(
#         self, expression: "Expression", names: list[str], options: list["Expression"]
#     ):
#         super().__init__()
#         self.expression = expression
#         self.names = names
#         self.options = options

#     def fmt(self) -> str:
#         return f"{self.expression.fmt()}({{{', '.join([f'{name}: {option.fmt()}' for name, option in zip(self.names, self.options)])}}})"


class IndexAccess(ExprNode):
    base_expression: "Expression"
    index_expression: "Expression"

    def __init__(self, base_expression: "Expression", index_expression: "Expression"):
        super().__init__()
        self.base_expression = base_expression
        self.index_expression = index_expression

    def fmt(self) -> str:
        return f"({self.base_expression.fmt()})[{self.index_expression.fmt()}]"


class IndexRangeAccess(ExprNode):
    base_expression: "Expression"
    end_expression: Optional["Expression"]
    start_expression: Optional["Expression"]

    def __init__(
        self,
        base_expression: "Expression",
        start_expression: Optional["Expression"] = None,
        end_expression: Optional["Expression"] = None,
    ):
        super().__init__()
        assert (
            start_expression is not None or end_expression is not None
        ), "Either start_expression or end_expression must be provided"
        self.base_expression = base_expression
        self.start_expression = start_expression
        self.end_expression = end_expression

    def fmt(self) -> str:
        start_expr = ""
        end_expr = ""
        if self.start_expression is not None:
            start_expr = self.start_expression.fmt()
        if self.end_expression is not None:
            end_expr = self.end_expression.fmt()
        return f"{self.base_expression.fmt()}[{start_expr}:{end_expr}]"


class MemberAccess(ExprNode):
    expression: "Expression"
    member_name: str
    referenced_declaration: Optional[int]

    def __init__(
        self,
        expression: "Expression",
        member_name: str,
        referenced_declaration: Optional[int] = None,
    ):
        super().__init__()
        self.expression = expression
        self.member_name = member_name
        self.referenced_declaration = referenced_declaration

    def fmt(self) -> str:
        return f"{self.expression.fmt()}.{self.member_name}"


class Literal(ExprNode):
    # hex_value: str
    kind: LiteralKind
    subdenomination: Optional[str]
    value: str

    def __init__(
        self,
        value: str,
        kind: LiteralKind = LiteralKind.Number,
        subdenomination: Optional[str] = None,
    ):
        super().__init__()
        self.kind = kind
        self.subdenomination = subdenomination
        self.value = value

    def to_yul_literal(self) -> "YulLiteral":
        if self.kind == LiteralKind.String:
            return YulLiteral(self.value, YulLiteralKind.String)
        elif self.kind == LiteralKind.HexString:
            return YulLiteral(self.value, YulLiteralKind.String)
        elif self.kind == LiteralKind.UnicodeString:
            raise ValueError("UnicodeString not supported for yul literals")
        elif self.kind == LiteralKind.Bool:
            return YulLiteral(self.value, YulLiteralKind.Bool)
        return YulLiteral(self.value, YulLiteralKind.Number)

    def fmt(self) -> str:
        if self.kind == LiteralKind.String:
            return f'"{self.value}"'  # TODO: handle escapes
        elif self.kind == LiteralKind.HexString:
            return f'hex"{self.value}"'
        elif self.kind == LiteralKind.UnicodeString:
            return f'unicode"{self.value}"'
        elif self.kind == LiteralKind.Number:
            suffix = self.subdenomination or ""
            return f"{self.value} {suffix}"
        return self.value


class NewExpression(ExprNode):
    type_name: "TypeName"


class TupleExpression(ExprNode):
    components: list["Expression"]
    is_inline_array: bool

    def __init__(self, components: list["Expression"], is_inline_array: bool = False):
        super().__init__()
        self.components = components
        self.is_inline_array = is_inline_array

    def fmt(self) -> str:
        if self.is_inline_array:
            return f"[{', '.join([component.fmt() for component in self.components])}]"
        else:
            return f"({', '.join([component.fmt() for component in self.components])})"


class UnaryOperation(ExprNode):
    operator: UnaryOperator
    prefix: bool
    sub_expression: "Expression"

    def __init__(
        self, operator: UnaryOperator, prefix: bool, sub_expression: "Expression"
    ):
        super().__init__()
        self.operator = operator
        self.prefix = prefix
        self.sub_expression = sub_expression

    def fmt(self) -> str:
        if self.prefix:
            return f"{self.operator.value}({self.sub_expression.fmt()})"
        else:
            return f"({self.sub_expression.fmt()}){self.operator.value}"


class ArrayTypeName(AstNode):
    type_descriptions: Optional[TypeDescriptions]
    base_type: "TypeName"
    length: Optional[Expression]

    def __init__(self, base_type: "TypeName", length: Optional[Expression] = None):
        super().__init__()
        self.base_type = base_type
        self.length = length

    def fmt(self) -> str:
        if self.length is None:
            return f"{self.base_type.fmt()}[]"
        else:
            return f"{self.base_type.fmt()}[{self.length.fmt()}]"


class OverrideSpecifier(AstNode):
    overrides: list[UserDefinedTypeNameOrIdentifierPath]

    def __init__(self, overrides: list[UserDefinedTypeNameOrIdentifierPath]):
        super().__init__()
        self.overrides = overrides

    def fmt(self) -> str:
        return f"override({', '.join([override.fmt() for override in self.overrides])})"


class VariableDeclaration(AstNode):
    name: Optional[str]
    name_location: Optional[SourceLocation]
    base_functions: list[AstId]
    constant: bool
    state_variable: bool
    documentation: Optional[StructuredDocumentation]
    function_selector: Optional[str]
    indexed: bool
    _mutability: Optional[Mutability]
    overrides: Optional[OverrideSpecifier]
    scope: Optional[AstId]
    storage_location: Optional[StorageLocation]
    type_descriptions: Optional[TypeDescriptions]
    type_name: "TypeName"
    value: Optional[Expression]
    visibility: Visibility

    def __init__(
        self,
        type_name: "TypeName",
        name: Optional[str],
        name_location: Optional[SourceLocation] = None,
        base_functions: list[AstId] = [],
        constant: bool = False,
        state_variable: bool = False,
        documentation: Optional[StructuredDocumentation] = None,
        function_selector: Optional[str] = None,
        indexed: bool = False,
        mutability: Optional[Mutability] = None,
        overrides: Optional[OverrideSpecifier] = None,
        scope: Optional[AstId] = None,
        storage_location: Optional[StorageLocation] = None,
        type_descriptions: Optional[TypeDescriptions] = None,
        value: Optional[Expression] = None,
        visibility: Visibility = Visibility.Internal,
    ):
        super().__init__()
        self.name = name
        self.name_location = name_location
        self.base_functions = base_functions
        self.constant = constant
        self.state_variable = state_variable
        self.documentation = documentation
        self.function_selector = function_selector
        self.indexed = indexed
        self._mutability = mutability
        self.overrides = overrides
        self.scope = scope
        self.storage_location = storage_location
        self.type_descriptions = type_descriptions
        self.type_name = type_name
        self.value = value
        self.visibility = visibility

    @property
    def mutability(self) -> Mutability:
        if self.mutability:
            return self.mutability
        if self.constant:
            return Mutability.Constant
        if self.state_variable:
            return Mutability.Mutable
        raise Unreachable()

    def fmt(self) -> str:
        qualifier = self.indexed or self.storage_location or self.mutability
        return f"{self.type_name.fmt()} {qualifier} {self.name or ''}"


class ParameterList:
    parameters: list[VariableDeclaration]

    def __init__(self, *parameters: VariableDeclaration):
        super().__init__()
        self.parameters = list(parameters)

    def fmt(self) -> str:
        return f"({', '.join([parameter.fmt() for parameter in self.parameters])})"


class FunctionTypeName(AstNode):
    type_descriptions: Optional[TypeDescriptions]
    parameter_types: ParameterList
    return_parameter_types: ParameterList
    visibility: Visibility

    def __init__(
        self,
        parameter_types: ParameterList,
        return_parameter_types: ParameterList,
        visibility: Visibility = Visibility.Internal,
    ):
        super().__init__()
        self.parameter_types = parameter_types
        self.return_parameter_types = return_parameter_types
        self.visibility = visibility

    def fmt(self) -> str:
        returns_clause = (
            f"returns ({self.return_parameter_types.fmt()})"
            if self.return_parameter_types
            else ""
        )
        return f"function ({self.parameter_types.fmt()}) {self.visibility.value} {returns_clause}"


class Mapping(AstNode):
    type_descriptions: Optional[TypeDescriptions]
    key_type: "TypeName"
    value_type: "TypeName"


class UsingForDirective(AstNode):
    function_list: list[FunctionIdentifierPath]
    global_: bool
    library_name: Optional[UserDefinedTypeNameOrIdentifierPath]
    type_name: Optional[TypeName]

    def __init__(
        self,
        function_list: list[FunctionIdentifierPath] = [],
        global_: bool = False,
        library_name: Optional[UserDefinedTypeNameOrIdentifierPath] = None,
        type_name: Optional[TypeName] = None,
    ):
        super().__init__()
        self.function_list = function_list
        self.global_ = global_
        self.library_name = library_name
        self.type_name = type_name

    def fmt(self) -> str:
        if self.library_name is None:
            using_clause = f"using {', '.join([function.fmt() for function in self.function_list])}"
        else:
            using_clause = f"using {self.library_name.fmt()}"
        if self.type_name is None:
            for_clause = "for *"
        else:
            for_clause = f"for {self.type_name.fmt()}"
        global_clause = "global;" if self.global_ else ";"
        return f"{using_clause} {for_clause} {global_clause}"


class SourceUnit(AstNode):
    absolute_path: Optional[str]
    exported_symbols: dict[str, list[AstId]]
    license: Optional[str]
    nodes: list["SourceUnitPart"]

    def __init__(
        self,
        *nodes: "SourceUnitPart",
        absolute_path: Optional[str] = None,
        exported_symbols: dict[str, list[AstId]] = {},
        license: Optional[str] = None,
    ):
        super().__init__()
        self.absolute_path = absolute_path
        self.exported_symbols = exported_symbols
        self.license = license
        self.nodes = list(nodes)

    def fmt(self) -> str:
        return "\n".join(node.fmt() for node in self.nodes)


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


class Statement(AstNode, metaclass=StatementChecker):
    pass


class Block(StmtNode):
    statements: list[BlockType]

    def __init__(self, *statements: BlockType):
        super().__init__()
        self.statements = list(statements)

    def fmt(self) -> str:
        return line_join(wrap_block(self.statements, semicolon=True))


class Break(Statement):
    pass


class Continue(Statement):
    pass


class DoWhileStatement(Statement):
    block: Block
    condition: Expression

    def __init__(self, block: Block, condition: Expression):
        super().__init__()
        self.block = block
        self.condition = condition

    def fmt(self) -> str:
        return f"do {self.block.fmt()} while ({self.condition.fmt()})"


class EmitStatement(Statement):
    event_call: FunctionCall

    def __init__(self, event_call: FunctionCall):
        super().__init__()
        self.event_call = event_call

    def fmt(self) -> str:
        return f"emit {self.event_call.fmt()};"


class ExpressionStatement(Statement):
    expression: Expression

    def __init__(self, expression: Expression):
        super().__init__()
        self.expression = expression

    def fmt(self) -> str:
        return self.expression.fmt() + ";"


class ForStatement(Statement):
    body: BlockType
    condition: Optional[Expression]
    initialization_expression: Optional["ExpressionOrVariableDeclarationStatement"]
    loop_expression: Optional[ExpressionStatement]

    def __init__(
        self,
        body: BlockType,
        condition: Optional[Expression] = None,
        initialization_expression: Optional[
            "ExpressionOrVariableDeclarationStatement"
        ] = None,
        loop_expression: Optional[ExpressionStatement] = None,
    ):
        super().__init__()
        self.body = body
        self.condition = condition
        self.initialization_expression = initialization_expression
        self.loop_expression = loop_expression

    def fmt(self) -> str:
        if self.initialization_expression is None:
            initialization = ""
        else:
            initialization = self.initialization_expression.fmt()

        if self.condition is None:
            condition = ""
        else:
            condition = self.condition.fmt()

        if self.loop_expression is None:
            loop_expression = ""
        else:
            loop_expression = self.loop_expression.fmt()
        return (
            f"for ({initialization}; {condition}; {loop_expression}) {self.body.fmt()}"
        )


class VariableDeclarationStatement(Statement):
    assignments: Optional[list[AstId]]
    declarations: Optional[list[VariableDeclaration]]
    initial_value: Optional[Expression]

    def __init__(
        self,
        assignments: Optional[list[AstId]],
        declarations: Optional[list[VariableDeclaration]],
        initial_value: Optional[Expression],
    ):
        super().__init__()
        if assignments is None and declarations is None:
            raise ValueError("Either assignments or declarations must be provided")
        if assignments is not None and declarations is not None:
            raise ValueError("Only one of assignments or declarations can be provided")
        if not len(assignments or declarations):  # type: ignore
            raise ValueError("Either assignments or declarations must be non-empty")
        if initial_value is None and declarations is None:
            raise ValueError("Either assignments or declarations must be provided")
        self.assignments = assignments
        self.declarations = declarations
        self.initial_value = initial_value

    def fmt(self) -> str:
        lhs = ""
        if self.assignments is not None:
            lhs = ", ".join(self.d[a].fmt() for a in self.assignments)
        elif self.declarations is not None:
            lhs = ", ".join(d.fmt() for d in self.declarations)
        rhs = ""
        if self.initial_value is not None:
            rhs = f" = ({self.initial_value.fmt()})"
        return f"{lhs}{rhs};"


class IfStatement(Statement):
    condition: Expression
    false_body: Optional[BlockType]
    true_body: BlockType


class YulBlock(StmtNode):
    statements: Sequence["YulStatement"]

    def __init__(self, *statements: "YulStatement"):
        self.statements = statements

    def fmt(self) -> str:
        return line_join(wrap_block(self.statements, semicolon=False))


class YulIdentifier(AstNode):
    name: str

    def __init__(self, name: str):
        self.name = name

    def fmt(self) -> str:
        return self.name


class YulKeyword(StmtNode):
    pass


class YulContinue(YulKeyword):
    def fmt(self) -> str:
        return "continue"


class YulBreak(YulKeyword):
    def fmt(self) -> str:
        return "break"


class YulLeave(YulKeyword):
    def fmt(self) -> str:
        return "leave"


class YulLiteral(AstNode):
    value: str
    kind: YulLiteralKind
    type_name: Optional[str]

    def __init__(
        self,
        value: str,
        kind: YulLiteralKind = YulLiteralKind.Number,
        type_name: Optional[str] = None,
    ):
        super().__init__()
        self.kind = kind
        self.value = value
        self.type_name = type_name

    def fmt(self) -> str:
        return self.value


class YulAssignment(StmtNode):
    value: "YulExpression"
    variables: list[YulIdentifier]

    def __init__(
        self,
        *variables: YulIdentifier,
        value: "YulExpression",
    ):
        super().__init__()
        self.value = value
        self.variables = list(variables)

    def fmt(self) -> str:
        return f"{', '.join(v.fmt() for v in self.variables)} := {self.value.fmt()}"


class YulExpressionStatement(StmtNode):
    expression: "YulExpression"

    def __init__(self, expression: "YulExpression"):
        super().__init__()
        self.expression = expression

    def fmt(self) -> str:
        return self.expression.fmt()


class YulForLoop(StmtNode):
    body: YulBlock
    condition: "YulExpression"
    post: YulBlock
    pre: YulBlock

    def __init__(
        self,
        body: YulBlock,
        condition: "YulExpression",
        post: YulBlock,
        pre: YulBlock,
    ):
        super().__init__()
        self.body = body
        self.condition = condition
        self.post = post
        self.pre = pre

    def fmt(self) -> str:
        return f"for {self.pre.fmt()} {self.condition.fmt()} {self.post.fmt()} {self.body.fmt()}"


class YulTypedName(AstNode):
    name: str
    type_name: str

    def __init__(self, name: str, type_name: str):
        super().__init__()
        self.name = name
        self.type_name = type_name

    def fmt(self) -> str:
        return f"{self.name} {self.type_name}"


class YulFunctionDefinition(StmtNode):
    body: YulBlock
    name: str
    parameters: list[YulTypedName]
    return_variables: list[YulTypedName]

    def __init__(
        self,
        name: str,
        parameters: list[YulTypedName],
        return_variables: list[YulTypedName],
        body: YulBlock,
    ):
        super().__init__()
        self.name = name
        self.parameters = parameters
        self.return_variables = return_variables
        self.body = body

    def fmt(self) -> str:
        return f"function {self.name}({', '.join(p.fmt() for p in self.parameters)}) -> ({', '.join(r.fmt() for r in self.return_variables)}) {self.body.fmt()}"


class YulIf(StmtNode):
    body: YulBlock
    condition: "YulExpression"

    def __init__(self, condition: "YulExpression", body: YulBlock):
        super().__init__()
        self.condition = condition
        self.body = body

    def fmt(self) -> str:
        return f"if {self.condition.fmt()} {self.body.fmt()}"


class YulCase(AstNode):
    body: YulBlock
    value: "YulCaseValue"

    def __init__(self, value: "YulCaseValue", body: YulBlock):
        super().__init__()
        self.value = value
        self.body = body

    def fmt(self) -> str:
        return f"case {self.value.fmt() if isinstance(self.value, YulLiteral) else self.value} {self.body.fmt()}"


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

    def fmt(self) -> str:
        return f"{self.function_name.name}({', '.join(arg.fmt() for arg in self.arguments)})"


def yulFunction(
    name: YulIdentifier, numArgs: int
) -> Callable[["YulExpression"], YulFunctionCall]:
    def f(*args: "YulExpression") -> YulFunctionCall:
        if len(args) != numArgs:
            raise ValueError(f"Expected {numArgs} arguments, got {len(args)}")
        return YulFunctionCall(arguments=list(args), name=name)

    return f


# operators with no arguments
def yul_nullary(name: YulIdentifier) -> YulFunctionCall:
    return YulFunctionCall(arguments=[], name=name)


def yul_unary(name: YulIdentifier, arg: YulExpression) -> YulFunctionCall:
    return YulFunctionCall(arguments=[arg], name=name)


def yul_binary(
    name: YulIdentifier, arg1: YulExpression, arg2: YulExpression
) -> YulFunctionCall:
    return YulFunctionCall(arguments=[arg1, arg2], name=name)


yul_add = partial(yul_binary, YulIdentifier("add"))
yul_sub = partial(yul_binary, YulIdentifier("sub"))
yul_mul = partial(yul_binary, YulIdentifier("mul"))
yul_div = partial(yul_binary, YulIdentifier("div"))
yul_sdiv = partial(yul_binary, YulIdentifier("sdiv"))
yul_mod = partial(yul_binary, YulIdentifier("mod"))
yul_smod = partial(yul_binary, YulIdentifier("smod"))
yul_exp = partial(yul_binary, YulIdentifier("exp"))
yul_not = partial(yul_unary, YulIdentifier("not"))
yul_iszero = partial(yul_unary, YulIdentifier("iszero"))
yul_eq = partial(yul_binary, YulIdentifier("eq"))
yul_lt = partial(yul_binary, YulIdentifier("lt"))
yul_gt = partial(yul_binary, YulIdentifier("gt"))
yul_slt = partial(yul_binary, YulIdentifier("slt"))
yul_sgt = partial(yul_binary, YulIdentifier("sgt"))
yul_and = partial(yul_binary, YulIdentifier("and"))
yul_or = partial(yul_binary, YulIdentifier("or"))
yul_xor = partial(yul_binary, YulIdentifier("xor"))
yul_shl = partial(yul_binary, YulIdentifier("shl"))
yul_shr = partial(yul_binary, YulIdentifier("shr"))
yul_sar = partial(yul_binary, YulIdentifier("sar"))
yul_pop = partial(yul_unary, YulIdentifier("pop"))
yul_mload = partial(yul_unary, YulIdentifier("mload"))
yul_mstore = partial(yul_binary, YulIdentifier("mstore"))
yul_mstore8 = partial(yul_binary, YulIdentifier("mstore8"))
yul_sload = partial(yul_unary, YulIdentifier("sload"))
yul_sstore = partial(yul_binary, YulIdentifier("sstore"))
yul_address = partial(yul_nullary, YulIdentifier("address"))
yul_balance = partial(yul_unary, YulIdentifier("balance"))
yul_callvalue = partial(yul_nullary, YulIdentifier("callvalue"))
yul_calldataload = partial(yul_unary, YulIdentifier("calldataload"))
yul_calldatasize = partial(yul_nullary, YulIdentifier("calldatasize"))
yul_signextend = partial(yul_binary, YulIdentifier("signextend"))


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

    def __init__(
        self,
        ast: YulBlock,
        external_references: list[ExternalInlineAssemblyReference] = [],
        flags: list[InlineAssemblyFlag] = [],
    ):
        super().__init__()
        self.ast = ast
        self.external_references = external_references
        self.flags = flags

    def fmt(self) -> str:
        flag_str = (
            f'("memory-safe")' if InlineAssemblyFlag.MemorySafe in self.flags else ""
        )
        return f"assembly {flag_str} {self.ast.fmt()}"


class PlaceholderStatement(Statement):
    def fmt(self) -> str:
        return "_"


class Return(Statement):
    expression: Optional[Expression]
    function_return_parameters: AstId


class RevertStatement(Statement):
    error_call: FunctionCall


class TryCatchClause(AstNode):
    block: Block
    error_name: str
    parameters: list[ParameterList]


class TryStatement(Statement):
    clauses: list[TryCatchClause]
    external_call: FunctionCall


class UncheckedBlock(Block):
    def fmt(self) -> str:
        return f"unchecked {super().fmt()}"


class WhileStatement(Statement):
    body: BlockType
    condition: Expression

    def __init__(self, condition: Expression, body: BlockType):
        super().__init__()
        self.condition = condition
        self.body = body

    def fmt(self) -> str:
        return f"while ({self.condition.fmt()}) {self.body.fmt()}"


class ModifierInvocation(AstNode):
    arguments: list[Expression]
    kind: Optional[ModifierInvocationKind]
    modifier_name: IdentifierOrIdentifierPath

    def __init__(self, name: IdentifierOrIdentifierPath, arguments: list[Expression]):
        self.modifier_name = name
        self.arguments = arguments
        self.kind = (
            ModifierInvocationKind.FunctionCall
            if arguments
            else ModifierInvocationKind.ModifierInvocation
        )

    def fmt(self) -> str:
        invocation = (
            f'({", ".join(arg.fmt() for arg in self.arguments)})'
            if self.arguments
            else ""
        )
        return f"{self.modifier_name.fmt()}{invocation}"


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

    def __init__(
        self,
        name: str,
        name_location: Optional[SourceLocation] = None,
        base_functions: list[int] = [],
        body: Optional[Block] = None,
        documentation: Optional[StructuredDocumentation] = None,
        function_selector: Optional[str] = None,
        implemented: bool = True,
        modifiers: list[ModifierInvocation] = [],
        overrides: Optional[OverrideSpecifier] = None,
        parameters: Optional[ParameterList] = None,
        return_parameters: Optional[ParameterList] = None,
        state_mutability: Optional[StateMutability] = None,
        scope: Optional[AstId] = None,
        visibility: Visibility = Visibility.Internal,
        is_virtual: bool = False,
        is_constructor: bool = False,
        is_declared_const: bool = False,
        is_payable: bool = False,
    ):
        self.name = name
        self.parameters = parameters or ParameterList()
        self.return_parameters = return_parameters or ParameterList()

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
    canonical_name: Optional[str]
    underlying_type: TypeName

    def __init__(self, name: str, underlying_type: TypeName):
        super().__init__()
        self.name = name
        self.underlying_type = underlying_type

    def user_defined_type_name(self):
        return UserDefinedTypeName(self.name, referenced_declaration=self.id)


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

    def __init__(
        self,
        *nodes: "ContractDefinitionPart",
        name: str,
        name_location: Optional[SourceLocation] = None,
        is_abstract: bool = False,
        base_contracts: list[InheritanceSpecifier] = [],
        canonical_name: Optional[str] = None,
        contract_dependencies: list[int] = [],
        kind: ContractKind = ContractKind.Contract,
        documentation: Optional[StructuredDocumentation] = None,
        fully_implemented: bool = True,
        scope: Optional[AstId] = None,
        used_errors: list[int] = [],
        used_events: list[int] = [],
        internal_function_ids: Optional[dict[int, int]] = None,
    ):
        super().__init__()
        self.name = name
        self.name_location = name_location
        self.is_abstract = is_abstract
        self.base_contracts = base_contracts
        self.canonical_name = canonical_name
        self.contract_dependencies = contract_dependencies
        self.kind = kind
        self.documentation = documentation
        self.fully_implemented = fully_implemented
        self.nodes = list(nodes)
        self.scope = scope or AstId(randint(0, 2**64))
        self.used_errors = used_errors
        self.used_events = used_events
        self.internal_function_ids = internal_function_ids or {}

    def fmt(self) -> str:
        prefix = "abstract " if self.is_abstract else ""
        body = "{\n" + "\n".join(node.fmt() for node in self.nodes) + "\n}"
        inheritance = (
            f'is {", ".join(base.fmt() for base in self.base_contracts)}'
            if self.base_contracts
            else ""
        )

        return f"{prefix}{self.kind.value} {self.name} {inheritance} {body}"


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
