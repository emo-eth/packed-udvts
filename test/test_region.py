from unittest import TestCase
from packed_udvts.region import Region
from packed_udvts.member import Member


class TestRegion(TestCase):
    def test_region_end_mask(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        r = Region(member=member, offset_bits=14)
        self.assertEqual(r.end_mask, "0x1f")
        self.assertEqual(r.end_mask_name, "FOO_END_MASK")

    def test_region_not_mask(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        r = Region(member=member, offset_bits=14)
        self.assertEqual(
            r.not_mask,
            "0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff83fff",
        )
        self.assertEqual(r.not_mask_name, "FOO_NOT_MASK")

    def test_region_offset_bits_name(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        r = Region(member=member, offset_bits=14)
        self.assertEqual(r.offset_bits_name, "FOO_OFFSET")

    def test_setter(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        r = Region(member=member, offset_bits=14)
        setter_str = f"""
function setFoo(Udt self, uint8 value) internal pure returns (Udt updated) {{
    require(value <= FOO_END_MASK, "foo value too large");
    assembly {{
        updated := or(and(self, FOO_NOT_MASK), shl({r.offset_bits_name}, value))
    }}
}}"""
        self.assertEqual(r.setter("Udt"), setter_str)

    def test_getter(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        r = Region(member=member, offset_bits=14)
        getter_str = f"""
function getFoo(Udt self) internal pure returns (uint8 _foo) {{
    assembly {{
        _foo := and(shr({r.offset_bits_name}, self), FOO_END_MASK)
    }}
}}"""
        self.assertEqual(r.getter("Udt"), getter_str)

        r = Region(member=member, offset_bits=0)
        getter_str = f"""
function getFoo(Udt self) internal pure returns (uint256 _foo) {{
    assembly {{
        _foo := and(self, FOO_END_MASK)
    }}
}}"""
        self.assertEqual(r.getter("Udt", typesafe=False), getter_str)

        member = Member(name="foo", width_bits=5, bytesN=4, signed=False)
        r = Region(member=member, offset_bits=0)
        getter_str = f"""
function getFoo(Udt self) internal pure returns (bytes4 _foo) {{
    assembly {{
        _foo := shl(FOO_EXPANSION_BITS, and(self, FOO_END_MASK))
    }}
}}"""
        self.assertEqual(r.getter("Udt"), getter_str)

        member = Member(name="foo", width_bits=8, bytesN=None, signed=True)
        r = Region(member=member, offset_bits=0)
        getter_str = f"""
function getFoo(Udt self) internal pure returns (int8 _foo) {{
    assembly {{
        _foo := signextend(0, and(self, FOO_END_MASK))
    }}
}}"""
        self.assertEqual(r.getter("Udt"), getter_str)
        member = Member(name="foo", width_bits=8, bytesN=None, signed=True)
        r = Region(member=member, offset_bits=0)
        getter_str = f"""
function getFoo(Udt self) internal pure returns (int256 _foo) {{
    assembly {{
        _foo := signextend(0, and(self, FOO_END_MASK))
    }}
}}"""
        self.assertEqual(r.getter("Udt", typesafe=False), getter_str)
