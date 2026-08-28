"""CLI entry point.

    python -m src.cli demo --shape circle --fabric twill --out testbench/out/demo
    python -m src.cli digitize input.png --fabric twill --out testbench/out/design
"""
import argparse
import sys

from src.params.presets import PRESETS, get_preset
from src.pathing.order import order_by_color_then_distance
from src.pipeline import digitize_image
from src.report import write_and_report
from src.stitches.model import StitchPlan
from src.stitches.shapes import DEMO_THREAD, SHAPES, build_demo_blocks


def cmd_demo(args: argparse.Namespace) -> None:
    fabric = get_preset(args.fabric)
    blocks = build_demo_blocks(args.shape, fabric, angle_deg=args.angle)
    ordered = order_by_color_then_distance(blocks)
    plan = StitchPlan(blocks=ordered, colors=[DEMO_THREAD])
    write_and_report(plan, args.out)


def cmd_digitize(args: argparse.Namespace) -> None:
    digitize_image(args.input, args.fabric, args.out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="digitize", description="Auto-digitizing embroidery editor (MVP)")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser(
        "demo", help="Generate a hand-built demo stitch file (M0 spine, no CV input)")
    demo.add_argument("--shape", default="circle", choices=sorted(SHAPES))
    demo.add_argument("--fabric", default="twill", choices=sorted(PRESETS))
    demo.add_argument("--angle", type=float, default=45.0,
                       help="Fill angle in degrees")
    demo.add_argument("--out", required=True,
                       help="Output path stem, e.g. testbench/out/demo")
    demo.set_defaults(func=cmd_demo)

    digitize = sub.add_parser(
        "digitize", help="Auto-digitize a clean raster/SVG logo or text image")
    digitize.add_argument("input", help="Path to a PNG/JPG/SVG input file")
    digitize.add_argument("--fabric", default="twill", choices=sorted(PRESETS))
    digitize.add_argument("--out", required=True,
                           help="Output path stem, e.g. testbench/out/design")
    digitize.set_defaults(func=cmd_digitize)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
