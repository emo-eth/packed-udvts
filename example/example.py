from unittest import TestCase
from packed_udvts.udvt import UserDefinedValueType
from packed_udvts.member import Member
from packed_udvts.test_gen import TestGen

foo_member = Member(
    name="foo", width_bits=8, bytesN=None, signed=True, expansion_bits=10
)
bar_member = Member(name="bar", width_bits=31, bytesN=4, signed=False)
baz_member = Member(name="baz", width_bits=69, bytesN=None, signed=False)
qux_member = Member(
    name="qux", width_bits=25, bytesN=None, signed=False, expansion_bits=1
)
members = [foo_member, bar_member, baz_member, qux_member]
u = UserDefinedValueType.from_members(
    name="UDVT", members=members, value_type="uint256"
)
tg = TestGen(u)

# typesafe=True by default
# print(u.render_file())

# make src/lib folder if not exists
import os

os.makedirs("src/lib", exist_ok=True)

with open("src/lib/UDVTType.sol", "w") as f:
    f.write(u.render_file(typesafe=False).fmt())


with open("test/foundry/UDVT.t.sol", "w") as f:
    f.write(tg.generate().fmt())

# print(u.render_file(typesafe=False))

# pool_member = Member(name="pool", width_bits=2, bytesN=None, signed=False)
# id_member = Member(name="id", width_bits=15, bytesN=None, signed=False)
# stake = UserDefinedValueType.from_members("Stake", [pool_member, id_member], "uint256")
# stake_array = UserDefinedValueType.packed_array_of(stake, max_length=8)

# print(stake.render_file())
# print(stake_array.render_file(typesafe=False))
