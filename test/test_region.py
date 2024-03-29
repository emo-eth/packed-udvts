from unittest import TestCase
from packed_udvts.region import Region
from packed_udvts.member import Member
from sol_ast.ast import UserDefinedTypeName


class TestRegion(TestCase):
    def setUp(self):
        self.maxDiff = 6969

    def test_region_end_mask(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        r = Region(member=member, offset_bits=14)
        self.assertEqual(r.end_mask.fmt(), "0x1f")
        self.assertEqual(r.end_mask_name.fmt(), "_5_BIT_END_MASK")

    def test_region_not_mask(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        r = Region(member=member, offset_bits=14)
        self.assertEqual(
            r.not_mask.fmt(),
            "0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff83fff",
        )
        self.assertEqual(r.not_mask_name.fmt(), "FOO_NOT_MASK")

    def test_region_offset_bits_name(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        r = Region(member=member, offset_bits=14)
        self.assertEqual(r.offset_bits_name.fmt(), "FOO_OFFSET")

    def test_setter(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        r = Region(member=member, offset_bits=14)
        setter_str = f"""function setFoo(Udt self, uint8 _foo) internal pure returns (Udt updated) {{
require(_foo <= _5_BIT_END_MASK, "foo value too large");
assembly {{
updated := or(and(self, FOO_NOT_MASK), shl({r.offset_bits_name}, _foo))
}}
}}"""
        result = r.setter(UserDefinedTypeName("Udt")).fmt()
        print(result)
        print("!!!")
        print(setter_str)
        self.assertEqual(result, setter_str)

    def test_getter(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        r = Region(member=member, offset_bits=14)
        name = UserDefinedTypeName("Udt")
        getter_str = f"""function getFoo(Udt self) internal pure returns (uint8 _foo) {{
assembly {{
_foo := and(shr({r.offset_bits_name}, self), _5_BIT_END_MASK)
}}
}}"""
        result = r.getter(name).fmt()
        self.assertEqual(result, getter_str)

        r = Region(member=member, offset_bits=0)
        getter_str = f"""function getFoo(Udt self) internal pure returns (uint256 _foo) {{
assembly {{
_foo := and(self, _5_BIT_END_MASK)
}}
}}"""
        result = r.getter(name, typesafe=False).fmt()
        self.assertEqual(result, getter_str)

        member = Member(name="foo", width_bits=5, bytesN=4, signed=False)
        r = Region(member=member, offset_bits=0)
        getter_str = f"""
function getFoo(Udt self) internal pure returns (bytes4 _foo) {{
assembly {{
_foo := shl(FOO_EXPANSION_BITS, and(self, _5_BIT_END_MASK))
}}
}}"""
        result = r.getter(name).fmt()
        self.assertEqual(result, getter_str.strip())

        member = Member(name="foo", width_bits=8, bytesN=None, signed=True)
        r = Region(member=member, offset_bits=0)
        getter_str = f"""
function getFoo(Udt self) internal pure returns (int8 _foo) {{
assembly {{
_foo := signextend(0, and(self, _8_BIT_END_MASK))
}}
}}"""
        result = r.getter(name).fmt()
        self.assertEqual(result, getter_str.strip())

        member = Member(name="foo", width_bits=8, bytesN=None, signed=True)
        r = Region(member=member, offset_bits=0)
        getter_str = f"""
function getFoo(Udt self) internal pure returns (int256 _foo) {{
assembly {{
_foo := signextend(0, and(self, _8_BIT_END_MASK))
}}
}}"""
        result = r.getter(name, typesafe=False).fmt()
        self.assertEqual(result, getter_str.strip())
