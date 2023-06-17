from typing import TypeVar, TYPE_CHECKING, Iterable
from itertools import chain

if TYPE_CHECKING:
    from sol_ast.ast import AstNode

SerializableNode = TypeVar("SerializableNode", bound=AstNode)


def wrap_block(nodes: Iterable[SerializableNode]) -> Iterable[str]:
    return chain("{", (x.serialize() for x in nodes), "}")


def line_join(lines: Iterable[str]) -> str:
    return "\n".join(x for x in lines if x)
