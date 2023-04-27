// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

type Stake is uint256;

using StakeType for Stake global;

library StakeType {
    uint256 constant ID_END_MASK = 0x7fff;
    uint256 constant ID_NOT_MASK = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0003;
    uint256 constant ID_OFFSET = 2;
    uint256 constant POOL_END_MASK = 0x3;
    uint256 constant POOL_NOT_MASK = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc;

    function createStake(uint8 _pool, uint16 _id) internal pure returns (Stake self) {
        assembly {
            self := _pool
            self := or(self, shl(ID_OFFSET, _id))
        }
    }

    function unpackStake(Stake self) internal pure returns (uint8 _pool, uint16 _id) {
        assembly {
            _pool := and(self, POOL_END_MASK)
            _id := and(shr(ID_OFFSET, self), ID_END_MASK)
        }
    }

    function getPool(Stake self) internal pure returns (uint8 _pool) {
        assembly {
            _pool := and(self, POOL_END_MASK)
        }
    }

    function getId(Stake self) internal pure returns (uint16 _id) {
        assembly {
            _id := and(shr(ID_OFFSET, self), ID_END_MASK)
        }
    }

    function setPool(Stake self, uint8 _pool) internal pure returns (Stake updated) {
        require(_pool <= POOL_END_MASK, "pool value too large");
        assembly {
            updated := or(and(self, POOL_NOT_MASK), _pool)
        }
    }

    function setId(Stake self, uint16 _id) internal pure returns (Stake updated) {
        require(_id <= ID_END_MASK, "id value too large");
        assembly {
            updated := or(and(self, ID_NOT_MASK), shl(ID_OFFSET, _id))
        }
    }
}
