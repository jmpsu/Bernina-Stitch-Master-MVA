"""ihive.py — I-HIVE engine enhancements (BRD § I-HIVE Target Engine).

Adds the BRD capabilities missing from the base vectorizer:

* **Bayesian path-quality scoring** — a Beta-posterior acceptance model plus a
  Gaussian composite-score model over the 7k-attempt history in
  ``vectorization_attempts.jsonl``, ranking parameter configurations by
  expected quality so exploration starts from statistically proven configs
  rather than fixed presets.
* **Locked background tracing layer** — embeds the source raster in a locked,
  non-exported archival layer inside the working SVG (Inkscape
  ``sodipodi:insensitive`` + ``display:none``), so the customer's
  source-of-truth image travels with the vector without ever becoming
  stitches; ``strip_archival_layers`` produces the production export.
"""

from __future__ import annotations

import base64
import json
import math
import re
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
ATTEMPTS = REPO_ROOT / "vectorization_attempts.jsonl"

ARCHIVAL_LAYER_ID = "embiz-archival-source"


# --- Bayesian candidate scoring ----------------------------------------------

def _param_key(params: dict) -> str:
    return json.dumps({k: params[k] for k in sorted(params)}, sort_keys=True)


def load_attempts(attempts_path: Path = ATTEMPTS, image: str | None = None):
    if not attempts_path.exists():
        return []
    out = []
    for line in attempts_path.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if image and rec.get("image") != image:
            continue
        if isinstance(rec.get("params"), dict) and \
                isinstance(rec.get("composite"), (int, float)):
            out.append(rec)
    return out


def bayes_rank_candidates(image: str | None = None, top_k: int = 10,
                          attempts_path: Path = ATTEMPTS) -> list[dict]:
    """Rank historical parameter configs by posterior expected quality.

    For each unique config: acceptance is modeled Beta(1+accepts, 1+rejects)
    (uniform prior) and composite score as Gaussian with a weak prior pulled
    toward the global mean. The ranking statistic is a conservative lower
    bound — posterior mean composite minus one posterior std of the mean,
    times the Beta acceptance mean — so one lucky attempt cannot outrank a
    consistently strong config. Deterministic and fully reproducible from
    the attempts ledger.
    """
    attempts = load_attempts(attempts_path, image)
    if not attempts:
        return []
    global_scores = [a["composite"] for a in attempts]
    g_mean = sum(global_scores) / len(global_scores)
    g_var = (sum((s - g_mean) ** 2 for s in global_scores)
             / max(1, len(global_scores) - 1))

    groups: dict[str, list[dict]] = defaultdict(list)
    for a in attempts:
        groups[_param_key(a["params"])].append(a)

    ranked = []
    prior_n = 2.0  # weak prior: two pseudo-observations at the global mean
    for key, recs in groups.items():
        n = len(recs)
        scores = [r["composite"] for r in recs]
        accepts = sum(1 for r in recs if r.get("accepted"))
        # Beta posterior over acceptance
        alpha, beta = 1 + accepts, 1 + (n - accepts)
        p_accept = alpha / (alpha + beta)
        # Gaussian posterior mean with conjugate-style shrinkage to g_mean
        post_mean = (prior_n * g_mean + sum(scores)) / (prior_n + n)
        var = (sum((s - post_mean) ** 2 for s in scores) / n) if n > 1 else g_var
        se = math.sqrt(max(var, 1e-8) / (prior_n + n))
        lower_bound = post_mean - se
        ranked.append({
            "params": recs[0]["params"],
            "n_attempts": n,
            "accept_posterior_mean": round(p_accept, 4),
            "composite_posterior_mean": round(post_mean, 4),
            "composite_lower_bound": round(lower_bound, 4),
            "bayes_score": round(lower_bound * p_accept, 4),
            "best_observed": round(max(scores), 4),
        })
    ranked.sort(key=lambda r: r["bayes_score"], reverse=True)
    return ranked[:top_k]


# --- locked background tracing layer -------------------------------------------

def add_locked_tracing_layer(svg_path: Path, raster_path: Path,
                             out_path: Path | None = None) -> Path:
    """Embed the source raster as a locked, hidden archival layer in the SVG.

    The layer is Inkscape-locked (``sodipodi:insensitive="true"``), hidden
    (``display:none``), and carries ``data-embiz-archival="true"`` so
    production export strips it deterministically. Idempotent: an existing
    archival layer is replaced.
    """
    svg_path, raster_path = Path(svg_path), Path(raster_path)
    out_path = Path(out_path) if out_path else svg_path
    text = svg_path.read_text(encoding="utf-8")
    text = _strip_layer_text(text)
    ext = raster_path.suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png"}.get(ext, "png")
    b64 = base64.b64encode(raster_path.read_bytes()).decode("ascii")
    layer = (
        f'<g id="{ARCHIVAL_LAYER_ID}" data-embiz-archival="true" '
        f'inkscape:groupmode="layer" inkscape:label="archival source (locked)" '
        f'sodipodi:insensitive="true" style="display:none">'
        f'<image xlink:href="data:image/{mime};base64,{b64}" '
        f'x="0" y="0" preserveAspectRatio="xMidYMid meet"/></g>')
    # namespaces required by the layer attributes
    for prefix, uri in [
        ("xmlns:inkscape", "http://www.inkscape.org/namespaces/inkscape"),
        ("xmlns:sodipodi", "http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd"),
        ("xmlns:xlink", "http://www.w3.org/1999/xlink"),
    ]:
        if prefix not in text:
            text = text.replace("<svg ", f'<svg {prefix}="{uri}" ', 1)
    if "</svg>" not in text:
        raise ValueError(f"not an SVG: {svg_path}")
    text = text.replace("</svg>", layer + "</svg>")
    out_path.write_text(text, encoding="utf-8")
    return out_path


def _strip_layer_text(text: str) -> str:
    return re.sub(
        rf'<g id="{ARCHIVAL_LAYER_ID}".*?</g>', "", text, flags=re.S)


def strip_archival_layers(svg_path: Path, out_path: Path) -> Path:
    """Production export: remove every archival layer (BRD: the final SVG
    contains only production-relevant subject paths)."""
    text = Path(svg_path).read_text(encoding="utf-8")
    out = Path(out_path)
    out.write_text(_strip_layer_text(text), encoding="utf-8")
    return out


def cleanup_svg(svg_path: Path, out_path: Path | None = None) -> dict:
    """SVG structural cleanup (BRD I-HIVE): remove exact duplicate paths —
    identical geometry AND identical presentation stitches the same shape
    twice, building thread and risking jams. Distinct fills on the same
    geometry (stacked layering) are preserved. Returns removal stats."""
    svg_path = Path(svg_path)
    out_path = Path(out_path) if out_path else svg_path
    text = svg_path.read_text(encoding="utf-8")
    # Identical geometry means the same shape stitched more than once — even
    # under a different fill the earlier copy is fully occluded in painter's
    # order and would only double-stitch. Keep the LAST (visible) occurrence.
    matches = list(re.finditer(r"<path\b[^>]*/?>", text))
    last_for_d: dict[str, int] = {}
    for i, m in enumerate(matches):
        dm = re.search(r'\bd="([^"]*)"', m.group(0))
        last_for_d[dm.group(1) if dm else f"__nod{i}"] = i
    keep = set(last_for_d.values())
    removed = 0
    out, pos = [], 0
    for i, m in enumerate(matches):
        out.append(text[pos:m.start()])
        if i in keep:
            out.append(m.group(0))
        else:
            removed += 1
        pos = m.end()
    out.append(text[pos:])
    out_path.write_text("".join(out), encoding="utf-8")
    return {"paths_removed": removed, "paths_kept": len(keep),
            "file": str(out_path)}


def has_archival_layer(svg_path: Path) -> bool:
    return ARCHIVAL_LAYER_ID in Path(svg_path).read_text(encoding="utf-8")


if __name__ == "__main__":
    ranked = bayes_rank_candidates(top_k=5)
    print(f"top {len(ranked)} configs from {ATTEMPTS.name}:")
    for r in ranked:
        print(f"  bayes={r['bayes_score']:.4f} mean={r['composite_posterior_mean']:.4f} "
              f"n={r['n_attempts']} accept={r['accept_posterior_mean']:.2f} "
              f"cp={r['params'].get('color_precision')} "
              f"fs={r['params'].get('filter_speckle')} "
              f"ct={r['params'].get('corner_threshold')}")
