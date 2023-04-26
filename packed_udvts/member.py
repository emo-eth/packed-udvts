from dataclasses import dataclass


@dataclass
class Member:
    # name of this member in the solidity struct
    name: str
    # width of this member in bits
    width_bits: int
