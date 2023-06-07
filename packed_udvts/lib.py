from packed_udvts.member import Member
from packed_udvts.region import Region
from dataclasses import dataclass


@dataclass
class UDTLibrary:
    udt_name: str
    regions: list[Region]

    def from_members():
        pass
