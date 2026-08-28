# habonaxel.ca

## Embroidery Editor (MVP)

An auto-digitizing embroidery editor: converts a clean logo/text image into
a real, sew-able machine embroidery file (DST + PES), with a stitch-level
preview. CLI-first, Python 3.11+.

**Scope (see build spec for full detail):** clean vector/raster input,
2-4 flat colors, running/satin/fill stitches, auto underlay, fabric-preset
density/angle, sew-order pathing, DST/PES export via `pyembroidery`.
Photos, gradients, 3D/puff, and sub-6mm text are out of scope and are
flagged rather than silently digitized.

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Usage

```bash
# M0 spine: hand-built shape, no image input, proves the export path
python -m src.cli demo --shape circle --fabric twill --out testbench/out/demo

# Full pipeline: digitize a real logo/text image
python -m src.cli digitize path/to/logo.png --fabric twill --out testbench/out/design
```

Each run writes `<out>.dst`, `<out>.pes`, and `<out>_preview.png`, and
prints the stitch count and an estimated run time.

Fabric presets: `twill` (default, stable woven), `fleece`, `knit`
(placeholder, conservative — see `src/params/presets.py` for caveats).

### Tests

```bash
pytest
./run_tests.sh   # full suite + batch digitize over testbench/inputs/
```

### Physical validation

A screen preview cannot catch push-pull distortion, puckering, or real
satin edge quality. See `testbench/SEWOUT_CHECKLIST.md` before calling any
preset production-ready.

### Project layout

See `src/` (io_, regions, stitches, params, pathing, preview, validate,
cli.py), `tests/`, and `testbench/` (inputs/expected/out).
