"""Shared "write files + print summary" step used by every CLI command."""
import os

from src.io_.export import write_pattern
from src.preview.render import render_preview
from src.preview.runtime import estimate_runtime_seconds, format_runtime
from src.stitches.model import StitchPlan


def write_and_report(plan: StitchPlan, out_stem: str) -> None:
    out_dir = os.path.dirname(out_stem)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    paths = write_pattern(plan, out_stem)
    preview_path = render_preview(plan, f"{out_stem}_preview.png")
    runtime_s = estimate_runtime_seconds(plan)

    print(f"Wrote {paths['dst']}")
    print(f"Wrote {paths['pes']}")
    print(f"Wrote {preview_path}")
    print(f"Stitch count: {plan.stitch_count()}")
    print(f"Estimated run time: {format_runtime(runtime_s)}")
