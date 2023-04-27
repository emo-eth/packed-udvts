from unittest import TestCase
from packed_udvts.udvt import UserDefinedValueType
from packed_udvts.member import Member

foo_member = Member(name="foo", width_bits=8, bytesN=None, signed=True)
bar_member = Member(name="bar", width_bits=31, bytesN=4, signed=False)
baz_member = Member(name="baz", width_bits=69, bytesN=None, signed=False)
members = [foo_member, bar_member, baz_member]
u = UserDefinedValueType.from_members(
    name="UDVT", members=members, value_type="uint256"
)

# typesafe=True by default
print(u.render_file())
# print(u.render_file(typesafe=False))
