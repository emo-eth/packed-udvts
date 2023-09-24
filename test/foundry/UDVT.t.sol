// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {UDVTType, UDVT} from "src/lib/UDVTType.sol";

contract UDVTTest is Test {
    function testGetSetFoo(int24 foo, bytes4 bar, uint72 baz, uint32 qux, int24 updatedFoo) public {
        assembly {
            foo := and(foo, 0x3fc00)
        }
        assembly {
            bar := and(bar, 0x7fffffff00000000000000000000000000000000000000000000000000000000)
        }
        baz = uint72(bound(baz, 0x0, 0x1fffffffffffffffff));
        assembly {
            qux := and(qux, 0x3fffffe)
        }
        assembly {
            updatedFoo := and(updatedFoo, 0x3fc00)
        }
        UDVT uDVT = (UDVTType.createUDVT({_foo: foo, _bar: bar, _baz: baz, _qux: qux}));
        assertEq(uDVT.getFoo(), foo, "getter for foo failed");
        assertEq(uDVT.getBar(), bar, "getter for bar failed");
        assertEq(uDVT.getBaz(), baz, "getter for baz failed");
        assertEq(uDVT.getQux(), qux, "getter for qux failed");
        UDVT updatedUdvt = (uDVT.setFoo(updatedFoo));
        assertEq(updatedUdvt.getBar(), bar, "getter for bar failed post-update");
        assertEq(updatedUdvt.getBaz(), baz, "getter for baz failed post-update");
        assertEq(updatedUdvt.getQux(), qux, "getter for qux failed post-update");
        assertEq(updatedUdvt.getFoo(), updatedFoo, "getter for updated region foo failed post-update");
    }

    function testGetSetBar(int24 foo, bytes4 bar, uint72 baz, uint32 qux, bytes4 updatedBar) public {
        assembly {
            foo := and(foo, 0x3fc00)
        }
        assembly {
            bar := and(bar, 0x7fffffff00000000000000000000000000000000000000000000000000000000)
        }
        baz = uint72(bound(baz, 0x0, 0x1fffffffffffffffff));
        assembly {
            qux := and(qux, 0x3fffffe)
        }
        assembly {
            updatedBar := and(updatedBar, 0x7fffffff00000000000000000000000000000000000000000000000000000000)
        }
        UDVT uDVT = (UDVTType.createUDVT({_foo: foo, _bar: bar, _baz: baz, _qux: qux}));
        assertEq(uDVT.getFoo(), foo, "getter for foo failed");
        assertEq(uDVT.getBar(), bar, "getter for bar failed");
        assertEq(uDVT.getBaz(), baz, "getter for baz failed");
        assertEq(uDVT.getQux(), qux, "getter for qux failed");
        UDVT updatedUdvt = (uDVT.setBar(updatedBar));
        assertEq(updatedUdvt.getFoo(), foo, "getter for foo failed post-update");
        assertEq(updatedUdvt.getBaz(), baz, "getter for baz failed post-update");
        assertEq(updatedUdvt.getQux(), qux, "getter for qux failed post-update");
        assertEq(updatedUdvt.getBar(), updatedBar, "getter for updated region bar failed post-update");
    }

    function testGetSetBaz(int24 foo, bytes4 bar, uint72 baz, uint32 qux, uint72 updatedBaz) public {
        assembly {
            foo := and(foo, 0x3fc00)
        }
        assembly {
            bar := and(bar, 0x7fffffff00000000000000000000000000000000000000000000000000000000)
        }
        baz = uint72(bound(baz, 0x0, 0x1fffffffffffffffff));
        assembly {
            qux := and(qux, 0x3fffffe)
        }
        updatedBaz = uint72(bound(updatedBaz, 0x0, 0x1fffffffffffffffff));
        UDVT uDVT = (UDVTType.createUDVT({_foo: foo, _bar: bar, _baz: baz, _qux: qux}));
        assertEq(uDVT.getFoo(), foo, "getter for foo failed");
        assertEq(uDVT.getBar(), bar, "getter for bar failed");
        assertEq(uDVT.getBaz(), baz, "getter for baz failed");
        assertEq(uDVT.getQux(), qux, "getter for qux failed");
        UDVT updatedUdvt = (uDVT.setBaz(updatedBaz));
        assertEq(updatedUdvt.getFoo(), foo, "getter for foo failed post-update");
        assertEq(updatedUdvt.getBar(), bar, "getter for bar failed post-update");
        assertEq(updatedUdvt.getQux(), qux, "getter for qux failed post-update");
        assertEq(updatedUdvt.getBaz(), updatedBaz, "getter for updated region baz failed post-update");
    }

    function testGetSetQux(int24 foo, bytes4 bar, uint72 baz, uint32 qux, uint32 updatedQux) public {
        assembly {
            foo := and(foo, 0x3fc00)
        }
        assembly {
            bar := and(bar, 0x7fffffff00000000000000000000000000000000000000000000000000000000)
        }
        baz = uint72(bound(baz, 0x0, 0x1fffffffffffffffff));
        assembly {
            qux := and(qux, 0x3fffffe)
        }
        assembly {
            updatedQux := and(updatedQux, 0x3fffffe)
        }
        UDVT uDVT = (UDVTType.createUDVT({_foo: foo, _bar: bar, _baz: baz, _qux: qux}));
        assertEq(uDVT.getFoo(), foo, "getter for foo failed");
        assertEq(uDVT.getBar(), bar, "getter for bar failed");
        assertEq(uDVT.getBaz(), baz, "getter for baz failed");
        assertEq(uDVT.getQux(), qux, "getter for qux failed");
        UDVT updatedUdvt = (uDVT.setQux(updatedQux));
        assertEq(updatedUdvt.getFoo(), foo, "getter for foo failed post-update");
        assertEq(updatedUdvt.getBar(), bar, "getter for bar failed post-update");
        assertEq(updatedUdvt.getBaz(), baz, "getter for baz failed post-update");
        assertEq(updatedUdvt.getQux(), updatedQux, "getter for updated region qux failed post-update");
    }
}
