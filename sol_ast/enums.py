from enum import Enum, auto


class Visibility(Enum):
    Public = "public"
    Private = "private"
    Internal = "internal"
    External = "external"


class AssignmentOperator(Enum):
    Assign = "="
    AddAssign = "+="
    SubAssign = "-="
    MulAssign = "*="
    DivAssign = "/="
    ModAssign = "%="
    OrAssign = "|="
    AndAssign = "&="
    XorAssign = "^="
    ShlAssign = "<<="
    ShrAssign = ">>="


class BinaryOperator(Enum):
    Add = "+"
    Sub = "-"
    Mul = "*"
    Div = "/"
    Mod = "%"
    Pow = "**"
    And = "&&"
    Or = "||"
    NotEqual = "!="
    Equal = "=="
    LessThan = "<"
    LessThanOrEqual = "<="
    GreaterThan = ">"
    GreaterThanOrEqual = ">="
    Xor = "^"
    BitAnd = "&"
    BitOr = "|"
    Shl = "<<"
    Shr = ">>"


class StateMutability(Enum):
    Payable = "payable"
    Pure = "pure"
    Nonpayable = ""
    View = "view"


class Mutability(Enum):
    Constant = "constant"
    Immutable = "immutable"
    Mutable = ""


class FunctionCallKind(Enum):
    FunctionCall = auto()
    TypeConversion = auto()
    StructConstructorCall = auto()


class LiteralKind(Enum):
    Bool = auto()
    Number = auto()
    String = auto()
    HexString = auto()
    UnicodeString = auto()


class UnaryOperator(Enum):
    Increment = "++"
    Decrement = "--"
    Negate = "-"
    Not = "!"
    BitNot = "~"
    Delete = "delete"


class StorageLocation(Enum):
    Calldata = "calldata"
    Default = ""
    Memory = "memory"
    Storage = "storage"


class FunctionKind(Enum):
    Function = auto()
    Receive = auto()
    Constructor = auto()
    Fallback = auto()
    FreeFunction = auto()


class YulLiteralKind(Enum):
    Number = auto()
    String = auto()
    Bool = auto()


class AssemblyReferenceSuffix(Enum):
    Slot = "slot"
    Offset = "offset"
    Length = "length"


class InlineAssemblyFlag(Enum):
    MemorySafe = auto()


class ModifierInvocationKind(Enum):
    ModifierInvocation = auto()
    FunctionCall = auto()


class ContractKind(Enum):
    Contract = "contract"
    Interface = "interface"
    Library = "library"
