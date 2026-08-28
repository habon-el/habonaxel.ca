"""Tatami/fill stitch generation.

Classic tatami fill: parallel rows of stitches following a chosen angle,
spaced `row_spacing_mm` apart, with needle points along each row every
`stitch_length_mm`. Rows snake back and forth (boustrophedon) so the whole
region is covered with minimal travel and consecutive rows connect
directly into each other.

Known MVP simplification: for a concave region where a single scan row
crosses the boundary more than twice (multiple disjoint segments), we
connect the segments left-to-right with a direct stitch rather than
routing around the gap. That can lay a short stitch across a narrow
notch on complex concave shapes. Acceptable for the "clean simple logo"
scope in Section 2; flagged here rather than silently producing a bad
path, per Section 9.
"""
import math

from shapely import affinity
from shapely.geometry import LineString, Polygon

from .model import Point


def _row_segments(polygon: Polygon, y: float, xmin: float, xmax: float
                   ) -> list[tuple[float, float]]:
    line = LineString([(xmin - 1, y), (xmax + 1, y)])
    inter = polygon.intersection(line)
    segs: list[tuple[float, float]] = []
    if inter.is_empty:
        return segs
    geoms = list(inter.geoms) if hasattr(inter, "geoms") else [inter]
    for g in geoms:
        if g.geom_type != "LineString" or g.length == 0:
            continue
        xs = [c[0] for c in g.coords]
        segs.append((min(xs), max(xs)))
    segs.sort()
    return segs


def generate_fill(polygon: Polygon, angle_deg: float, row_spacing_mm: float,
                   stitch_length_mm: float) -> list[Point]:
    """Return an ordered list of needle points (mm) filling `polygon`."""
    centroid = polygon.centroid
    rotated = affinity.rotate(polygon, -angle_deg, origin=centroid)
    xmin, ymin, xmax, ymax = rotated.bounds

    points_rot: list[Point] = []
    y = ymin + row_spacing_mm / 2
    row_idx = 0
    while y <= ymax:
        segs = _row_segments(rotated, y, xmin, xmax)
        if segs:
            ordered = segs if row_idx % 2 == 0 else list(reversed(segs))
            for (x0, x1) in ordered:
                lo, hi = (x0, x1) if row_idx % 2 == 0 else (x1, x0)
                n_steps = max(1, int(abs(hi - lo) / stitch_length_mm))
                for step in range(n_steps + 1):
                    x = lo + (hi - lo) * step / n_steps
                    points_rot.append((x, y))
        row_idx += 1
        y += row_spacing_mm

    if not points_rot:
        return []

    # Rotate back to original design space.
    line = LineString(points_rot)
    line = affinity.rotate(line, angle_deg, origin=centroid)
    return [(round(x, 4), round(y, 4)) for x, y in line.coords]
