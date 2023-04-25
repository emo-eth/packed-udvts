from unittest import TestCase
from packed_udts.region import Region


class TestRegion(TestCase):
    def test_region(self):
        r = Region("Udt", "foo", 5, 14)
        self.assertEqual(r.end_mask(), "0x1f")
        self.assertEqual(r.end_mask_name(), "FOO_END_MASK")
        self.assertEqual(
            r.not_mask(),
            "0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff83fff",
        )
        self.assertEqual(r.not_mask_name(), "FOO_NOT_MASK")
        self.assertEqual(r.offset_bits_name(), "FOO_OFFSET")
        setter_str = f"""
function setFoo(Udt self, uint256 value) internal pure returns (Udt updated) {{
    require(value <= FOO_END_MASK, "{r.name} value too large");
    assembly {{
        let masked := and(self, FOO_NOT_MASK)
        updated := or(masked, shl({r.offset_bits}, value))
    }}
}}"""
        self.assertEqual(r.setter(), setter_str)
