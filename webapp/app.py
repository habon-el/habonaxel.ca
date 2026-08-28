"""Local web UI for the embroidery editor.

Run it with:

    source .venv/bin/activate
    pip install -r requirements.txt   # picks up Flask if not already installed
    python -m webapp.app

Then open http://127.0.0.1:5000 in a browser. Everything runs locally --
no data leaves your machine. This is a thin UI over src/pipeline.py; it
does not duplicate any digitizing logic.
"""
import os
import uuid

from flask import Flask, abort, request, send_from_directory
from werkzeug.utils import secure_filename

from src.params.presets import PRESETS
from src.pipeline import digitize_image
from src.regions.model import DigitizeScopeError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg"}
MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


def _page(body: str) -> str:
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Embroidery Editor</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 780px;
         margin: 40px auto; padding: 0 20px; color: #222; background: #fafafa; }}
  h1 {{ font-size: 1.6rem; }}
  .card {{ background: white; border: 1px solid #ddd; border-radius: 10px;
           padding: 24px; margin-bottom: 20px; }}
  label {{ display: block; margin: 14px 0 4px; font-weight: 600; font-size: 0.9rem; }}
  select, input[type=file], input[type=number] {{ padding: 8px; border-radius: 6px;
           border: 1px solid #ccc; width: 100%; box-sizing: border-box; }}
  button {{ margin-top: 20px; padding: 10px 22px; background: #1c5aaa; color: white;
            border: none; border-radius: 6px; font-size: 1rem; cursor: pointer; }}
  button:hover {{ background: #164683; }}
  .warn {{ background: #fff8e1; border: 1px solid #f0d385; border-radius: 8px;
           padding: 12px 16px; margin: 12px 0; font-size: 0.9rem; }}
  .error {{ background: #fdecea; border: 1px solid #f2b8b5; border-radius: 8px;
            padding: 14px 16px; }}
  .stat {{ display: inline-block; margin-right: 24px; font-size: 0.95rem; }}
  .stat b {{ display: block; font-size: 1.3rem; }}
  img.preview {{ max-width: 100%; border: 1px solid #ddd; border-radius: 8px; }}
  a.download {{ display: inline-block; margin: 8px 12px 0 0; padding: 8px 16px;
                background: #eee; border-radius: 6px; text-decoration: none; color: #222; }}
  a.download:hover {{ background: #ddd; }}
  .back {{ font-size: 0.9rem; }}
</style>
</head>
<body>
<h1>🪡 Embroidery Editor</h1>
{body}
</body>
</html>"""


UPLOAD_FORM = f"""
<div class="card">
  <p>Upload a clean, flat 2-4 color logo/text image (PNG/JPG/SVG). Photos
  and gradients will be rejected rather than digitized badly -- that's
  intentional.</p>
  <form action="/digitize" method="post" enctype="multipart/form-data">
    <label>Image file</label>
    <input type="file" name="image" accept=".png,.jpg,.jpeg,.svg" required>

    <label>Fabric preset</label>
    <select name="fabric">
      {"".join(f'<option value="{name}">{name}</option>' for name in sorted(PRESETS))}
    </select>

    <label>Border width (mm, 0 = disabled)</label>
    <input type="number" name="border" value="0" min="0" max="10" step="0.5">
    <p style="font-size:0.85rem;color:#666;margin-top:4px;">
      A denser fill ring stitched along each shape's own edge, on top of
      its interior fill, for a bolder/more raised-looking border.
    </p>

    <label style="display:flex;align-items:center;gap:8px;font-weight:normal;">
      <input type="checkbox" name="force" value="1" style="width:auto;">
      Force -- digitize anyway if this looks like a photo or has detail
      below the minimum size, instead of rejecting
    </label>
    <p style="font-size:0.85rem;color:#666;margin-top:4px;">
      These checks exist because a needle physically can't render detail
      that small -- forcing past them doesn't change that, just skips
      the warning. Check the preview carefully if you use this.
    </p>

    <button type="submit">Digitize</button>
  </form>
</div>
"""


@app.route("/")
def index():
    return _page(UPLOAD_FORM)


def _run_and_render(job_id: str, input_path: str, fabric: str, border: float,
                     force: bool) -> tuple[str, int]:
    job_dir = os.path.dirname(input_path)
    out_stem = os.path.join(job_dir, "design")

    try:
        result = digitize_image(input_path, fabric, out_stem,
                                 border_width_mm=border, force=force)
    except DigitizeScopeError as e:
        retry = "" if force else f"""
<form action="/force/{job_id}" method="post" style="margin-top:12px;">
  <input type="hidden" name="fabric" value="{fabric}">
  <input type="hidden" name="border" value="{border}">
  <button type="submit" style="background:#a94442;">Force digitize anyway</button>
</form>"""
        return _page(f'<div class="card error"><p><b>Rejected:</b> {e}</p>'
                      f'{retry}'
                      f'<p class="back"><a href="/">&larr; try another image</a></p>'
                      f'</div>'), 200
    except Exception as e:  # noqa: BLE001 -- surface any pipeline error to the UI, not a 500 page
        return _page(f'<div class="card error"><p><b>Error:</b> {e}</p>'
                      f'<p class="back"><a href="/">&larr; try another image</a></p></div>'), 500

    warnings_html = "".join(f'<div class="warn">⚠️ {w}</div>' for w in result["warnings"])

    return _page(f"""
<div class="card">
  <p class="stat"><b>{result['stitch_count']}</b>stitches</p>
  <p class="stat"><b>{result['runtime_formatted']}</b>est. run time</p>
  <p class="stat"><b>{fabric}</b>fabric</p>
  {warnings_html}
  <div style="margin-top:16px;">
    <img class="preview" src="/outputs/{job_id}/design_preview.png" alt="Stitch preview">
  </div>
  <div>
    <a class="download" href="/outputs/{job_id}/design.dst" download>Download .DST</a>
    <a class="download" href="/outputs/{job_id}/design.pes" download>Download .PES</a>
  </div>
</div>
<p class="back"><a href="/">&larr; digitize another image</a></p>
"""), 200


@app.route("/digitize", methods=["POST"])
def digitize():
    file = request.files.get("image")
    if not file or file.filename == "":
        return _page('<div class="card error"><p>No file selected.</p>'
                      '<p class="back"><a href="/">&larr; back</a></p></div>'), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return _page(f'<div class="card error"><p>Unsupported file type '
                      f'"{ext}". Use PNG, JPG, or SVG.</p>'
                      f'<p class="back"><a href="/">&larr; back</a></p></div>'), 400

    fabric = request.form.get("fabric", "twill")
    if fabric not in PRESETS:
        fabric = "twill"
    try:
        border = float(request.form.get("border", "0") or 0)
    except ValueError:
        border = 0.0
    force = request.form.get("force") == "1"

    job_id = uuid.uuid4().hex[:12]
    job_dir = os.path.join(RESULTS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    input_path = os.path.join(job_dir, f"input{ext}")
    file.save(input_path)

    return _run_and_render(job_id, input_path, fabric, border, force)


@app.route("/force/<job_id>", methods=["POST"])
def force_digitize(job_id):
    """Re-run a rejected job with force=True, reusing the already-saved
    upload so the user doesn't have to pick the file again."""
    job_dir = os.path.join(RESULTS_DIR, secure_filename(job_id))
    if not os.path.isdir(job_dir):
        abort(404)
    matches = [f for f in os.listdir(job_dir) if f.startswith("input.")]
    if not matches:
        abort(404)
    input_path = os.path.join(job_dir, matches[0])

    fabric = request.form.get("fabric", "twill")
    if fabric not in PRESETS:
        fabric = "twill"
    try:
        border = float(request.form.get("border", "0") or 0)
    except ValueError:
        border = 0.0

    return _run_and_render(job_id, input_path, fabric, border, force=True)


@app.route("/outputs/<job_id>/<path:filename>")
def outputs(job_id, filename):
    job_dir = os.path.join(RESULTS_DIR, job_id)
    if not os.path.isdir(job_dir):
        abort(404)
    return send_from_directory(job_dir, filename)


if __name__ == "__main__":
    os.makedirs(RESULTS_DIR, exist_ok=True)
    app.run(host="127.0.0.1", port=5000, debug=False)
