"""Cut by visibility, not distance (src/pathing/visibility.py): a jump the
machine doesn't cut leaves a strand lying on the fabric. Whether that
shows depends on what is sewn over it afterwards, not on how far the
jump is -- a 3mm hop between two letters used to stay uncut and leave
a loose strand the customer had to snip off by hand."""
import pyembroidery as pe

from src.io_.export import stitch_plan_to_pattern
from src.pathing.route import JUMP_THRESHOLD_MM, TRIM_THRESHOLD_MM, needs_trim
from src.pathing.visibility import COVER_RADIUS_MM
from src.stitches.model import FILL, RUNNING, StitchBlock, StitchPlan, ThreadColor
from src.validate.audit import visible_floats

THREAD = ThreadColor(name="c", rgb=(10, 10, 10))
GAP = (JUMP_THRESHOLD_MM + TRIM_THRESHOLD_MM) / 2  # a jump, under the old trim distance


def _cut_before(pattern, point) -> bool:
    """Whether the thread is cut on the way to the first stitch at point."""
    target = (round(point[0] * 10), round(point[1] * 10))
    for x, y, cmd in pattern.stitches:
        kind = cmd & pe.COMMAND_MASK
        if kind == pe.TRIM:
            return True
        if kind == pe.STITCH and (round(x), round(y)) == target:
            return False
    raise AssertionError(f"never stitched at {point}")


def _hop(*later: StitchBlock) -> StitchPlan:
    a = StitchBlock(RUNNING, [(0.0, 0.0), (2.0, 0.0)], element_id="a")
    b = StitchBlock(RUNNING, [(2.0 + GAP, 0.0), (4.0 + GAP, 0.0)], element_id="b")
    return StitchPlan(blocks=[a, b, *later], colors=[THREAD])


def _fill_over(x0, x1, y0=-2.0, y1=2.0, spacing=0.4) -> StitchBlock:
    """Back-and-forth fill rows covering the rectangle x0..x1, y0..y1."""
    pts, y, flip = [], y0, False
    while y <= y1 + 1e-9:
        row = [(x0, y), (x1, y)]
        pts.extend(reversed(row) if flip else row)
        y += spacing
        flip = not flip
    return StitchBlock(FILL, pts, element_id="cover")


def test_needs_trim_rule():
    assert not needs_trim(JUMP_THRESHOLD_MM, float_hidden=False)  # sewn, not jumped
    assert needs_trim(GAP, float_hidden=False)
    assert not needs_trim(GAP, float_hidden=True)
    assert needs_trim(TRIM_THRESHOLD_MM + 1, float_hidden=True)  # long: always cut
    assert not needs_trim(GAP)  # a caller that can't tell keeps the old rule


def test_short_hop_across_bare_fabric_is_cut():
    pattern = stitch_plan_to_pattern(_hop())
    assert _cut_before(pattern, (2.0 + GAP, 0.0))
    assert visible_floats(pattern) == []


def test_short_hop_buried_by_a_later_fill_is_not_cut():
    pattern = stitch_plan_to_pattern(_hop(_fill_over(1.0, 3.0 + GAP)))
    assert not _cut_before(pattern, (2.0 + GAP, 0.0))
    assert visible_floats(pattern) == []


def test_hop_over_stitching_already_done_is_still_cut():
    """Finished stitching underneath doesn't hide a strand lying on top
    of it -- only stitching sewn afterwards does."""
    a = _fill_over(1.0, 3.0 + GAP)
    a_end = a.points_mm[-1]
    b_start = (a_end[0] - GAP if a_end[0] > 2 else a_end[0] + GAP, a_end[1])
    b = StitchBlock(RUNNING, [b_start, (b_start[0], b_start[1] + 2.0)], element_id="b")
    pattern = stitch_plan_to_pattern(StitchPlan(blocks=[a, b], colors=[THREAD]))
    assert _cut_before(pattern, b_start)


def test_audit_counts_a_strand_left_showing():
    plan = _hop()
    plan.blocks[1].force_trim_before = False  # the user switched this cut off
    shown = visible_floats(stitch_plan_to_pattern(plan))
    assert len(shown) == 1
    # Block b's own first stitch is sewn after the strand and lies over
    # its end -- the file-only measure counts that as cover.
    assert GAP - 2 * COVER_RADIUS_MM <= shown[0] <= GAP
