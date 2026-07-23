#!/usr/bin/env python3
"""pipeline_v2.py — End-to-end: PNG → SVG → stitch plan → output files."""

import json
import sys
from pathlib import Path

import vectorizer_v2
import stitch_planner_v2


def run_pipeline(image_path: str) -> dict:
    """Full pipeline with output files."""
    image_path = Path(image_path)

    # Step 1: Vectorize
    vec_result = vectorizer_v2.vectorize_v2(str(image_path))
    if vec_result["status"] != "ok":
        return {"error": f"Vectorization failed: {vec_result}"}

    svg_path = Path(vec_result["svg_path"])

    # Step 2: Generate stitch plan
    svg_text = svg_path.read_text()
    stitch_plan = stitch_planner_v2.generate_stitch_plan(svg_text)

    # Step 3: Save stitch plan
    stem = image_path.stem
    plan_json = Path("stitch_plans") / f"{stem}_v2.json"
    plan_json.parent.mkdir(exist_ok=True)
    plan_json.write_text(json.dumps(stitch_plan, indent=2, default=str))

    # Step 4: Generate EXP format (simple stitch list)
    exp_path = Path("stitch_plans") / f"{stem}_v2.exp"
    exp_lines = []
    exp_lines.append("STITCH FILE")
    for obj in stitch_plan["objects"]:
        for x, y in obj["fill_stitches"] + obj["satin_stitches"]:
            # EXP format: simple XY coordinates
            exp_lines.append(f"{int(x*10)},{int(y*10)}")
    exp_path.write_text("\n".join(exp_lines))

    return {
        "image": str(image_path),
        "svg": str(svg_path),
        "stitch_plan": str(plan_json),
        "exp": str(exp_path),
        "regions": vec_result["regions"],
        "total_stitches": stitch_plan["total_stitches"],
        "density": stitch_plan["density_estimate"],
        "status": "ok",
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: pipeline_v2.py <image.png> [image2.png ...]")
        sys.exit(1)

    results = []
    for img_path in sys.argv[1:]:
        print(f"Processing {img_path}...")
        result = run_pipeline(img_path)
        results.append(result)
        print(json.dumps(result, indent=2))

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    ok_count = sum(1 for r in results if r.get("status") == "ok")
    print(f"Processed: {ok_count}/{len(results)} successful")
    for r in results:
        if r.get("status") == "ok":
            print(f"  ✓ {Path(r['image']).name}: {r['total_stitches']} stitches")
        else:
            print(f"  ✗ {r}")
