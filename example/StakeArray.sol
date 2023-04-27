// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {Stake} from "./Stake.sol";

type StakeArray is uint256;

using StakeArrayType for StakeArray global;

library StakeArrayType {
    uint256 constant INDEX0_NOT_MASK = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00007;
    uint256 constant INDEX0_OFFSET = 3;
    uint256 constant INDEX1_NOT_MASK = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffe0000fffff;
    uint256 constant INDEX1_OFFSET = 20;
    uint256 constant INDEX2_NOT_MASK = 0xffffffffffffffffffffffffffffffffffffffffffffffffffc0001fffffffff;
    uint256 constant INDEX2_OFFSET = 37;
    uint256 constant INDEX3_NOT_MASK = 0xffffffffffffffffffffffffffffffffffffffffffffff80003fffffffffffff;
    uint256 constant INDEX3_OFFSET = 54;
    uint256 constant INDEX4_NOT_MASK = 0xffffffffffffffffffffffffffffffffffffffffff00007fffffffffffffffff;
    uint256 constant INDEX4_OFFSET = 71;
    uint256 constant INDEX5_NOT_MASK = 0xfffffffffffffffffffffffffffffffffffffe0000ffffffffffffffffffffff;
    uint256 constant INDEX5_OFFSET = 88;
    uint256 constant INDEX6_NOT_MASK = 0xfffffffffffffffffffffffffffffffffc0001ffffffffffffffffffffffffff;
    uint256 constant INDEX6_OFFSET = 105;
    uint256 constant INDEX7_NOT_MASK = 0xfffffffffffffffffffffffffffff80003ffffffffffffffffffffffffffffff;
    uint256 constant INDEX7_OFFSET = 122;
    uint256 constant LENGTH_NOT_MASK = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff8;
    uint256 constant _17_BIT_END_MASK = 0x1ffff;
    uint256 constant _3_BIT_END_MASK = 0x7;

    function createStakeArray(
        uint256 _length,
        Stake _index0,
        Stake _index1,
        Stake _index2,
        Stake _index3,
        Stake _index4,
        Stake _index5,
        Stake _index6,
        Stake _index7
    ) internal pure returns (StakeArray self) {
        assembly {
            self := _length
            self := or(self, shl(INDEX0_OFFSET, _index0))
            self := or(self, shl(INDEX1_OFFSET, _index1))
            self := or(self, shl(INDEX2_OFFSET, _index2))
            self := or(self, shl(INDEX3_OFFSET, _index3))
            self := or(self, shl(INDEX4_OFFSET, _index4))
            self := or(self, shl(INDEX5_OFFSET, _index5))
            self := or(self, shl(INDEX6_OFFSET, _index6))
            self := or(self, shl(INDEX7_OFFSET, _index7))
        }
    }

    function unpackStakeArray(StakeArray self)
        internal
        pure
        returns (
            uint256 _length,
            Stake _index0,
            Stake _index1,
            Stake _index2,
            Stake _index3,
            Stake _index4,
            Stake _index5,
            Stake _index6,
            Stake _index7
        )
    {
        assembly {
            _length := and(self, _3_BIT_END_MASK)
            _index0 := and(shr(INDEX0_OFFSET, self), _17_BIT_END_MASK)
            _index1 := and(shr(INDEX1_OFFSET, self), _17_BIT_END_MASK)
            _index2 := and(shr(INDEX2_OFFSET, self), _17_BIT_END_MASK)
            _index3 := and(shr(INDEX3_OFFSET, self), _17_BIT_END_MASK)
            _index4 := and(shr(INDEX4_OFFSET, self), _17_BIT_END_MASK)
            _index5 := and(shr(INDEX5_OFFSET, self), _17_BIT_END_MASK)
            _index6 := and(shr(INDEX6_OFFSET, self), _17_BIT_END_MASK)
            _index7 := and(shr(INDEX7_OFFSET, self), _17_BIT_END_MASK)
        }
    }

    function getLength(StakeArray self) internal pure returns (uint256 _length) {
        assembly {
            _length := and(self, _3_BIT_END_MASK)
        }
    }

    function getIndex0(StakeArray self) internal pure returns (Stake _index0) {
        assembly {
            _index0 := and(shr(INDEX0_OFFSET, self), _17_BIT_END_MASK)
        }
    }

    function getIndex1(StakeArray self) internal pure returns (Stake _index1) {
        assembly {
            _index1 := and(shr(INDEX1_OFFSET, self), _17_BIT_END_MASK)
        }
    }

    function getIndex2(StakeArray self) internal pure returns (Stake _index2) {
        assembly {
            _index2 := and(shr(INDEX2_OFFSET, self), _17_BIT_END_MASK)
        }
    }

    function getIndex3(StakeArray self) internal pure returns (Stake _index3) {
        assembly {
            _index3 := and(shr(INDEX3_OFFSET, self), _17_BIT_END_MASK)
        }
    }

    function getIndex4(StakeArray self) internal pure returns (Stake _index4) {
        assembly {
            _index4 := and(shr(INDEX4_OFFSET, self), _17_BIT_END_MASK)
        }
    }

    function getIndex5(StakeArray self) internal pure returns (Stake _index5) {
        assembly {
            _index5 := and(shr(INDEX5_OFFSET, self), _17_BIT_END_MASK)
        }
    }

    function getIndex6(StakeArray self) internal pure returns (Stake _index6) {
        assembly {
            _index6 := and(shr(INDEX6_OFFSET, self), _17_BIT_END_MASK)
        }
    }

    function getIndex7(StakeArray self) internal pure returns (Stake _index7) {
        assembly {
            _index7 := and(shr(INDEX7_OFFSET, self), _17_BIT_END_MASK)
        }
    }

    function setLength(StakeArray self, uint256 _length) internal pure returns (StakeArray updated) {
        assembly {
            updated := or(and(self, LENGTH_NOT_MASK), _length)
        }
    }

    function setIndex0(StakeArray self, Stake _index0) internal pure returns (StakeArray updated) {
        assembly {
            updated := or(and(self, INDEX0_NOT_MASK), shl(INDEX0_OFFSET, _index0))
        }
    }

    function setIndex1(StakeArray self, Stake _index1) internal pure returns (StakeArray updated) {
        assembly {
            updated := or(and(self, INDEX1_NOT_MASK), shl(INDEX1_OFFSET, _index1))
        }
    }

    function setIndex2(StakeArray self, Stake _index2) internal pure returns (StakeArray updated) {
        assembly {
            updated := or(and(self, INDEX2_NOT_MASK), shl(INDEX2_OFFSET, _index2))
        }
    }

    function setIndex3(StakeArray self, Stake _index3) internal pure returns (StakeArray updated) {
        assembly {
            updated := or(and(self, INDEX3_NOT_MASK), shl(INDEX3_OFFSET, _index3))
        }
    }

    function setIndex4(StakeArray self, Stake _index4) internal pure returns (StakeArray updated) {
        assembly {
            updated := or(and(self, INDEX4_NOT_MASK), shl(INDEX4_OFFSET, _index4))
        }
    }

    function setIndex5(StakeArray self, Stake _index5) internal pure returns (StakeArray updated) {
        assembly {
            updated := or(and(self, INDEX5_NOT_MASK), shl(INDEX5_OFFSET, _index5))
        }
    }

    function setIndex6(StakeArray self, Stake _index6) internal pure returns (StakeArray updated) {
        assembly {
            updated := or(and(self, INDEX6_NOT_MASK), shl(INDEX6_OFFSET, _index6))
        }
    }

    function setIndex7(StakeArray self, Stake _index7) internal pure returns (StakeArray updated) {
        assembly {
            updated := or(and(self, INDEX7_NOT_MASK), shl(INDEX7_OFFSET, _index7))
        }
    }
}
