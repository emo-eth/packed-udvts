from packed_udts.member import Member
from packed_udts.region import Region


def make_regions(udt_name: str, members: list[Member]):
    """Given a list of members, return a list of regions"""
    regions = []
    offset = 0
    for m in members:
        regions.append(Region(udt_name, m.name, m.width_bits, offset))
        offset += m.width_bits
    assert offset <= 256, "Too many bits to pack into a single UDT"
    return regions
