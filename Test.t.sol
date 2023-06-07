// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {Test} from 'forge-std/Test.sol';
import {UDVTType, UDVT} from '../src/UDVTType.sol';

contract UDVTTypeTest is Test {

function testGetSetFoo(int8 foo, bytes4 bar, uint72 baz, int8 updated_var_name) public {
// first bound all regions
foo = int8(bound(foo, -128, 127));

assembly {
bar := and(bar, 57896044591698151044634852709676938839615361659183137597188219522852954570752)
}
baz = uint72(bound(baz, 0, 590295810358705651711));
// then create the self.udvt
UDVT uDVT = UDVTType.createUDVT({_foo: foo,
_bar: bar,
_baz: baz});

// assert getters works
assertEq(uDVT.getFoo(), foo);
assertEq(uDVT.getBar(), bar);
assertEq(uDVT.getBaz(), baz);

// update the region
UDVT updatedUdvt = uDVT.setFoo(updatedFoo);

// assert setter works without changing other regions
assertEq(uDVT.getBar(), bar);
assertEq(uDVT.getBaz(), baz);
assertEq(uDVT.getFoo(), updatedFoo);
}
        

function testGetSetBar(int8 foo, bytes4 bar, uint72 baz, bytes4 updated_var_name) public {
// first bound all regions
foo = int8(bound(foo, -128, 127));

assembly {
bar := and(bar, 57896044591698151044634852709676938839615361659183137597188219522852954570752)
}
baz = uint72(bound(baz, 0, 590295810358705651711));
// then create the self.udvt
UDVT uDVT = UDVTType.createUDVT({_foo: foo,
_bar: bar,
_baz: baz});

// assert getters works
assertEq(uDVT.getFoo(), foo);
assertEq(uDVT.getBar(), bar);
assertEq(uDVT.getBaz(), baz);

// update the region
UDVT updatedUdvt = uDVT.setBar(updatedBar);

// assert setter works without changing other regions
assertEq(uDVT.getFoo(), foo);
assertEq(uDVT.getBaz(), baz);
assertEq(uDVT.getBar(), updatedBar);
}
        

function testGetSetBaz(int8 foo, bytes4 bar, uint72 baz, uint72 updated_var_name) public {
// first bound all regions
foo = int8(bound(foo, -128, 127));

assembly {
bar := and(bar, 57896044591698151044634852709676938839615361659183137597188219522852954570752)
}
baz = uint72(bound(baz, 0, 590295810358705651711));
// then create the self.udvt
UDVT uDVT = UDVTType.createUDVT({_foo: foo,
_bar: bar,
_baz: baz});

// assert getters works
assertEq(uDVT.getFoo(), foo);
assertEq(uDVT.getBar(), bar);
assertEq(uDVT.getBaz(), baz);

// update the region
UDVT updatedUdvt = uDVT.setBaz(updatedBaz);

// assert setter works without changing other regions
assertEq(uDVT.getFoo(), foo);
assertEq(uDVT.getBar(), bar);
assertEq(uDVT.getBaz(), updatedBaz);
}
        
}
        
