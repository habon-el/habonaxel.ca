"""Travel routing thresholds: when a gap between the end of one block and
the start of the next needs a JUMP (and, if the gap is large enough, a
TRIM so the machine doesn't drag a long thread across the design)."""

# A normal stitch is a couple mm; anything wider than this between blocks
# is deliberate travel, not stitching, so we jump instead of sewing it.
JUMP_THRESHOLD_MM = 2.0

# Beyond this, always cut: even buried under later stitching, a float
# this long gets pulled tight and puckers the fabric under it. Under it,
# a jump is cut only when its float would show (src/pathing/visibility.py)
# -- the distance alone used to decide, which left every 2-6mm hop
# between letters as a loose strand across bare fabric.
TRIM_THRESHOLD_MM = 6.0


def needs_jump(gap_mm: float) -> bool:
    return gap_mm > JUMP_THRESHOLD_MM


def needs_trim(gap_mm: float, float_hidden: bool = True) -> bool:
    """float_hidden: whether stitching sewn later buries the travel.
    Defaults to True (the old distance-only rule) so a caller that
    can't tell never gains a cut it didn't ask for."""
    if gap_mm > TRIM_THRESHOLD_MM:
        return True
    return needs_jump(gap_mm) and not float_hidden
