from unittest import TestCase
from packed_udvts.member import Member


class TestMember(TestCase):
    def test_zero_width_fail(self):
        with self.assertRaises(AssertionError, msg="width_bits must be positive"):
            member = Member(name="foo", width_bits=0, bytesN=None, signed=False)

    def test_bytes_signed_fail(self):
        with self.assertRaises(
            AssertionError,
            msg="signed regions must have a width divisible by 8 for compatibility with SIGNEXTEND",
        ):
            member = Member(name="foo", width_bits=5, bytesN=4, signed=True)

    def test_title(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        self.assertEqual(member.title, "Foo")

    def test_shadowed_name(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        self.assertEqual(member.shadowed_name, "_foo")

    def test_safe_typestr(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        self.assertEqual(member.safe_typestr, "uint8")

    def test_safe_typestr_signed(self):
        member = Member(name="foo", width_bits=8, bytesN=None, signed=True)
        self.assertEqual(member.safe_typestr, "int8")

    def test_safe_typestr_bytes(self):
        member = Member(name="foo", width_bits=5, bytesN=2, signed=False)
        self.assertEqual(member.safe_typestr, "bytes2")

    def test_whole_bytes(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        self.assertEqual(member.whole_bytes, 1)

    def test_whole_bytes_bytes(self):
        member = Member(name="foo", width_bits=5, bytesN=2, signed=False)
        self.assertEqual(member.whole_bytes, 1)

    def test_unsafe_typestr(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        self.assertEqual(member.unsafe_typestr, "uint256")

    def test_unsafe_typestr_signed(self):
        member = Member(name="foo", width_bits=8, bytesN=None, signed=True)
        self.assertEqual(member.unsafe_typestr, "int256")

    def test_unsafe_typestr_bytes(self):
        member = Member(name="foo", width_bits=5, bytesN=2, signed=False)
        self.assertEqual(member.unsafe_typestr, "bytes32")

    def test_num_expansion_bits(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        self.assertEqual(member.num_expansion_bits, None)

    def test_typestr(self):
        member = Member(name="foo", width_bits=5, bytesN=None, signed=False)
        self.assertEqual(member.typestr(typesafe=True), "uint8")
        self.assertEqual(member.typestr(typesafe=False), "uint256")

        member = Member(name="foo", width_bits=8, bytesN=None, signed=True)
        self.assertEqual(member.typestr(typesafe=True), "int8")
        self.assertEqual(member.typestr(typesafe=False), "int256")

        member = Member(name="foo", width_bits=69, bytesN=None, signed=False)
        self.assertEqual(member.typestr(typesafe=True), "uint72")
        self.assertEqual(member.typestr(typesafe=False), "uint256")
