from typing import TypeVar, TYPE_CHECKING, Iterable
from itertools import chain
from abc import ABCMeta


if TYPE_CHECKING:
    from sol_ast.ast import AstNode, Statement

SerializableNode = TypeVar("SerializableNode", bound="AstNode")
StatementNode = TypeVar("StatementNode", bound="Statement")
T = TypeVar("T")


def wrap_block(nodes: Iterable[SerializableNode], semicolon: bool) -> Iterable[str]:
    return chain("{", indent(x.fmt() + ";" if semicolon else "" for x in nodes), "}")


def indent(lines: Iterable[str], indent: int = 0) -> Iterable[str]:
    indent_str = " " * 4 * indent
    return (f"{indent_str}{x}" for x in lines)


def line_join(lines: Iterable[str]) -> str:
    return f"\n".join(x for x in lines if x)


def super_checker(node: type[SerializableNode]) -> type[SerializableNode]:
    old_init = node.__init__

    def new_init(self, *args, **kwargs):
        old_init(self, *args, **kwargs)
        assert self.d is not None

    node.__init__ = new_init

    return node


def statement_checker(node: type[StatementNode]) -> type[StatementNode]:
    old_fmt = node.fmt

    def new_fmt(self) -> str:
        output = old_fmt(self)
        assert output.endswith(";"), f"Statement {self} does not end with a semicolon"
        return output

    node.fmt = new_fmt
    return node


class NodeDictChecker(ABCMeta):
    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)
        x = super_checker(x)  # type: ignore
        return x


class StatementChecker(NodeDictChecker):
    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)
        x = statement_checker(x)  # type: ignore
        return x
