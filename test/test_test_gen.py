from unittest import TestCase
from packed_udvts.test_gen import TestGen
from packed_udvts.udvt import UserDefinedValueType
from packed_udvts.member import Member

foo_member = Member(name="foo", width_bits=8, bytesN=None, signed=True)
bar_member = Member(name="bar", width_bits=31, bytesN=4, signed=False)
baz_member = Member(name="baz", width_bits=69, bytesN=None, signed=False)
members = [foo_member, bar_member, baz_member]
u = UserDefinedValueType.from_members(
    name="UDVT", members=members, value_type="uint256"
)
foo_region, bar_region, baz_region = u.regions


class TestTestGen(TestCase):
    tg: TestGen
    u: UserDefinedValueType

    def setUp(self) -> None:
        self.u = UserDefinedValueType(
            name="UDVT",
            regions=[foo_region, bar_region, baz_region],
            value_type="uint256",
        )
        self.tg = TestGen(self.u)
        self.maxDiff = 6969

    def test_fuzz_get_set_region(self):
        test_method = f"""
function testGetSetFoo(int8 foo, bytes4 bar, uint72 baz, int8 updatedFoo) public pure returns (bool) {{
foo = bound(foo, -128,127);
bar = bound(bar, 0, 4294967295);
baz = bound(baz, 0, 4722366482869645213695);
updatedFoo = bound(updatedFoo, -128,127);
UDVT memory u = createUDVT(foo, bar, baz);


}}
"""
        result = self.tg.fuzz_get_set_region(foo_region).fmt()
        self.assertEqual(result, test_method)
