"""Full digitize pipeline (M1-M4): input -> regions -> classify -> stitch
generation -> pathing -> validate -> export + preview. This is what the
`digitize` CLI subcommand calls."""
from src.params.classify import classify_region
from src.params.presets import get_preset
from src.pathing.order import order_by_color_then_distance
from src.regions.pipeline import load_and_extract_regions
from src.report import write_and_report
from src.stitches.build import build_blocks_for_region
from src.stitches.model import StitchBlock, StitchPlan
from src.validate.checks import validate_plan


def digitize_image(input_path: str, fabric_name: str, out_stem: str) -> None:
    fabric = get_preset(fabric_name)

    region_set = load_and_extract_regions(input_path)
    for w in region_set.warnings:
        print(f"Warning: {w}")

    all_blocks: list[StitchBlock] = []
    classifications = []
    for region in region_set.regions:
        classification = classify_region(region, fabric)
        classifications.append((region, classification))
        blocks = build_blocks_for_region(region, classification, fabric)
        for b in blocks:
            if b.is_empty():
                print(f"Warning: element '{region.region_id}' ({b.stitch_type}) "
                      f"produced no stitches -- skipped.")
        all_blocks.extend(blocks)

    ordered = order_by_color_then_distance(all_blocks)
    plan = StitchPlan(blocks=ordered, colors=region_set.colors)

    for w in validate_plan(plan, fabric, classifications):
        print(f"Warning: {w}")

    write_and_report(plan, out_stem)
