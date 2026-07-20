#!/usr/bin/env python3
"""fidelity_compare.py — compute REAL similarity metrics between a candidate
artifact (SVG or a raster render of a PES/DST) and the customer SOURCE image.

This is the code the attestation gates require the worker to run BEFORE it may
state the mandated confirmation sentence. It does not merely assert similarity —
it measures it, so a false attestation cannot pass the validator.

Metrics (all in [0,1] except proportion/scale which are ratios):
  - silhouette_iou   : IoU of binarized foreground masks (shape preservation)
  - proportion_error : |aspect_candidate - aspect_source| / aspect_source
  - scale_ratio      : candidate bbox area / source bbox area (relative scale)
  - intent_score     : coarse structural similarity of downsampled luminance

Thresholds live in config/fidelity_thresholds.json. Any metric that cannot be
computed (missing renderer / lib) is returned as null with an error, which the
validator treats as FAILURE — never as a pass.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
THRESHOLDS = os.path.join(ROOT, "config", "fidelity_thresholds.json")


def _load_png(path):
    from PIL import Image  # type: ignore
    return Image.open(path).convert("RGBA")


def _render_svg_to_png(svg_path: str, out_png: str) -> str | None:
    if subprocess.run(["bash", "-lc", "command -v inkscape"], capture_output=True).returncode == 0:
        r = subprocess.run(["inkscape", svg_path, "--export-type=png",
                            f"--export-filename={out_png}"], capture_output=True, timeout=120)
        if r.returncode == 0 and os.path.exists(out_png):
            return None
    try:
        import cairosvg  # type: ignore
        cairosvg.svg2png(url=svg_path, write_to=out_png)
        return None
    except Exception as e:  # noqa: BLE001
        return f"no_svg_renderer:{e}"


def _mask(img, thresh=250):
    """Foreground mask: opaque + non-white pixels."""
    from PIL import Image  # type: ignore
    g = img.convert("L")
    a = img.getchannel("A")
    w, h = img.size
    px_g, px_a = g.load(), a.load()
    mask = Image.new("1", (w, h))
    pm = mask.load()
    for y in range(h):
        for x in range(w):
            pm[x, y] = 1 if (px_a[x, y] > 10 and px_g[x, y] < thresh) else 0
    return mask


def _bbox(mask):
    return mask.getbbox()  # None if empty


def compare(candidate: str, source: str) -> dict:
    res = {"candidate": candidate, "source": source,
           "silhouette_iou": None, "proportion_error": None,
           "scale_ratio": None, "intent_score": None, "errors": []}
    try:
        from PIL import Image  # noqa: F401
    except Exception as e:  # noqa: BLE001
        res["errors"].append(f"PIL_unavailable:{e}")
        return res

    tmp = tempfile.mkdtemp()
    cand_png = candidate
    if candidate.lower().endswith(".svg"):
        cand_png = os.path.join(tmp, "cand.png")
        err = _render_svg_to_png(candidate, cand_png)
        if err:
            res["errors"].append(err); return res
    try:
        ci = _load_png(cand_png)
        si = _load_png(source)
    except Exception as e:  # noqa: BLE001
        res["errors"].append(f"load_error:{e}"); return res

    N = 256
    ci_r = ci.resize((N, N)); si_r = si.resize((N, N))
    cm, sm = _mask(ci_r), _mask(si_r)
    cinter = sum(1 for c, s in zip(cm.getdata(), sm.getdata()) if c and s)
    cunion = sum(1 for c, s in zip(cm.getdata(), sm.getdata()) if c or s)
    res["silhouette_iou"] = round(cinter / cunion, 4) if cunion else 0.0

    cb, sb = _bbox(cm), _bbox(sm)
    if cb and sb:
        ca = (cb[2]-cb[0]) / max(1, (cb[3]-cb[1]))
        sa = (sb[2]-sb[0]) / max(1, (sb[3]-sb[1]))
        res["proportion_error"] = round(abs(ca - sa) / max(1e-6, sa), 4)
        carea = (cb[2]-cb[0]) * (cb[3]-cb[1])
        sarea = (sb[2]-sb[0]) * (sb[3]-sb[1])
        res["scale_ratio"] = round(carea / max(1, sarea), 4)
    else:
        res["errors"].append("empty_bbox")

    cg = list(ci_r.convert("L").resize((32, 32)).getdata())
    sg = list(si_r.convert("L").resize((32, 32)).getdata())
    diff = sum(abs(a - b) for a, b in zip(cg, sg)) / (len(cg) * 255)
    res["intent_score"] = round(1.0 - diff, 4)
    return res


def default_thresholds() -> dict:
    if os.path.exists(THRESHOLDS):
        return json.load(open(THRESHOLDS))
    return {"silhouette_iou_min": 0.80, "proportion_error_max": 0.10,
            "scale_ratio_min": 0.75, "scale_ratio_max": 1.25, "intent_score_min": 0.80}


def passes(metrics: dict, th: dict | None = None) -> tuple[bool, list[str]]:
    th = th or default_thresholds()
    fails = []
    if metrics.get("errors"):
        fails += metrics["errors"]
    def bad(k, cond, msg):
        v = metrics.get(k)
        if v is None or not cond(v):
            fails.append(f"{msg} (got {v})")
    bad("silhouette_iou", lambda v: v >= th["silhouette_iou_min"], "silhouette below min")
    bad("proportion_error", lambda v: v <= th["proportion_error_max"], "proportion error too high")
    bad("scale_ratio", lambda v: th["scale_ratio_min"] <= v <= th["scale_ratio_max"], "scale out of range")
    bad("intent_score", lambda v: v >= th["intent_score_min"], "intent score below min")
    return (len(fails) == 0), fails


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: fidelity_compare.py <candidate.svg|png> <source.png>")
        sys.exit(2)
    m = compare(sys.argv[1], sys.argv[2])
    ok, fails = passes(m)
    print(json.dumps({"metrics": m, "passes": ok, "failures": fails}, indent=2))
    sys.exit(0 if ok else 1)
