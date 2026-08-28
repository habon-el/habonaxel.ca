"""Full digitize pipeline (M1-M4): input -> regions -> classify -> stitch
generation -> pathing -> validate -> export + preview. This is what the
`digitize` CLI subcommand and the web UI (webapp/app.py) both call."""
from src.params.classify import classify_region
from src.params.presets import get_preset
from src.pathing.order import order_by_color_then_distance
from src.regions.pipeline import load_and_extract_regions
from src.report import write_and_report
from src.stitches.build import build_blocks_for_region
from src.stitches.model import StitchBlock, StitchPlan
from src.validate.checks import validate_plan


def digitize_image(input_path: str, fabric_name: str, out_stem: str,
                    border_width_mm: float = 0.0) -> dict:
    """Runs the full pipeline and returns a dict: the write_and_report()
    result (dst/pes/preview paths, stitch_count, runtime) plus a
    "warnings" list of every non-fatal notice raised along the way.
    Raises DigitizeScopeError (unchanged) if the input is out of scope.
    """
    fabric = get_preset(fabric_name)

    region_set = load_and_extract_regions(input_path)
    warnings: list[str] = list(region_set.warnings)

    all_blocks: list[StitchBlock] = []
    classifications = []
    for region in region_set.regions:
        classification = classify_region(region, fabric)
        classifications.append((region, classification))
        blocks = build_blocks_for_region(region, classification, fabric, border_width_mm)
        for b in blocks:
            if b.is_empty():
                warnings.append(f"element '{region.region_id}' ({b.stitch_type}) "
                                 f"produced no stitches -- skipped.")
        all_blocks.extend(blocks)

    ordered = order_by_color_then_distance(all_blocks)
    plan = StitchPlan(blocks=ordered, colors=region_set.colors)

    warnings.extend(validate_plan(plan, fabric, classifications))
    for w in warnings:
        print(f"Warning: {w}")

    result = write_and_report(plan, out_stem)
    result["warnings"] = warnings
    return result
