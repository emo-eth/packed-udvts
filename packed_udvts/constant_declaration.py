from dataclasses import dataclass


@dataclass(frozen=True, unsafe_hash=True)
class ConstantDeclaration:
    name: str
    value: str

    def render(self) -> str:
        return f"uint256 constant {self.name} = {self.value};"
