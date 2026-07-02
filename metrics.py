"""Measurement module for the Bernina Stitch Master optimization loop.

Pure stdlib + pyembroidery. Two entry points:
  - svg_metrics(path) -> dict
  - pes_metrics(path) -> dict

Both functions are robust: they never raise on a bad file. On failure they
return a dict shaped like {"valid": False, "error": "<message>", ...}.
"""

import math
import os
import re
import xml.etree.ElementTree as ET

try:
    import pyembroidery
    _HAVE_PYEMB = True
except Exception:  # pragma: no cover - environment dependent
    pyembroidery = None
    _HAVE_PYEMB = False


# All SVG path command letters.
_PATH_CMD_LETTERS = set("MmLlHhVvCcSsQqTtAaZz")
_PATH_CMD_RE = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]")


def _localname(tag):
    """Strip XML namespace, e.g. '{http://...}path' -> 'path'."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def svg_metrics(path):
    """Parse an SVG file with xml.etree and return structural metrics.

    Namespace-agnostic. Never raises.
    """
    result = {
        "artifact": os.path.basename(path),
        "kind": "svg",
        "valid": False,
    }
    try:
        result["bytes"] = os.path.getsize(path)
    except OSError as e:
        result["bytes"] = None
        result["error"] = str(e)
        return result

    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        result["error"] = str(e)
        return result

    root_local = _localname(root.tag).lower()
    # "svg-ish" root: either literally <svg> or a root that contains svg content.
    valid = root_local == "svg"

    path_count = 0
    group_count = 0
    element_count = 0
    node_count = 0

    for el in root.iter():
        element_count += 1
        local = _localname(el.tag).lower()
        if local == "path":
            path_count += 1
            d = el.get("d")
            if d:
                node_count += len(_PATH_CMD_RE.findall(d))
        elif local == "g":
            group_count += 1

    # Include the root element in the total element count if iter() excluded it.
    # ET.Element.iter() DOES include the root, so element_count is already total.

    if not valid:
        # Still report what we counted, but flag invalid root.
        valid = path_count > 0  # tolerate svg fragments that still have paths

    result.update({
        "valid": bool(valid),
        "path_count": path_count,
        "node_count": node_count,
        "group_count": group_count,
        "element_count": element_count,
    })
    return result


def _command_of(stitch):
    """Return the masked command code of a [x, y, cmd] stitch entry."""
    cmd = stitch[2]
    if _HAVE_PYEMB:
        return cmd & pyembroidery.COMMAND_MASK
    return cmd


def pes_metrics(path):
    """Read a PES file with pyembroidery and return embroidery metrics.

    PES coordinates are in 1/10 mm; lengths are divided by 10 to give mm.
    Never raises.
    """
    result = {
        "artifact": os.path.basename(path),
        "kind": "pes",
        "valid": False,
    }
    try:
        result["bytes"] = os.path.getsize(path)
    except OSError as e:
        result["bytes"] = None
        result["error"] = str(e)
        return result

    if not _HAVE_PYEMB:
        result["error"] = "pyembroidery not available"
        return result

    try:
        pattern = pyembroidery.read(path)
    except Exception as e:
        result["error"] = "read failed: %s" % e
        return result

    if pattern is None:
        result["error"] = "pyembroidery returned no pattern"
        return result

    try:
        stitches = pattern.stitches or []
        STITCH = pyembroidery.STITCH
        JUMP = pyembroidery.JUMP
        TRIM = pyembroidery.TRIM
        COLOR_CHANGE = pyembroidery.COLOR_CHANGE

        stitch_count = 0
        jump_count = 0
        trim_count = 0
        color_change_count = 0

        xs = []
        ys = []
        total_travel = 0.0
        prev = None

        for s in stitches:
            x, y = s[0], s[1]
            cmd = _command_of(s)
            if cmd == STITCH:
                stitch_count += 1
            elif cmd == JUMP:
                jump_count += 1
            elif cmd == TRIM:
                trim_count += 1
            elif cmd == COLOR_CHANGE:
                color_change_count += 1

            xs.append(x)
            ys.append(y)
            if prev is not None:
                dx = x - prev[0]
                dy = y - prev[1]
                total_travel += math.hypot(dx, dy)
            prev = (x, y)

        # Color count: prefer threadlist, fall back to color changes + 1.
        try:
            color_count = len(pattern.threadlist)
        except Exception:
            color_count = 0
        if color_count == 0:
            color_count = color_change_count + 1 if stitches else 0

        if xs and ys:
            width_mm = (max(xs) - min(xs)) / 10.0
            height_mm = (max(ys) - min(ys)) / 10.0
        else:
            width_mm = 0.0
            height_mm = 0.0

        total_travel_mm = total_travel / 10.0
        avg_stitch_length_mm = (total_travel_mm / stitch_count) if stitch_count else 0.0

        area_cm2 = (width_mm / 10.0) * (height_mm / 10.0)
        stitch_density_per_cm2 = (stitch_count / area_cm2) if area_cm2 > 0 else 0.0

        result.update({
            "valid": True,
            "stitch_count": stitch_count,
            "jump_count": jump_count,
            "trim_count": trim_count,
            "color_change_count": color_change_count,
            "color_count": color_count,
            "width_mm": round(width_mm, 3),
            "height_mm": round(height_mm, 3),
            "total_travel_mm": round(total_travel_mm, 3),
            "avg_stitch_length_mm": round(avg_stitch_length_mm, 4),
            "stitch_density_per_cm2": round(stitch_density_per_cm2, 3),
        })
        return result
    except Exception as e:  # defensive: never throw
        result["error"] = "metric computation failed: %s" % e
        return result


if __name__ == "__main__":
    import json
    import sys
    for p in sys.argv[1:]:
        if p.lower().endswith(".svg"):
            print(json.dumps(svg_metrics(p), indent=2))
        elif p.lower().endswith(".pes"):
            print(json.dumps(pes_metrics(p), indent=2))
        else:
            print("skip (unknown type):", p)
