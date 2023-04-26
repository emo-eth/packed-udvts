from packed_udvts.member import Member
from packed_udvts.region import Region

from dataclasses import dataclass


@dataclass
class UserDefinedValueType:
    name: str
    regions: list[Region]

    @staticmethod
    def from_members(name: str, members: list[Member]):
        regions = []
        offset = 0
        for m in members:
            regions.append(Region(m.name, m.width_bits, offset))
            offset += m.width_bits
        assert offset <= 256, "Too many bits to pack into a single UDT"
        return UserDefinedValueType(name=name, regions=regions)


def make_regions(udt_name: str, members: list[Member]):
    """Given a list of members, return a list of regions"""
