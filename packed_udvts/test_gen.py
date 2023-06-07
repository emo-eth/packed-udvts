from packed_udvts.udvt import UserDefinedValueType
from packed_udvts.region import Region
from packed_udvts.member import Member


class TestGen:
    udvt: UserDefinedValueType

    def __init__(self, udvt: UserDefinedValueType):
        self.udvt = udvt

    def call_get(self, region: Region, terminal: bool = False):
        return f"{self.udvt.var_name}.get{region.member.title}()" + (
            ";" if terminal else ""
        )

    def call_set(self, region: Region, value: str):
        return f"{self.udvt.var_name}.set{region.member.title}({value})"

    def update_region(
        self,
        region: Region,
        value: str,
        redeclare: bool = False,
    ) -> str:
        return f"{self.udvt.name if redeclare else ''} updated{self.udvt.var_name.title()} = {self.call_set(region,value)};"

    def assert_eq(self, lhs: str, rhs: str) -> str:
        return f"assertEq({lhs}, {rhs});"

    def fuzz_get_set_region(self, region: Region):
        updated_var_name = f"updated{region.member.title}"
        all_region_declarations = ", ".join(
            r.member.declaration for r in self.udvt.regions
        )
        all_region_declarations_with_fuzz_update = ", ".join(
            [
                all_region_declarations,
                f"{region.member.safe_typestr} updated_var_name",
            ]
        )
        all_region_shadowed_assignments = ",\n".join(
            f"{r.member.shadowed_name}: {r.member.name}" for r in self.udvt.regions
        )
        all_region_bounds = "\n".join(r.member.get_bounds() for r in self.udvt.regions)

        initial_getter_asserts = "\n".join(
            self.assert_eq(self.call_get(r), r.member.name) for r in self.udvt.regions
        )

        post_update_non_updated_asserts = "\n".join(
            self.assert_eq(self.call_get(r), r.member.name)
            for r in self.udvt.regions
            if r != region
        )
        post_update_asserts = "\n".join(
            (
                post_update_non_updated_asserts,
                self.assert_eq(self.call_get(region), updated_var_name),
            )
        )

        """"""
        return f"""
function testGetSet{region.member.title}({all_region_declarations_with_fuzz_update}) public {{
// first bound all regions
{all_region_bounds}
// then create the self.udvt
{self.udvt.name} {self.udvt.var_name } = {self.udvt.lib_name}.create{self.udvt.name}({{{all_region_shadowed_assignments}}});

// assert getters works
{initial_getter_asserts}

// update the region
{self.update_region(region, updated_var_name, redeclare=True)}

// assert setter works without changing other regions
{post_update_asserts}
}}
        """

    def generate(self):
        functions = "\n".join(self.fuzz_get_set_region(r) for r in self.udvt.regions)
        return f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {{Test}} from 'forge-std/Test.sol';
import {{{self.udvt.lib_name}, {self.udvt.name}}} from '../src/{self.udvt.lib_name}.sol';

contract {self.udvt.lib_name}Test is Test {{
{functions}
}}
        """
