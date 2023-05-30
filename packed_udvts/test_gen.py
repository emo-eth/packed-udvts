from packed_udvts.udvt import UserDefinedValueType
from packed_udvts.region import Region
from packed_udvts.member import Member


class TestGen:
    def fuzz_get_set_region(self, udvt: UserDefinedValueType, region: Region):
        all_region_declarations = ", ".join(r.member.declaration for r in udvt.regions)
        updated_member = ", ".join(
            [
                all_region_declarations,
                f"{region.member.safe_typestr} updated{region.member.title}",
            ]
        )
        all_region_shadowed_assignments = ",\n".join(
            f"{r.member.shadowed_name}: {r.member.name}" for r in udvt.regions
        )
        all_region_bounds = "\n".join(r.member.get_bounds() for r in udvt.regions)
        """"""
        return f"""
function testGetSet{region.member.title}({all_region_declarations}) public {{
// first bound all regions
{all_region_bounds}
// then create the UDVT
{udvt.name} {udvt.var_name } = {udvt.lib_name}.create{udvt.name}({{{all_region_shadowed_assignments}}});
}}

// assert getter works
assertEq({udvt.var_name}.get{region.member.title}(), {region.member.name});
        """
