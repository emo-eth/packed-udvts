// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {UDVTType, UDVT} from "src/lib/UDVTType.sol";

contract UDVTTest is Test {
    function testGetSetFoo(int24 foo, bytes4 bar, uint72 baz, int24 updatedFoo) public {
        assembly {
            foo := and(foo, 0x3fc00)
        }
        assembly {
            bar := and(bar, 0x7fffffff00000000000000000000000000000000000000000000000000000000)
        }
        baz = uint72(bound(baz, 0x0, 0x1fffffffffffffffff));
        assembly {
            updatedFoo := and(updatedFoo, 0x3fc00)
        }
        UDVT uDVT = (UDVTType.createUDVT({_foo: foo, _bar: bar, _baz: baz}));
        assertEq(uDVT.getFoo(), foo, "getter for foo failed");
        assertEq(uDVT.getBar(), bar, "getter for bar failed");
        assertEq(uDVT.getBaz(), baz, "getter for baz failed");
        UDVT updatedUdvt = (uDVT.setFoo(updatedFoo));
        assertEq(updatedUdvt.getBar(), bar, "getter for bar failed post-update");
        assertEq(updatedUdvt.getBaz(), baz, "getter for baz failed post-update");
        assertEq(updatedUdvt.getFoo(), updatedFoo, "getter for updated region foo failed post-update");
    }

    function testGetSetBar(int24 foo, bytes4 bar, uint72 baz, bytes4 updatedBar) public {
        assembly {
            foo := and(foo, 0x3fc00)
        }
        assembly {
            bar := and(bar, 0x7fffffff00000000000000000000000000000000000000000000000000000000)
        }
        baz = uint72(bound(baz, 0x0, 0x1fffffffffffffffff));
        assembly {
            updatedBar := and(updatedBar, 0x7fffffff00000000000000000000000000000000000000000000000000000000)
        }
        UDVT uDVT = (UDVTType.createUDVT({_foo: foo, _bar: bar, _baz: baz}));
        assertEq(uDVT.getFoo(), foo, "getter for foo failed");
        assertEq(uDVT.getBar(), bar, "getter for bar failed");
        assertEq(uDVT.getBaz(), baz, "getter for baz failed");
        UDVT updatedUdvt = (uDVT.setBar(updatedBar));
        assertEq(updatedUdvt.getFoo(), foo, "getter for foo failed post-update");
        assertEq(updatedUdvt.getBaz(), baz, "getter for baz failed post-update");
        assertEq(updatedUdvt.getBar(), updatedBar, "getter for updated region bar failed post-update");
    }

    function testGetSetBaz(int24 foo, bytes4 bar, uint72 baz, uint72 updatedBaz) public {
        assembly {
            foo := and(foo, 0x3fc00)
        }
        assembly {
            bar := and(bar, 0x7fffffff00000000000000000000000000000000000000000000000000000000)
        }
        baz = uint72(bound(baz, 0x0, 0x1fffffffffffffffff));
        updatedBaz = uint72(bound(updatedBaz, 0x0, 0x1fffffffffffffffff));
        UDVT uDVT = (UDVTType.createUDVT({_foo: foo, _bar: bar, _baz: baz}));
        assertEq(uDVT.getFoo(), foo, "getter for foo failed");
        assertEq(uDVT.getBar(), bar, "getter for bar failed");
        assertEq(uDVT.getBaz(), baz, "getter for baz failed");
        UDVT updatedUdvt = (uDVT.setBaz(updatedBaz));
        assertEq(updatedUdvt.getFoo(), foo, "getter for foo failed post-update");
        assertEq(updatedUdvt.getBar(), bar, "getter for bar failed post-update");
        assertEq(updatedUdvt.getBaz(), updatedBaz, "getter for updated region baz failed post-update");
    }
}
