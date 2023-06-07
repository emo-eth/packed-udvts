// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {Test} from "forge-std/Test.sol";
import {UDVTType, UDVT} from "../../src/UDVTType.sol";

contract UDVTTypeTest is Test {
    function testGetSetFoo(int8 foo, bytes4 bar, uint72 baz, int8 updatedFoo) public {
        // first bound all regions
        foo = int8(bound(foo, -0x80, 0x7f));

        assembly {
            bar := and(bar, 0x7fffffff00000000000000000000000000000000000000000000000000000000)
        }
        baz = uint72(bound(baz, 0x0, 0x1fffffffffffffffff));
        updatedFoo = int8(bound(updatedFoo, -0x80, 0x7f));
        // then create the self.udvt
        UDVT uDVT = UDVTType.createUDVT({_foo: foo, _bar: bar, _baz: baz});

        // assert getters works
        assertEq(uDVT.getFoo(), foo, "getter for foo failed");
        assertEq(uDVT.getBar(), bar, "getter for bar failed");
        assertEq(uDVT.getBaz(), baz, "getter for baz failed");

        // update the region
        UDVT updatedUdvt = uDVT.setFoo(updatedFoo);

        // assert setter works without changing other regions
        assertEq(updatedUdvt.getBar(), bar, "getter for bar failed post-update");
        assertEq(updatedUdvt.getBaz(), baz, "getter for baz failed post-update");
        assertEq(updatedUdvt.getFoo(), updatedFoo, "getter for updated region foo failed post-update");
    }

    function testGetSetBar(int8 foo, bytes4 bar, uint72 baz, bytes4 updatedBar) public {
        // first bound all regions
        foo = int8(bound(foo, -0x80, 0x7f));

        assembly {
            bar := and(bar, 0x7fffffff00000000000000000000000000000000000000000000000000000000)
        }
        baz = uint72(bound(baz, 0x0, 0x1fffffffffffffffff));

        assembly {
            updatedBar := and(updatedBar, 0x7fffffff00000000000000000000000000000000000000000000000000000000)
        }
        // then create the self.udvt
        UDVT uDVT = UDVTType.createUDVT({_foo: foo, _bar: bar, _baz: baz});

        // assert getters works
        assertEq(uDVT.getFoo(), foo, "getter for foo failed");
        assertEq(uDVT.getBar(), bar, "getter for bar failed");
        assertEq(uDVT.getBaz(), baz, "getter for baz failed");

        // update the region
        UDVT updatedUdvt = uDVT.setBar(updatedBar);

        // assert setter works without changing other regions
        assertEq(updatedUdvt.getFoo(), foo, "getter for foo failed post-update");
        assertEq(updatedUdvt.getBaz(), baz, "getter for baz failed post-update");
        assertEq(updatedUdvt.getBar(), updatedBar, "getter for updated region bar failed post-update");
    }

    function testGetSetBaz(int8 foo, bytes4 bar, uint72 baz, uint72 updatedBaz) public {
        // first bound all regions
        foo = int8(bound(foo, -0x80, 0x7f));

        assembly {
            bar := and(bar, 0x7fffffff00000000000000000000000000000000000000000000000000000000)
        }
        baz = uint72(bound(baz, 0x0, 0x1fffffffffffffffff));
        updatedBaz = uint72(bound(updatedBaz, 0x0, 0x1fffffffffffffffff));
        // then create the self.udvt
        UDVT uDVT = UDVTType.createUDVT({_foo: foo, _bar: bar, _baz: baz});

        // assert getters works
        assertEq(uDVT.getFoo(), foo, "getter for foo failed");
        assertEq(uDVT.getBar(), bar, "getter for bar failed");
        assertEq(uDVT.getBaz(), baz, "getter for baz failed");

        // update the region
        UDVT updatedUdvt = uDVT.setBaz(updatedBaz);

        // assert setter works without changing other regions
        assertEq(updatedUdvt.getFoo(), foo, "getter for foo failed post-update");
        assertEq(updatedUdvt.getBar(), bar, "getter for bar failed post-update");
        assertEq(updatedUdvt.getBaz(), updatedBaz, "getter for updated region baz failed post-update");
    }
}
