"""Does a stretch of travel thread show, or is it buried?

When the machine jumps without cutting, the thread lies loose on top of
the fabric between the two points (a "float"). Whether that matters has
nothing to do with how long the jump is: a 3mm float across bare
fabric between two letters is a visible strand the customer has to snip
by hand, while a 15mm float that a later fill sews straight over is
pinned flat and never seen. The distance-only rule in route.py could
only ever guess at that; this module checks it.

A float is hidden only when stitching sewn *later* covers it. Thread
crossing stitching that is already finished lies on top of it, which
shows and snags just the same as crossing bare fabric.
"""
from __future__ import annotations

from shapely import STRtree
from shapely.geometry import LineString
from shapely.ops import unary_union

from src.stitches.model import BORDER, FILL, SATIN, StitchBlock

# Only stitch types that lay down a surface bury a float. A running
# line crossing it pins it at one point and leaves the rest showing.
COVER_STITCH_TYPES = (FILL, SATIN, BORDER)

# Half the width of thread surface a covering stitch path lays down
# around its own needle line. Fill rows and satin zigzags sit well under
# 2x this apart, so the buffered paths of one block merge into the
# block's whole area.
COVER_RADIUS_MM = 0.5

# A float may poke out this far past the cover and still count as
# hidden: the needle lands a hair outside an edge on any real block
# (pull compensation, the 1/10mm file grid), and a stub this short
# lies under the neighbouring stitches rather than across fabric.
MAX_EXPOSED_MM = 0.5


def exposed_mm(a, b, covers: list) -> float:
    """Length of the straight float a->b not lying under any of covers."""
    seg = LineString([a, b])
    if seg.length == 0:
        return 0.0
    if not covers:
        return seg.length
    return seg.difference(unary_union(covers)).length


class LaterCover:
    """Answers "is the travel from a to b buried by stitching that comes
    after block i?" for every block of one plan. Built once per export;
    a spatial index keeps each query to the blocks actually nearby."""

    def __init__(self, blocks: list[StitchBlock]):
        self._geoms = []
        self._order = []
        for i, block in enumerate(blocks):
            if block.stitch_type in COVER_STITCH_TYPES and len(block.points_mm) >= 2:
                self._geoms.append(LineString(block.points_mm).buffer(COVER_RADIUS_MM))
                self._order.append(i)
        self._tree = STRtree(self._geoms) if self._geoms else None

    def exposed_after(self, a, b, after_index: int) -> float:
        """mm of the float a->b left showing by blocks after after_index."""
        if self._tree is None:
            return exposed_mm(a, b, [])
        hits = self._tree.query(LineString([a, b]))
        later = [self._geoms[h] for h in hits if self._order[h] > after_index]
        return exposed_mm(a, b, later)

    def hidden_after(self, a, b, after_index: int) -> bool:
        return self.exposed_after(a, b, after_index) <= MAX_EXPOSED_MM
