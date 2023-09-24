// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

type UDVT is uint256;

using UDVTType for UDVT global;

library UDVTType {
    uint256 constant _8_BIT_END_MASK = 0xff;
    uint256 constant FOO_NOT_MASK = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00;
    uint256 constant FOO_EXPANSION_BITS = 10;
    uint256 constant FOO_EMPTY_MASK = 0x3ff;
    uint256 constant _31_BIT_END_MASK = 0x7fffffff;
    uint256 constant BAR_NOT_MASK = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffff80000000ff;
    uint256 constant BAR_OFFSET = 8;
    uint256 constant BAR_EXPANSION_BITS = 224;
    uint256 constant _69_BIT_END_MASK = 0x1fffffffffffffffff;
    uint256 constant BAZ_NOT_MASK = 0xfffffffffffffffffffffffffffffffffffff000000000000000007fffffffff;
    uint256 constant BAZ_OFFSET = 39;
    uint256 constant _25_BIT_END_MASK = 0x1ffffff;
    uint256 constant QUX_NOT_MASK = 0xffffffffffffffffffffffffffffffe000000fffffffffffffffffffffffffff;
    uint256 constant QUX_OFFSET = 108;
    uint256 constant QUX_EXPANSION_BITS = 1;
    uint256 constant QUX_EMPTY_MASK = 0x1;

    error UnsafeValue();

    function createUDVT(int24 _foo, bytes4 _bar, uint72 _baz, uint32 _qux) internal pure returns (UDVT self) {
        bool err;
        assembly {
            let compacted := shr(FOO_EXPANSION_BITS, _foo)
            err := or(iszero(iszero(and(_foo, FOO_EMPTY_MASK))), gt(compacted, _8_BIT_END_MASK))
        }
        assembly {
            let compacted := shr(BAR_EXPANSION_BITS, _bar)
            err := gt(compacted, _31_BIT_END_MASK)
        }
        assembly {
            err := gt(_baz, BAZ_NOT_MASK)
        }
        assembly {
            err := iszero(iszero(and(_qux, QUX_EMPTY_MASK)))
        }
        if (err) {
            revert UnsafeValue();
        }
        assembly {
            self :=
                or(
                    shl(7, gt(shr(FOO_EXPANSION_BITS, _foo), _8_BIT_END_MASK)),
                    and(shr(FOO_EXPANSION_BITS, _foo), _8_BIT_END_MASK)
                )
            self := or(self, shl(BAR_OFFSET, shr(BAR_EXPANSION_BITS, _bar)))
            self := or(self, shl(BAZ_OFFSET, _baz))
            self := or(self, shl(QUX_OFFSET, shr(QUX_EXPANSION_BITS, _qux)))
        }
    }

    function unpackUDVT(UDVT self) internal pure returns (int24 _foo, bytes4 _bar, uint72 _baz, uint32 _qux) {
        assembly {
            _foo := signextend(2, shl(FOO_EXPANSION_BITS, and(self, _8_BIT_END_MASK)))
            _bar := shl(BAR_EXPANSION_BITS, and(shr(BAR_OFFSET, self), _31_BIT_END_MASK))
            _baz := and(shr(BAZ_OFFSET, self), _69_BIT_END_MASK)
            _qux := shl(QUX_EXPANSION_BITS, and(shr(QUX_OFFSET, self), _25_BIT_END_MASK))
        }
    }

    function getFoo(UDVT self) internal pure returns (int24 _foo) {
        assembly {
            _foo := signextend(2, shl(FOO_EXPANSION_BITS, and(self, _8_BIT_END_MASK)))
        }
    }

    function getBar(UDVT self) internal pure returns (bytes4 _bar) {
        assembly {
            _bar := shl(BAR_EXPANSION_BITS, and(shr(BAR_OFFSET, self), _31_BIT_END_MASK))
        }
    }

    function getBaz(UDVT self) internal pure returns (uint72 _baz) {
        assembly {
            _baz := and(shr(BAZ_OFFSET, self), _69_BIT_END_MASK)
        }
    }

    function getQux(UDVT self) internal pure returns (uint32 _qux) {
        assembly {
            _qux := shl(QUX_EXPANSION_BITS, and(shr(QUX_OFFSET, self), _25_BIT_END_MASK))
        }
    }

    function setFoo(UDVT self, int24 _foo) internal pure returns (UDVT updated) {
        bool err;
        assembly {
            let compacted := shr(FOO_EXPANSION_BITS, _foo)
            err := or(iszero(iszero(and(_foo, FOO_EMPTY_MASK))), gt(compacted, _8_BIT_END_MASK))
        }
        if (err) {
            revert UnsafeValue();
        }
        assembly {
            updated :=
                or(
                    and(self, FOO_NOT_MASK),
                    and(
                        or(
                            shl(7, gt(shr(FOO_EXPANSION_BITS, _foo), _8_BIT_END_MASK)),
                            and(shr(FOO_EXPANSION_BITS, _foo), _8_BIT_END_MASK)
                        ),
                        _8_BIT_END_MASK
                    )
                )
        }
    }

    function setBar(UDVT self, bytes4 _bar) internal pure returns (UDVT updated) {
        bool err;
        assembly {
            let compacted := shr(BAR_EXPANSION_BITS, _bar)
            err := gt(compacted, _31_BIT_END_MASK)
        }
        if (err) {
            revert UnsafeValue();
        }
        assembly {
            updated := or(and(self, BAR_NOT_MASK), shl(BAR_OFFSET, shr(BAR_EXPANSION_BITS, _bar)))
        }
    }

    function setBaz(UDVT self, uint72 _baz) internal pure returns (UDVT updated) {
        bool err;
        assembly {
            err := gt(_baz, BAZ_NOT_MASK)
        }
        if (err) {
            revert UnsafeValue();
        }
        assembly {
            updated := or(and(self, BAZ_NOT_MASK), shl(BAZ_OFFSET, _baz))
        }
    }

    function setQux(UDVT self, uint32 _qux) internal pure returns (UDVT updated) {
        bool err;
        assembly {
            err := iszero(iszero(and(_qux, QUX_EMPTY_MASK)))
        }
        if (err) {
            revert UnsafeValue();
        }
        assembly {
            updated := or(and(self, QUX_NOT_MASK), shl(QUX_OFFSET, shr(QUX_EXPANSION_BITS, _qux)))
        }
    }
}
