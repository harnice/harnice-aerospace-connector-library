import json
import math
import os
import subprocess
import sys

from harnice import fileio, state
from harnice.lists import rev_history
import harnice.project_types.part as part


def _load_step_utils():
    try:
        from harnice.utils import step_utils as module
        return module
    except ImportError:
        pass
    import importlib.util

    sibling = os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "..",
            "Harnice",
            "src",
            "harnice",
            "utils",
            "step_utils.py",
        )
    )
    spec = importlib.util.spec_from_file_location("harnice_step_utils", sibling)
    if spec is None or spec.loader is None:
        raise ImportError(
            "Generating STEP envelopes requires harnice.utils.step_utils "
            "(Harnice src/harnice/utils/step_utils.py)."
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


step_utils = _load_step_utils()

REVISION = "1"
DATE_STARTED = "8/7/26"
delete_pngs = True

# ---------------------------------------------------------------------------
# Datasheet / catalog sources (traceability)
# ---------------------------------------------------------------------------
# Primary (dimensions, finishes, how-to-order, designator H):
#   Glenair AS85049/88, /89, /90 — Straight, 45° and 90° Banding Backshells
#   with Self-Locking Coupling (U.S. CAGE 06324; sheet Rev. 06.28.23)
#   https://www.glenair.com/mil-spec/as85049-qualified-backshells-and-connector-accessories/pdf/as85049-88-and-as85049-89-and-as85049-90.pdf
#
# Straight body length L Max corroboration (1.35 in / 34.3 mm):
#   Milnec M85049/88 Type Banding Backshell datasheet
#   https://www.milnec.com/m85049/m85049-88-datasheet.pdf
#
# Mass: Glenair does not publish a full /88–90 weight table. Scaled from
# listed M85049/88-25W03 at 1.552 oz using C^2 * body length (F/G/H) from
# the same Glenair sheet. Stainless finish F uses density ratio 8.0/2.70.
#
# Assembly torque (not on Glenair /88–90 sheet) — SAE-AS85049 coupling thread
# strength, as published by Amphenol backshell catalogs:
#   https://www.amphenol.co.jp/military/catalog/pdf_howtoselectbackshell/Torque.pdf
#
# Circular backshell assembly wrench dash numbers:
#   Glenair 600-006 (std Al), 600-079 (anti-decoupling Al), 600-102 (std SS)
#   https://cdn.glenair.com/tools/pdf/a/600-006.pdf
# ---------------------------------------------------------------------------

# SVG px per inch — must match harnice part.py csys rendering (96 px/in)
PX_PER_IN = 96.0

# Origin is the right end of the banding knurl (drawings / attributes csys).
# The knurl itself extends −X so a terminated cable segment overlaps it.
# Straight (/88) body length from that origin to the connector face: Glenair
# drawing / Milnec L Max = 1.35 (34.3 mm). Banding platform length is not
# tabulated on the Glenair /88–90 sheet; 0.35 in is an estimate for
# drawing/csys silhouette only.
# STEP models are shifted so the connector mating face is at (0,0,0) with +X
# toward the connector; drawings keep the knurl-end origin above.
STRAIGHT_BODY_IN = 1.35
BAND_PLATFORM_IN = 0.35

# TABLE I — Shell Size, Cable Entry and Backshell Dimensions (inches / mm).
# Source: Glenair AS85049/88–90 PDF, Table I (link in header above).
# E entry 02/03; F/G for 45° (/89); H/J for 90° (/90). Entry 02 is N/A on 9 & 11.
SHELL_DATA = {
    9: {
        "a_thread": "M12 X 1 - 6H",
        "c_in": 0.860,
        "c_mm": 21.8,
        "e_02_in": None,
        "e_02_mm": None,
        "e_03_in": 0.250,
        "e_03_mm": 6.4,
        "f_in": 1.010,
        "f_mm": 25.7,
        "g_in": 1.160,
        "g_mm": 29.5,
        "h_in": 1.375,
        "h_mm": 34.9,
        "j_in": 1.417,
        "j_mm": 36.0,
    },
    11: {
        "a_thread": "M15 X 1 - 6H",
        "c_in": 0.990,
        "c_mm": 25.1,
        "e_02_in": None,
        "e_02_mm": None,
        "e_03_in": 0.312,
        "e_03_mm": 7.9,
        "f_in": 1.030,
        "f_mm": 26.2,
        "g_in": 1.190,
        "g_mm": 30.2,
        "h_in": 1.437,
        "h_mm": 36.5,
        "j_in": 1.480,
        "j_mm": 37.6,
    },
    13: {
        "a_thread": "M18 X 1 - 6H",
        "c_in": 1.160,
        "c_mm": 29.5,
        "e_02_in": 0.312,
        "e_02_mm": 7.9,
        "e_03_in": 0.438,
        "e_03_mm": 11.1,
        "f_in": 1.060,
        "f_mm": 26.9,
        "g_in": 1.210,
        "g_mm": 30.7,
        "h_in": 1.562,
        "h_mm": 39.7,
        "j_in": 1.553,
        "j_mm": 39.4,
    },
    15: {
        "a_thread": "M22 X 1 - 6H",
        "c_in": 1.280,
        "c_mm": 32.5,
        "e_02_in": 0.438,
        "e_02_mm": 11.1,
        "e_03_in": 0.562,
        "e_03_mm": 14.3,
        "f_in": 1.080,
        "f_mm": 27.4,
        "g_in": 1.240,
        "g_mm": 31.5,
        "h_in": 1.687,
        "h_mm": 42.8,
        "j_in": 1.614,
        "j_mm": 41.0,
    },
    17: {
        "a_thread": "M25 X 1 - 6H",
        "c_in": 1.410,
        "c_mm": 35.8,
        "e_02_in": 0.500,
        "e_02_mm": 12.7,
        "e_03_in": 0.625,
        "e_03_mm": 15.9,
        "f_in": 1.110,
        "f_mm": 28.2,
        "g_in": 1.260,
        "g_mm": 32.0,
        "h_in": 1.750,
        "h_mm": 44.5,
        "j_in": 1.678,
        "j_mm": 42.6,
    },
    19: {
        "a_thread": "M28 X 1 - 6H",
        "c_in": 1.520,
        "c_mm": 38.6,
        "e_02_in": 0.625,
        "e_02_mm": 15.9,
        "e_03_in": 0.750,
        "e_03_mm": 19.1,
        "f_in": 1.120,
        "f_mm": 28.4,
        "g_in": 1.270,
        "g_mm": 32.3,
        "h_in": 1.875,
        "h_mm": 47.6,
        "j_in": 1.733,
        "j_mm": 44.0,
    },
    21: {
        "a_thread": "M31 X 1 - 6H",
        "c_in": 1.640,
        "c_mm": 41.7,
        "e_02_in": 0.625,
        "e_02_mm": 15.9,
        "e_03_in": 0.812,
        "e_03_mm": 20.6,
        "f_in": 1.150,
        "f_mm": 29.2,
        "g_in": 1.300,
        "g_mm": 33.0,
        "h_in": 1.938,
        "h_mm": 49.2,
        "j_in": 1.796,
        "j_mm": 45.6,
    },
    23: {
        "a_thread": "M34 X 1 - 6H",
        "c_in": 1.770,
        "c_mm": 45.0,
        "e_02_in": 0.688,
        "e_02_mm": 17.5,
        "e_03_in": 0.938,
        "e_03_mm": 23.8,
        "f_in": 1.170,
        "f_mm": 29.7,
        "g_in": 1.330,
        "g_mm": 33.8,
        "h_in": 2.062,
        "h_mm": 52.4,
        "j_in": 1.859,
        "j_mm": 47.2,
    },
    25: {
        "a_thread": "M37 X 1 - 6H",
        "c_in": 1.890,
        "c_mm": 48.0,
        "e_02_in": 0.750,
        "e_02_mm": 19.1,
        "e_03_in": 1.000,
        "e_03_mm": 25.4,
        "f_in": 1.200,
        "f_mm": 30.5,
        "g_in": 1.350,
        "g_mm": 34.3,
        "h_in": 2.125,
        "h_mm": 54.0,
        "j_in": 1.919,
        "j_mm": 48.7,
    },
}

# TABLE II — Finish and Material (Glenair AS85049/88–90 PDF, Table II).
# Aluminum letter codes only; composite aliases (M, L, J, XC, YL, ZC, ZL) omitted.
# Finish F (Stainless Steel) is NOT on that aluminum Table II — retained for
# D38999 stainless/black-anodize pairing via find_backshell.
FINISHES = {
    "F": "Stainless Steel",
    "G": "Electroless Nickel (Space Grade)",
    "N": "Electroless Nickel",
    "P": "Cadmium Olive Drab over Electroless Nickel, Selective Plating",
    "W": "Cadmium Olive Drab",
    "X": "Nickel Fluorocarbon Polymer",
    "YP": "Pure Dense Electrodeposited Aluminum, Selective Plating",
    "Z": "Zinc Nickel",
    "ZP": "Zinc Nickel, Selective Plating",
}

# Approximate drawing colors. Visual appearance of shared D38999 / M85049
# finishes (electroless nickel, space-grade nickel, olive drab cadmium,
# stainless, black zinc nickel) is taken from:
# https://d38999.federalconnectors.com/
# M85049-only codes (N, P, X, YP, ZP) use the closest matching finish photo.
FINISH_DRAWING_COLORS = {
    "F": {  # Stainless steel — match D38999 class K
        "body": "#A3A4A0",
        "light": "#C8C9C5",
        "dark": "#6E6F6C",
        "specular": "#E8E9E6",
        "rim": "#4A4B48",
        "knurl": "#5C5D5A",
        "metallic": True,
    },
    "G": {  # Space-grade electroless nickel — satin silver
        "body": "#B4B9BE",
        "light": "#D8DCE0",
        "dark": "#7A8086",
        "specular": "#F2F4F6",
        "rim": "#555B61",
        "knurl": "#5E646A",
        "metallic": True,
    },
    "N": {  # Electroless nickel — bright chrome-like silver (D38999 F)
        "body": "#C5CAD0",
        "light": "#E8ECF0",
        "dark": "#6E757C",
        "specular": "#FBFCFF",
        "rim": "#4A5056",
        "knurl": "#5A6168",
        "metallic": True,
    },
    "P": {  # Cadmium olive drab, selective — khaki / greenish-bronze
        "body": "#6B6C38",
        "light": "#8E8F52",
        "dark": "#3E3F22",
        "specular": "#B8B86A",
        "rim": "#2C2D18",
        "knurl": "#2E2F16",
        "metallic": False,
    },
    "W": {  # Cadmium olive drab
        "body": "#6B6C38",
        "light": "#8E8F52",
        "dark": "#3E3F22",
        "specular": "#B8B86A",
        "rim": "#2C2D18",
        "knurl": "#2E2F16",
        "metallic": False,
    },
    "X": {  # Nickel fluorocarbon polymer — duller grey (D38999 T)
        "body": "#9B9E9A",
        "light": "#B8BBB7",
        "dark": "#5E615D",
        "specular": "#D0D3CF",
        "rim": "#454844",
        "knurl": "#4E514D",
        "metallic": False,
    },
    "YP": {  # Pure dense electrodeposited aluminum
        "body": "#C0C4C8",
        "light": "#E0E4E8",
        "dark": "#7A7F83",
        "specular": "#F5F7F9",
        "rim": "#555A5E",
        "knurl": "#5E6367",
        "metallic": True,
    },
    "Z": {  # Zinc nickel — deep charcoal (D38999 Z)
        "body": "#3D3E40",
        "light": "#5A5B5D",
        "dark": "#1E1F21",
        "specular": "#7A7B7D",
        "rim": "#141516",
        "knurl": "#6A6B6D",
        "metallic": False,
    },
    "ZP": {  # Zinc nickel, selective
        "body": "#3D3E40",
        "light": "#5A5B5D",
        "dark": "#1E1F21",
        "specular": "#7A7B7D",
        "rim": "#141516",
        "knurl": "#6A6B6D",
        "metallic": False,
    },
}
_DEFAULT_FINISH_COLORS = {
    "body": "#C0C0C0",
    "light": "#D8D8D8",
    "dark": "#A8A8A8",
    "specular": "#F0F0F0",
    "rim": "#444444",
    "knurl": "#555555",
    "metallic": True,
}
# P / YP / ZP leave the banding platform electroless nickel (selective plating),
# as on typical /88–/90 hardware photos.
SELECTIVE_FINISHES = {"P", "YP", "ZP"}
STROKE_COLOR = "#222222"
STROKE_WIDTH = 1.5

# Basic part number → geometry. Glenair how-to-order: /88 straight, /89 45°, /90 90°.
ORIENTATIONS = {
    "88": "straight",
    "89": "45",
    "90": "90",
}

# Assembly torque to connector (in-lbs) by connector shell size.
# Not listed on the Glenair /88–90 drawing. Values follow SAE-AS85049 coupling
# thread strength as tabulated by Amphenol (see Torque.pdf link in header):
# shells 8–19 → 40 in-lbs; 20–25 → 80 in-lbs (we map 38999 sizes 9–19 / 21–25).
TORQUE_IN_LBS = {
    9: 40,
    11: 40,
    13: 40,
    15: 40,
    17: 40,
    19: 40,
    21: 80,
    23: 80,
    25: 80,
}

# Glenair circular backshell assembly wrenches — dash ↔ shell size from
# https://cdn.glenair.com/tools/pdf/a/600-006.pdf
# /88–90 are self-locking → anti-decoupling 600-079 for aluminum finishes;
# stainless (finish F) uses standard stainless wrench 600-102.
WRENCH_DASH_STANDARD = {  # 600-006 / 600-102 (dash 08→08/09 … 24→24/25)
    9: "08",
    11: "10",
    13: "12",
    15: "14",
    17: "16",
    19: "18",
    21: "20",
    23: "22",
    25: "24",
}
WRENCH_DASH_ANTI_DECOUPLING = {  # 600-079 (dash 01→08/09 … 10→24/25)
    9: "01",
    11: "02",
    13: "03",
    15: "04",
    17: "05",
    19: "06",
    21: "07",
    23: "08",
    25: "10",
}

# Polar flagnotes about the silhouette centroid, every 15°.
# Angled parts keep only outside-of-bend rays; numbering starts at the exterior
# bisector and interleaves outward (flagnote-1 at center of the outside arc).
FLAGNOTE_ANGLES_DEG = list(range(-180, 180, 15))
FLAGNOTE_OFFSET_IN = 2.0  # flagnotes sit this far beyond the farthest leader tip
MIN_LEADER_RADIUS_IN = 0.2  # drop rays that skim too close to the centroid
MIN_FLAGNOTE_CLEARANCE_IN = 0.5  # drop flagnotes that land too close to the part


def entry_dia(shell_size, entry_size):
    data = SHELL_DATA[shell_size]
    if entry_size == "02":
        return data["e_02_in"], data["e_02_mm"]
    if entry_size == "03":
        return data["e_03_in"], data["e_03_mm"]
    raise ValueError(f"Unknown entry size '{entry_size}'")


def valid_entries(shell_size):
    data = SHELL_DATA[shell_size]
    entries = []
    if data["e_02_in"] is not None:
        entries.append("02")
    if data["e_03_in"] is not None:
        entries.append("03")
    return entries


def px_in(inches):
    return inches * PX_PER_IN


def finish_palette(finish):
    p = FINISH_DRAWING_COLORS.get((finish or "").upper(), _DEFAULT_FINISH_COLORS)
    return {**_DEFAULT_FINISH_COLORS, **p}


def _knurl_pattern_id(part_number, suffix):
    # Matplotlib's SVG parser lowercases url(#id) lookups, so ids must be lowercase.
    return f"{part_number}-{suffix}".lower()


def _diamond_pattern(pid, color):
    return (
        f'<pattern id="{pid}" width="8" height="8" patternUnits="userSpaceOnUse">\n'
        f'  <path d="M0,8 L8,0 M-2,2 L2,-2 M6,10 L10,6" '
        f'stroke="{color}" stroke-width="0.85" fill="none"/>\n'
        f'  <path d="M0,0 L8,8 M-2,6 L2,10 M6,-2 L10,2" '
        f'stroke="{color}" stroke-width="0.85" fill="none"/>\n'
        f"</pattern>"
    )


def finish_svg_defs(part_number, finish):
    """Knurl patterns only. Finish hues from federalconnectors.com;
    knurl / nut / band layout from typical M85049/88 /89 /90 hardware photos.
    """
    body = finish_palette(finish)
    selective = (finish or "").upper() in SELECTIVE_FINISHES
    band = finish_palette("N") if selective else body
    return "\n".join(
        [
            "<!-- Finish colors approximated from https://d38999.federalconnectors.com/ -->",
            "<!-- Knurl and section details from typical M85049/88 /89 /90 hardware -->",
            "<defs>",
            _diamond_pattern(_knurl_pattern_id(part_number, "knurl-diamond"), band["knurl"]),
            _diamond_pattern(_knurl_pattern_id(part_number, "knurl-diamond-nut"), body["knurl"]),
            "</defs>",
        ]
    )


def finish_fills(part_number, finish):
    body = finish_palette(finish)
    band = finish_palette("N") if (finish or "").upper() in SELECTIVE_FINISHES else body
    return {
        "body": body["body"],
        "nut": body["dark"],
        "band": band["body"],
        "diamond": band["knurl"],
        "diamond_nut": body["knurl"],
        "rim": body["rim"],
        "selective": (finish or "").upper() in SELECTIVE_FINISHES,
    }


def _stroke_attr(stroke, stroke_width):
    if stroke is None:
        return ' stroke="none"'
    return f' stroke="{stroke}" stroke-width="{stroke_width}"'


def _rect(x, y, w, h, fill="#C0C0C0", stroke=STROKE_COLOR, stroke_width=STROKE_WIDTH, extra=""):
    extra_attr = f" {extra}" if extra else ""
    return (
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
        f'fill="{fill}"{_stroke_attr(stroke, stroke_width)}{extra_attr}/>'
    )


def _poly(points, fill="#C0C0C0", stroke=STROKE_COLOR, stroke_width=STROKE_WIDTH, extra=""):
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    extra_attr = f" {extra}" if extra else ""
    return (
        f'<polygon points="{pts}" fill="{fill}"'
        f'{_stroke_attr(stroke, stroke_width)}{extra_attr}/>'
    )


def _weld_line(x1, y1, x2, y2):
    """Faint miter/weld across a 45° or 90° elbow."""
    return (
        f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="#000000" stroke-width="1" opacity="0.05"/>'
    )


def banding_ribs(x0, y_top, y_bot, length, count=5):
    """Kept for call-site compatibility; knurl patterns replace these marks."""
    return ""


def platform_od_in(shell_size, entry_size):
    """Banding platform outer diameter (inches), slightly over E dia."""
    e_in, _ = entry_dia(shell_size, entry_size)
    c_in = SHELL_DATA[shell_size]["c_in"]
    return max(e_in + 0.16, c_in * 0.45)


def straight_backshell_svg(part_number, shell_size, entry_size, finish=None):
    """Knurl in −X under the cable; origin at right end of knurl; body +X to connector."""
    data = SHELL_DATA[shell_size]
    fills = finish_fills(part_number, finish)

    c = px_in(data["c_in"])
    e_od = px_in(platform_od_in(shell_size, entry_size))
    body_len = px_in(STRAIGHT_BODY_IN)
    band_len = px_in(BAND_PLATFORM_IN)
    nut_len = body_len * 0.28
    taper_len = body_len * 0.12
    mid_len = body_len - nut_len - taper_len

    half_c = c / 2
    half_e = e_od / 2
    half_mid = (half_c + half_e) / 2

    # Origin at right end of knurl; cable-side platform extends −X
    x0 = -band_len
    x1 = 0.0
    x2 = taper_len
    x3 = taper_len + mid_len
    x4 = body_len

    outline = [
        (x0, -half_e),
        (x1, -half_e),
        (x2, -half_mid),
        (x3, -half_mid),
        (x3, -half_c),
        (x4, -half_c),
        (x4, half_c),
        (x3, half_c),
        (x3, half_mid),
        (x2, half_mid),
        (x1, half_e),
        (x0, half_e),
    ]

    lip = max(3.0, band_len * 0.12)
    knurl_w = band_len - lip
    nut_knurl_w = nut_len * 0.70

    parts = [
        finish_svg_defs(part_number, finish),
        _poly(outline, fill=fills["body"]),
        _rect(x3, -half_c, nut_len, c, fill=fills["nut"], stroke=None),
        _rect(x3, -half_c, nut_knurl_w, c, fill=fills["diamond_nut"], stroke=None, extra='opacity="0.55"'),
        _rect(x0, -half_e, band_len, e_od, fill=fills["band"], stroke=None) if fills["selective"] else "",
        _rect(x0 + lip, -half_e, knurl_w, e_od, fill=fills["diamond"], stroke=None, extra='opacity="0.55"'),
        _poly(outline, fill="none"),
    ]

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="400" height="400">
<g id="{part_number}-drawing-contents-start">
{chr(10).join(p for p in parts if p)}
</g>
<g id="{part_number}-drawing-contents-end">
</g>
</svg>'''


def fortyfive_backshell_svg(part_number, shell_size, entry_size, finish=None):
    """Knurl in −X under the cable; origin at right end of knurl; body +X then 45° to connector."""
    data = SHELL_DATA[shell_size]
    fills = finish_fills(part_number, finish)

    c = px_in(data["c_in"])
    e_od = px_in(platform_od_in(shell_size, entry_size))
    f = px_in(data["f_in"])
    g = px_in(data["g_in"])
    band_len = px_in(BAND_PLATFORM_IN)
    nut_len = f * 0.35

    half_c = c / 2
    half_e = e_od / 2
    angle = math.radians(45)
    cos_a, sin_a = math.cos(angle), math.sin(angle)

    # SVG y is down; negative Y is up
    def offset_point(cx, cy, tx, ty, dist):
        nx, ny = -ty, tx
        return cx + nx * dist, cy + ny * dist

    # Centerline: cable entry (−band, 0) → origin (0,0) → +X by G−band → 45° to connector
    c0 = (-band_len, 0.0)
    c1 = (g - band_len, 0.0)
    c2 = (g - band_len + f * cos_a, -f * sin_a)

    w0, w1, w2 = half_e, (half_c + half_e) / 2, half_c

    top = [
        offset_point(*c0, 1, 0, w0),
        offset_point(*c1, 1, 0, w1),
        offset_point(
            c2[0] - nut_len * cos_a, c2[1] + nut_len * sin_a, cos_a, -sin_a, w2
        ),
        offset_point(*c2, cos_a, -sin_a, w2),
    ]
    bot = [
        offset_point(*c2, cos_a, -sin_a, -w2),
        offset_point(
            c2[0] - nut_len * cos_a, c2[1] + nut_len * sin_a, cos_a, -sin_a, -w2
        ),
        offset_point(*c1, 1, 0, -w1),
        offset_point(*c0, 1, 0, -w0),
    ]
    outline = top + bot

    nut_x = c2[0] - nut_len * cos_a
    nut_y = c2[1] + nut_len * sin_a
    nut_pts = [
        offset_point(nut_x, nut_y, cos_a, -sin_a, half_c),
        offset_point(*c2, cos_a, -sin_a, half_c),
        offset_point(*c2, cos_a, -sin_a, -half_c),
        offset_point(nut_x, nut_y, cos_a, -sin_a, -half_c),
    ]
    knurl_frac = 0.72
    nut_knurl_pts = [
        offset_point(nut_x, nut_y, cos_a, -sin_a, half_c),
        offset_point(
            nut_x + nut_len * knurl_frac * cos_a,
            nut_y - nut_len * knurl_frac * sin_a,
            cos_a,
            -sin_a,
            half_c,
        ),
        offset_point(
            nut_x + nut_len * knurl_frac * cos_a,
            nut_y - nut_len * knurl_frac * sin_a,
            cos_a,
            -sin_a,
            -half_c,
        ),
        offset_point(nut_x, nut_y, cos_a, -sin_a, -half_c),
    ]

    lip = max(3.0, band_len * 0.12)

    parts = [
        finish_svg_defs(part_number, finish),
        _poly(outline, fill=fills["body"]),
        _poly(nut_pts, fill=fills["nut"], stroke=None),
        _poly(nut_knurl_pts, fill=fills["diamond_nut"], stroke=None, extra='opacity="0.55"'),
        _rect(-band_len, -half_e, band_len, e_od, fill=fills["band"], stroke=None) if fills["selective"] else "",
        _rect(-band_len + lip, -half_e, band_len - lip, e_od, fill=fills["diamond"], stroke=None, extra='opacity="0.55"'),
        _weld_line(*offset_point(*c1, 1, 0, w1), *offset_point(*c1, 1, 0, -w1)),
        _poly(outline, fill="none"),
    ]

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="400" height="400">
<g id="{part_number}-drawing-contents-start">
{chr(10).join(p for p in parts if p)}
</g>
<g id="{part_number}-drawing-contents-end">
</g>
</svg>'''


def ninety_backshell_svg(part_number, shell_size, entry_size, finish=None):
    """Knurl in −X under the cable; origin at right end of knurl; body +X then +Y to connector."""
    data = SHELL_DATA[shell_size]
    fills = finish_fills(part_number, finish)

    c = px_in(data["c_in"])
    e_od = px_in(platform_od_in(shell_size, entry_size))
    h = px_in(data["h_in"])
    j = px_in(data["j_in"])
    band_len = px_in(BAND_PLATFORM_IN)
    nut_len = h * 0.30

    half_c = c / 2
    half_e = e_od / 2

    # Origin at right of knurl; bend at (J − band, 0); connector face at that x, −H
    x_bend = j - band_len
    y_conn = -h  # SVG: negative Y is up

    outline = [
        (-band_len, -half_e),
        (x_bend - half_c, -half_e),
        (x_bend - half_c, y_conn),
        (x_bend + half_c, y_conn),
        (x_bend + half_c, half_e),
        (-band_len, half_e),
    ]

    lip = max(3.0, band_len * 0.12)
    nut_knurl_h = nut_len * 0.70

    horiz = _rect(
        -band_len, -half_e, x_bend + half_c + band_len, e_od, fill=fills["body"], stroke=None
    )
    vert = _rect(
        x_bend - half_c,
        y_conn,
        c,
        h + half_e,
        fill=fills["body"],
        stroke=None,
    )

    parts = [
        finish_svg_defs(part_number, finish),
        horiz,
        vert,
        _rect(x_bend - half_c, y_conn, c, nut_len, fill=fills["nut"], stroke=None),
        _rect(
            x_bend - half_c,
            y_conn + nut_len - nut_knurl_h,
            c,
            nut_knurl_h,
            fill=fills["diamond_nut"],
            stroke=None,
            extra='opacity="0.55"',
        ),
        _rect(-band_len, -half_e, band_len, e_od, fill=fills["band"], stroke=None) if fills["selective"] else "",
        _rect(-band_len + lip, -half_e, band_len - lip, e_od, fill=fills["diamond"], stroke=None, extra='opacity="0.55"'),
        _weld_line(x_bend - half_c, -half_e, x_bend + half_c, half_e),
        _poly(outline, fill="none"),
    ]

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="400" height="400">
<g id="{part_number}-drawing-contents-start">
{chr(10).join(p for p in parts if p)}
</g>
<g id="{part_number}-drawing-contents-end">
</g>
</svg>'''


INCH_TO_MM = 25.4


def backshell_envelope_mm(orientation, shell_size, entry_size):
    """Low-fidelity 3D envelope in millimetres.

    Same silhouette as the 2D drawing (including the banding platform in −X),
    without knurl texture. Origin is the right end of that platform; body +X
    toward the connector.
    """
    data = SHELL_DATA[shell_size]
    half_c = data["c_in"] * INCH_TO_MM / 2.0
    half_e = platform_od_in(shell_size, entry_size) * INCH_TO_MM / 2.0
    band = BAND_PLATFORM_IN * INCH_TO_MM

    if orientation == "straight":
        body = STRAIGHT_BODY_IN * INCH_TO_MM
        nut = body * 0.28
        taper = body * 0.12
        mid = body - nut - taper
        half_mid = (half_c + half_e) / 2.0
        stations = [
            (-band, half_e),
            (0.0, half_e),
            (taper, half_mid),
            (taper + mid, half_mid),
            (taper + mid, half_c),
            (body, half_c),
        ]
        return "revolution", stations, None

    if orientation == "45":
        f_mm = data["f_in"] * INCH_TO_MM
        g_mm = data["g_in"] * INCH_TO_MM
        return "elbow", {
            "entry": (-band, 0.0, 0.0),
            "corner": (g_mm - band, 0.0, 0.0),
            "angle_deg": 45,
            "exit_length": f_mm,
            "r_entry": half_e,
            "r_body": (half_c + half_e) / 2.0,
            "r_nut": half_c,
            "nut_length": f_mm * 0.35,
        }, None

    if orientation == "90":
        h_mm = data["h_in"] * INCH_TO_MM
        j_mm = data["j_in"] * INCH_TO_MM
        return "elbow", {
            "entry": (-band, 0.0, 0.0),
            "corner": (j_mm - band, 0.0, 0.0),
            "angle_deg": 90,
            "exit_length": h_mm,
            "r_entry": half_e,
            "r_body": (half_c + half_e) / 2.0,
            "r_nut": half_c,
            "nut_length": h_mm * 0.30,
        }, None

    raise ValueError(f"Unknown orientation '{orientation}'")


def _ocp_move_connector_face_to_origin(shape, face_xyz, axis_xy):
    """Translate ``face_xyz`` to the origin and align ``axis_xy`` with +X.

    After this, the connector mating face is at (0,0,0) and +X points along the
    coupling axis toward the connector (backshell body lies in −X).
    """
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt, gp_Trsf, gp_Vec

    fx, fy, fz = float(face_xyz[0]), float(face_xyz[1]), float(face_xyz[2])
    ux, uy = float(axis_xy[0]), float(axis_xy[1])
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(-fx, -fy, -fz))
    shape = BRepBuilderAPI_Transform(shape, trsf, True).Shape()
    angle = math.atan2(uy, ux)
    if abs(angle) > 1e-9:
        rot = gp_Trsf()
        rot.SetRotation(gp_Ax1(gp_Pnt(0.0, 0.0, 0.0), gp_Dir(0.0, 0.0, 1.0)), -angle)
        shape = BRepBuilderAPI_Transform(shape, rot, True).Shape()
    return shape


def write_part_step(rev_dir, part_number, orientation, shell_size, entry_size):
    """Write STEP with origin on the connector mating face (+X toward connector)."""
    kind, geom, _radii = backshell_envelope_mm(orientation, shell_size, entry_size)
    path = os.path.join(rev_dir, f"{part_number}-rev{REVISION}-model.step")
    description = f"M85049/{orientation} low-fidelity envelope (connector-face origin)"
    if kind == "revolution":
        face_x = float(geom[-1][0])
        stations = [(x - face_x, radius) for x, radius in geom]
        step_utils.write_revolution_step(
            path, part_number, stations, description=description
        )
        return path
    if kind == "elbow":
        layout = step_utils._elbow_layout(
            geom["entry"],
            geom["corner"],
            geom["angle_deg"],
            geom["exit_length"],
            geom["nut_length"],
        )
        try:
            shape = step_utils._ocp_elbow_solid(
                geom["entry"],
                geom["r_entry"],
                geom["r_body"],
                geom["r_nut"],
                geom["nut_length"],
                layout,
            )
            shape = _ocp_move_connector_face_to_origin(
                shape, layout["p_face"], (layout["ux"], layout["uy"])
            )
            step_utils._ocp_write_shape(shape, path, part_number)
            return path
        except ImportError:
            # Fallback mesh path still uses the knurl-frame elbow writer.
            step_utils.write_elbow_step(
                path, part_number, description=description, **geom
            )
            return path
    raise ValueError(f"Unknown M85049 envelope kind {kind!r}")


def csys_6dof_mm(x_mm, y_mm, z_mm, rx=0.0, ry=0.0, rz=0.0):
    """Child csys pose in inches/degrees relative to the STEP (part) origin.

    (x, y, z) locates the child origin. (rx, ry, rz) are intrinsic XYZ Euler
    rotations of the child axes, so the pose fully constrains 6 DOF.
    """
    return {
        "x": round(float(x_mm) / INCH_TO_MM, 4),
        "y": round(float(y_mm) / INCH_TO_MM, 4),
        "z": round(float(z_mm) / INCH_TO_MM, 4),
        "rx": round(float(rx), 4),
        "ry": round(float(ry), 4),
        "rz": round(float(rz), 4),
    }


def bundle_mate_csys_3d(orientation, shell_size, entry_size):
    """Cable-entry face in the STEP frame (inches).

    Same plane as the STEP banding-platform free end. +X into the backshell
    (toward the connector), +Z matching the part origin. Straight parts keep
    identity orientation; 45°/90° rotate about Z so +X follows the entry axis.
    """
    kind, geom, _radii = backshell_envelope_mm(orientation, shell_size, entry_size)
    if kind == "revolution":
        face_x = float(geom[-1][0])
        entry_x = float(geom[0][0])
        return csys_6dof_mm(entry_x - face_x, 0.0, 0.0)
    layout = step_utils._elbow_layout(
        geom["entry"],
        geom["corner"],
        geom["angle_deg"],
        geom["exit_length"],
        geom["nut_length"],
    )
    fx, fy, fz = layout["p_face"]
    ex, ey, ez = geom["entry"]
    px, py, pz = ex - fx, ey - fy, ez - fz
    ang = math.atan2(layout["uy"], layout["ux"])
    ca, sa = math.cos(-ang), math.sin(-ang)
    return csys_6dof_mm(
        px * ca - py * sa,
        px * sa + py * ca,
        pz,
        rz=math.degrees(-ang),
    )



def backshell_svg(part_number, orientation, shell_size, entry_size, finish=None):
    if orientation == "straight":
        return straight_backshell_svg(part_number, shell_size, entry_size, finish)
    if orientation == "45":
        return fortyfive_backshell_svg(part_number, shell_size, entry_size, finish)
    if orientation == "90":
        return ninety_backshell_svg(part_number, shell_size, entry_size, finish)
    raise ValueError(f"Unknown orientation '{orientation}'")


def connector_csys(orientation, shell_size):
    """Connector mating face csys in inches.

    Origin is the right end of the cable-side knurl. Knurl/cable extend −X;
    body inline with the cable extends +X (then up for angled parts).
    """
    data = SHELL_DATA[shell_size]
    if orientation == "straight":
        return {"x": STRAIGHT_BODY_IN, "y": 0, "angle": 0, "rotation": 0}
    if orientation == "45":
        f, g = data["f_in"], data["g_in"]
        return {
            "x": (g - BAND_PLATFORM_IN) + f * math.cos(math.radians(45)),
            "y": f * math.sin(math.radians(45)),
            "angle": 0,
            "rotation": 45,
        }
    if orientation == "90":
        return {
            "x": data["j_in"] - BAND_PLATFORM_IN,
            "y": data["h_in"],
            "angle": 0,
            "rotation": 90,
        }
    raise ValueError(f"Unknown orientation '{orientation}'")


def part_perimeter_inches(orientation, shell_size, entry_size):
    """Outer silhouette vertices in inches (math coords, +Y up), CCW, closed.

    Must match the drawing outline in backshell_svg so leader tips land on the
    visible edge.
    """
    data = SHELL_DATA[shell_size]
    half_c = data["c_in"] / 2
    half_e = platform_od_in(shell_size, entry_size) / 2

    if orientation == "straight":
        body = STRAIGHT_BODY_IN
        band = BAND_PLATFORM_IN
        nut = body * 0.28
        taper = body * 0.12
        mid = body - nut - taper
        half_mid = (half_c + half_e) / 2
        # Same stepped outline as straight_backshell_svg (inches, +Y up)
        x0 = -band
        x1 = 0.0
        x2 = taper
        x3 = taper + mid
        x4 = body
        pts = [
            (x0, half_e),
            (x1, half_e),
            (x2, half_mid),
            (x3, half_mid),
            (x3, half_c),
            (x4, half_c),
            (x4, -half_c),
            (x3, -half_c),
            (x3, -half_mid),
            (x2, -half_mid),
            (x1, -half_e),
            (x0, -half_e),
        ]
    elif orientation == "45":
        f, g = data["f_in"], data["g_in"]
        a = math.radians(45)
        cos_a, sin_a = math.cos(a), math.sin(a)

        # Centerline: (−band,0) → (G−band,0) → connector
        def off(cx, cy, tx, ty, dist):
            nx, ny = -ty, tx
            return (cx + nx * dist, cy + ny * dist)

        c0 = (-BAND_PLATFORM_IN, 0.0)
        c1 = (g - BAND_PLATFORM_IN, 0.0)
        c2 = (g - BAND_PLATFORM_IN + f * cos_a, f * sin_a)
        w0, w1, w2 = half_e, (half_c + half_e) / 2, half_c
        pts = [
            off(*c0, 1, 0, w0),
            off(*c1, 1, 0, w1),
            off(*c2, cos_a, sin_a, w2),
            off(*c2, cos_a, sin_a, -w2),
            off(*c1, 1, 0, -w1),
            off(*c0, 1, 0, -w0),
        ]
    elif orientation == "90":
        h, j = data["h_in"], data["j_in"]
        band = BAND_PLATFORM_IN
        # Cable entry at −band; bend at (J−band, 0); connector at (J−band, H)
        pts = [
            (-band, half_e),
            (j - band - half_c, half_e),
            (j - band - half_c, h),
            (j - band + half_c, h),
            (j - band + half_c, -half_e),
            (-band, -half_e),
        ]
    else:
        raise ValueError(f"Unknown orientation '{orientation}'")

    if pts[0] != pts[-1]:
        pts = pts + [pts[0]]
    return pts


def connector_mating_face_inches(orientation, shell_size, entry_size):
    """Endpoints of the connector mating face segment (inches, +Y up)."""
    data = SHELL_DATA[shell_size]
    half_c = data["c_in"] / 2

    if orientation == "straight":
        return (STRAIGHT_BODY_IN, half_c), (STRAIGHT_BODY_IN, -half_c)

    if orientation == "45":
        f, g = data["f_in"], data["g_in"]
        a = math.radians(45)
        cos_a, sin_a = math.cos(a), math.sin(a)
        c2 = (g - BAND_PLATFORM_IN + f * cos_a, f * sin_a)
        # Face is perpendicular to the F centerline at the connector end
        nx, ny = -sin_a, cos_a
        return (
            (c2[0] + nx * half_c, c2[1] + ny * half_c),
            (c2[0] - nx * half_c, c2[1] - ny * half_c),
        )

    if orientation == "90":
        h, j = data["h_in"], data["j_in"] - BAND_PLATFORM_IN
        return (j - half_c, h), (j + half_c, h)

    raise ValueError(f"Unknown orientation '{orientation}'")


def cable_entry_face_inches(orientation, shell_size, entry_size):
    """Endpoints of the cable-entry face segment (inches, +Y up)."""
    half_e = platform_od_in(shell_size, entry_size) / 2
    x = -BAND_PLATFORM_IN
    return (x, half_e), (x, -half_e)


def inside_bend_edges_inches(orientation, shell_size, entry_size):
    """Perimeter edges on the inside of a 45°/90° bend (inches, +Y up).

    Used when ray-casting from the centroid (straight unused). Straight parts
    have no bend; return [].
    """
    if orientation == "straight":
        return []

    data = SHELL_DATA[shell_size]
    half_c = data["c_in"] / 2
    half_e = platform_od_in(shell_size, entry_size) / 2

    if orientation == "90":
        h, j = data["h_in"], data["j_in"] - BAND_PLATFORM_IN
        band = BAND_PLATFORM_IN
        return [
            ((-band, half_e), (j - half_c, half_e)),
            ((j - half_c, half_e), (j - half_c, h)),
        ]

    if orientation == "45":
        f, g = data["f_in"], data["g_in"]
        a = math.radians(45)
        cos_a, sin_a = math.cos(a), math.sin(a)

        def off(cx, cy, tx, ty, dist):
            nx, ny = -ty, tx
            return (cx + nx * dist, cy + ny * dist)

        c0 = (-BAND_PLATFORM_IN, 0.0)
        c1 = (g - BAND_PLATFORM_IN, 0.0)
        c2 = (g - BAND_PLATFORM_IN + f * cos_a, f * sin_a)
        w0, w1, w2 = half_e, (half_c + half_e) / 2, half_c
        # +offset side of both arms faces the concave inside of the bend.
        p0 = off(*c0, 1, 0, w0)
        p1 = off(*c1, 1, 0, w1)
        p2 = off(*c2, cos_a, sin_a, w2)
        return [(p0, p1), (p1, p2)]

    raise ValueError(f"Unknown orientation '{orientation}'")


def leader_center_inches(orientation, shell_size, entry_size):
    """Polar origin for flagnote leaders: silhouette area centroid (inches, +Y up)."""
    return _polygon_centroid(
        part_perimeter_inches(orientation, shell_size, entry_size)
    )


def exterior_bisector_deg(orientation):
    """Preferred start angle (deg) for flagnote-1 about the centroid."""
    if orientation == "straight":
        return 90.0  # middle of the top face
    if orientation == "90":
        # Exterior bisector of the L outer corner (body occupies ~90°…180°).
        return -45.0
    if orientation == "45":
        # Outward normal of the 0°→45° bend.
        return (0.0 + 45.0) / 2.0 - 90.0  # −67.5°
    raise ValueError(f"Unknown orientation '{orientation}'")


def _angle_diff_deg(a, b):
    """Signed difference a−b in (−180, 180]."""
    d = (a - b + 180.0) % 360.0 - 180.0
    if d <= -180.0:
        d += 360.0
    return d


def flagnote_angles_deg(orientation):
    """Candidate polar angles (deg) about the centroid, outside-of-bend for angled."""
    if orientation == "straight":
        return list(FLAGNOTE_ANGLES_DEG)

    if orientation == "90":
        # From centroid, outside faces are bottom (−Y) and outer vertical (+X).
        # Keep the open half toward the convex exterior (about bisector −45°).
        bisector = exterior_bisector_deg(orientation)
        half_span = 135.0  # ~270° exterior sector
        return [
            a
            for a in FLAGNOTE_ANGLES_DEG
            if abs(_angle_diff_deg(a, bisector)) <= half_span + 1e-9
        ]

    if orientation == "45":
        bisector = exterior_bisector_deg(orientation)
        half_span = 90.0  # ~180° convex-outside arc
        return [
            a
            for a in FLAGNOTE_ANGLES_DEG
            if abs(_angle_diff_deg(a, bisector)) <= half_span + 1e-9
        ]

    raise ValueError(f"Unknown orientation '{orientation}'")


def _order_angles_from_bisector(angles, bisector):
    """flagnote-1 nearest bisector, then alternate sides outward (2,3,4,5,…)."""
    if not angles:
        return []
    # Seed with the angle closest to the exterior bisector
    first = min(angles, key=lambda a: abs(_angle_diff_deg(a, bisector)))
    first_diff = _angle_diff_deg(first, bisector)
    left = sorted(
        (a for a in angles if _angle_diff_deg(a, bisector) < first_diff - 1e-9),
        key=lambda a: -_angle_diff_deg(a, bisector),
    )
    right = sorted(
        (a for a in angles if _angle_diff_deg(a, bisector) > first_diff + 1e-9),
        key=lambda a: _angle_diff_deg(a, bisector),
    )
    ordered = [first]
    for i in range(max(len(left), len(right))):
        if i < len(left):
            ordered.append(left[i])
        if i < len(right):
            ordered.append(right[i])
    return ordered


def _points_close(a, b, tol=1e-4):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def _same_segment(a0, a1, b0, b1, tol=1e-4):
    return (_points_close(a0, b0, tol) and _points_close(a1, b1, tol)) or (
        _points_close(a0, b1, tol) and _points_close(a1, b0, tol)
    )


def _polygon_centroid(pts):
    """Area centroid of a polygon in inches (+Y up). pts may be closed."""
    verts = pts[:-1] if pts and pts[0] == pts[-1] else pts
    n = len(verts)
    if n < 3:
        if not verts:
            return 0.0, 0.0
        return (
            sum(v[0] for v in verts) / n,
            sum(v[1] for v in verts) / n,
        )

    area2 = 0.0  # 2 * signed area
    cx = cy = 0.0
    for i in range(n):
        x0, y0 = verts[i]
        x1, y1 = verts[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        area2 += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross

    if abs(area2) < 1e-12:
        return (
            sum(v[0] for v in verts) / n,
            sum(v[1] for v in verts) / n,
        )
    inv = 1.0 / (3.0 * area2)
    return cx * inv, cy * inv


def _point_segment_distance(px, py, a, b):
    ax, ay = a
    bx, by = b
    ex, ey = bx - ax, by - ay
    L2 = ex * ex + ey * ey
    if L2 < 1e-18:
        return math.hypot(px - ax, py - ay)
    u = max(0.0, min(1.0, ((px - ax) * ex + (py - ay) * ey) / L2))
    return math.hypot(px - (ax + u * ex), py - (ay + u * ey))


def _point_perimeter_distance(px, py, perimeter):
    if perimeter[0] != perimeter[-1]:
        perimeter = perimeter + [perimeter[0]]
    return min(
        _point_segment_distance(px, py, perimeter[i], perimeter[i + 1])
        for i in range(len(perimeter) - 1)
    )


def _ray_edge_intersection_t(origin, angle_rad, p0, p1, eps=1e-9):
    """Distance t>=0 along ray from origin at angle_rad to segment p0→p1, or None."""
    ox, oy = origin
    dx, dy = math.cos(angle_rad), math.sin(angle_rad)
    ex, ey = p1[0] - p0[0], p1[1] - p0[1]
    det = dx * ey - dy * ex
    if abs(det) < eps:
        return None
    rx, ry = p0[0] - ox, p0[1] - oy
    t = (rx * ey - ry * ex) / det
    u = (rx * dy - ry * dx) / det
    if t < -eps or u < -eps or u > 1 + eps:
        return None
    return max(0.0, t)


def _ray_perimeter_exit_distance(origin, angle_deg, perimeter, exclude_edges=None):
    """Farthest intersection of a polar ray with the part perimeter (inches)."""
    if perimeter[0] != perimeter[-1]:
        perimeter = perimeter + [perimeter[0]]
    exclude_edges = exclude_edges or []
    angle_rad = math.radians(angle_deg)
    hits = []
    for i in range(len(perimeter) - 1):
        p0, p1 = perimeter[i], perimeter[i + 1]
        if any(_same_segment(p0, p1, e0, e1) for e0, e1 in exclude_edges):
            continue
        t = _ray_edge_intersection_t(origin, angle_rad, p0, p1)
        if t is not None and t > 1e-6:
            hits.append(t)
    if not hits:
        return None
    return max(hits)


def flagnote_csys_children(orientation, shell_size, entry_size):
    """Polar flagnotes about the silhouette centroid.

    Leaders at each ray's perimeter hit. Connector mating face and cable-entry
    face are never used; for 45°/90°, inside-of-bend edges are also excluded.
    Flagnotes share one circle: max(hit) + FLAGNOTE_OFFSET_IN.
    flagnote-1 is nearest the preferred start angle (top for straight; exterior
    bisector for angled), then interleaved outward. Rays/flagnotes too close to
    the part are dropped.

    Stored as absolute x/y (harnice treats x/y vs angle/distance as exclusive).
    """
    perimeter = part_perimeter_inches(orientation, shell_size, entry_size)
    cx, cy = _polygon_centroid(perimeter)
    origin = (cx, cy)
    bisector = exterior_bisector_deg(orientation)

    mating = connector_mating_face_inches(orientation, shell_size, entry_size)
    cable = cable_entry_face_inches(orientation, shell_size, entry_size)
    exclude = [mating, cable] + inside_bend_edges_inches(
        orientation, shell_size, entry_size
    )

    leaders = []
    for angle in flagnote_angles_deg(orientation):
        r_leader = _ray_perimeter_exit_distance(
            origin, angle, perimeter, exclude_edges=exclude
        )
        if r_leader is None or r_leader < MIN_LEADER_RADIUS_IN:
            continue
        leaders.append((angle, r_leader))

    if not leaders:
        return {
            "leader_center": {
                "x": round(cx, 4),
                "y": round(cy, 4),
                "rotation": 0,
            }
        }

    r_flag = max(r for _, r in leaders) + FLAGNOTE_OFFSET_IN

    kept = []
    for angle, r_leader in leaders:
        rad = math.radians(angle)
        fx = cx + r_flag * math.cos(rad)
        fy = cy + r_flag * math.sin(rad)
        if _point_perimeter_distance(fx, fy, perimeter) < MIN_FLAGNOTE_CLEARANCE_IN:
            continue
        kept.append((angle, r_leader))

    # Number after filtering so flagnote-1 is truly nearest the start angle.
    by_angle = {angle: r for angle, r in kept}
    ordered_angles = _order_angles_from_bisector(list(by_angle), bisector)
    kept = [(angle, by_angle[angle]) for angle in ordered_angles]

    children = {
        "leader_center": {
            "x": round(cx, 4),
            "y": round(cy, 4),
            "rotation": 0,
        }
    }
    for i, (angle, r_leader) in enumerate(kept, start=1):
        rad = math.radians(angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        children[f"flagnote-{i}-leader_dest"] = {
            "x": round(cx + r_leader * cos_a, 4),
            "y": round(cy + r_leader * sin_a, 4),
            "rotation": 0,
        }
        children[f"flagnote-{i}"] = {
            "x": round(cx + r_flag * cos_a, 4),
            "y": round(cy + r_flag * sin_a, 4),
            "rotation": 0,
        }
    return children

def circular_backshell_assembly_wrench_part_number(shell_size, finish):
    """Glenair 600-series circular backshell assembly wrench for this shell/finish."""
    if finish == "F":
        # Stainless steel — standard coupling wrench 600-102
        dash = WRENCH_DASH_STANDARD[shell_size]
        return f"Glenair 600-102-{dash}"
    # Aluminum self-locking (/88–90) — anti-decoupling wrench 600-079
    dash = WRENCH_DASH_ANTI_DECOUPLING[shell_size]
    return f"Glenair 600-079-{dash}"



# Mass: Glenair does not publish a full AS85049/88–90 weight table.
# Scaled from listed M85049/88-25W03 at 1.552054 oz using C^2 * body length
# (F=/88, G=/89, H=/90) from the Glenair AS85049/88–90 dimension table used
# by SHELL_DATA above.
# https://www.glenair.com/mil-spec/as85049-qualified-backshells-and-connector-accessories/pdf/as85049-88-and-as85049-89-and-as85049-90.pdf
# Stainless finish F is scaled by density ratio 8.0/2.70. Entry 02 is +4%.
MASS_SOURCE = (
    "Estimated. Glenair does not publish a full AS85049/88–90 weight table. "
    "Scaled from listed M85049/88-25W03 at 1.552 oz using C^2 * body length "
    "(F straight / G 45deg / H 90deg) from "
    "https://www.glenair.com/mil-spec/as85049-qualified-backshells-and-connector-accessories/pdf/as85049-88-and-as85049-89-and-as85049-90.pdf "
    "Stainless finish F is scaled by density ratio 8.0/2.70."
)
_MASS_K_OZ = 1.552054 / (1.890 ** 2 * 1.200)


def part_mass_lbs(basic, shell_size, finish, entry_size):
    data = SHELL_DATA[int(shell_size)]
    length = {"88": data["f_in"], "89": data["g_in"], "90": data["h_in"]}[str(basic)]
    oz = _MASS_K_OZ * data["c_in"] ** 2 * length
    if str(entry_size) == "02":
        oz *= 1.04
    if finish == "F":
        oz *= 8.0 / 2.70
    return oz / 16.0


def compile_part_attributes(part_configuration):
    shell_size = part_configuration["shell_size"]
    entry_size = part_configuration["entry_size"]
    orientation = ORIENTATIONS[part_configuration["basic"]]
    finish = part_configuration["finish"]

    csys = {
        # Origin = right end of cable-side knurl; knurl/cable −X; body +X
        "connector": connector_csys(orientation, shell_size),
        "bundle_mate_3d": bundle_mate_csys_3d(orientation, shell_size, entry_size),
    }
    csys.update(flagnote_csys_children(orientation, shell_size, entry_size))

    torque = TORQUE_IN_LBS[shell_size]
    wrench = circular_backshell_assembly_wrench_part_number(shell_size, finish)

    attributes = {
        "mass": f"{part_mass_lbs(part_configuration['basic'], shell_size, finish, entry_size):.4f}lbs",
        "mass_source": MASS_SOURCE,
        "tools": [
            "Band-it clamp tool",
            "Torque wrench",
            f"{wrench} circular backshell assembly wrench",
            "Torque-stripe marker",
        ],
        "build_notes": [
            f"Torque to {torque} in-lbs",
        ],
        "csys_children": csys,
    }
    return attributes


def make_part_number(basic, detent, shell_size, finish, entry_size):
    # Matches harness example style: M85049-90_9Z03 / M85049-88_N17P02
    detent_code = detent  # "" or "N"
    return f"M85049-{basic}_{detent_code}{shell_size}{finish}{entry_size}"


def iter_part_configurations():
    for basic in ORIENTATIONS:
        for detent in ["", "N"]:
            for shell_size in SHELL_DATA:
                for finish in FINISHES:
                    for entry_size in valid_entries(shell_size):
                        yield {
                            "basic": basic,
                            "detent": detent,
                            "shell_size": shell_size,
                            "finish": finish,
                            "entry_size": entry_size,
                        }


def _progress_bar(done, total, width=25):
    """Return a text progress bar like: [ x x x . . . ] (35%)."""
    if total <= 0:
        filled = width
        pct = 100
    else:
        filled = min(width, max(0, round(width * done / total)))
        pct = round(100.0 * done / total)
    cells = ["x"] * filled + ["."] * (width - filled)
    return "[ " + " ".join(cells) + f" ] ({pct}%)"


def cache_run_constant_lookups():
    """Resolve the per-part lookups that cannot change during a run, once.

    `rev_history.part_family_append` calls `get_git_hash_of_harnice_src` (which
    shells out to `git rev-parse`) and re-reads `drawnby.json` for every part.
    Neither value can change while the run is in flight.
    """
    git_hash = fileio.get_git_hash_of_harnice_src()
    drawnby = fileio.drawnby()
    fileio.get_git_hash_of_harnice_src = lambda: git_hash
    fileio.drawnby = lambda: drawnby


def build_part(part_number, rev_dir):
    """Run the harnice part build in this process.

    Equivalent to `harnice -b` in **rev_dir**, minus the checks the CLI performs
    that this generator has already satisfied: it wrote the revision history
    itself, so it does not need `verify_revision_structure` to discover the part
    number, re-derive the library identity, or refresh datemodified. Skipping
    the CLI avoids paying interpreter startup and a harnice import per part.
    """
    cwd = os.getcwd()
    os.chdir(rev_dir)
    try:
        state.set_pn(part_number)
        state.set_rev(REVISION)
        state.set_file_structure(part.file_structure())
        part.generate_structure()
        part.build()
    finally:
        os.chdir(cwd)


def main(step_only=False, use_cli=False):
    state.set_rev(REVISION)
    state.set_project_type("part")

    configs = list(iter_part_configurations())
    total = len(configs)

    if not step_only:
        cache_run_constant_lookups()

    for i, part_configuration in enumerate(configs, start=1):
        part_number = make_part_number(
            part_configuration["basic"],
            part_configuration["detent"],
            part_configuration["shell_size"],
            part_configuration["finish"],
            part_configuration["entry_size"],
        )
        print("Preparing part number: ", part_number)

        family_dir = os.path.dirname(os.path.abspath(__file__))
        part_dir = os.path.join(family_dir, part_number)
        os.makedirs(part_dir, exist_ok=True)
        orientation = ORIENTATIONS[part_configuration["basic"]]
        rev_dir = os.path.join(part_dir, f"{part_number}-rev{REVISION}")

        if step_only:
            os.makedirs(rev_dir, exist_ok=True)
            write_part_step(
                rev_dir,
                part_number,
                orientation,
                part_configuration["shell_size"],
                part_configuration["entry_size"],
            )
            print(_progress_bar(i, total))
            continue

        revision_history_content_dict = {
            "project_type": state.project_type,
            "mfg": "mil spec",
            "pn": part_number,
            "rev": REVISION,
            "desc": "",
            "status": "",
            "datestarted": DATE_STARTED,
            "library_repo": "https://github.com/harnice/harnice-aerospace-library",
            "library_subpath": "M85049",
        }
        revision_history_csv_path = os.path.join(
            part_dir, f"{part_number}-revision_history.tsv"
        )
        rev_history.part_family_append(
            revision_history_content_dict, revision_history_csv_path
        )

        if os.path.exists(rev_dir):
            for item in os.listdir(rev_dir):
                item_path = os.path.join(rev_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
        else:
            os.makedirs(rev_dir)

        json_path = os.path.join(
            rev_dir, f"{part_number}-rev{REVISION}-attributes.json"
        )
        attributes = compile_part_attributes(part_configuration)
        with open(json_path, "w") as f:
            json.dump(attributes, f, indent=2)

        svg_content = backshell_svg(
            part_number,
            orientation,
            part_configuration["shell_size"],
            part_configuration["entry_size"],
            part_configuration["finish"],
        )
        svg_path = os.path.join(rev_dir, f"{part_number}-rev{REVISION}-drawing.svg")
        with open(svg_path, "w") as f:
            f.write(svg_content)

        write_part_step(
            rev_dir,
            part_number,
            orientation,
            part_configuration["shell_size"],
            part_configuration["entry_size"],
        )

        # d38999_generator used `harnice -r`; current CLI builds with -b
        if use_cli:
            subprocess.run(["harnice", "-b"], cwd=rev_dir, check=True)
        else:
            build_part(part_number, rev_dir)
        if delete_pngs:
            for item in os.listdir(rev_dir):
                if item.endswith(".png"):
                    os.remove(os.path.join(rev_dir, item))

        print(_progress_bar(i, total))

    print("Finished rendering all parts in family.")


if __name__ == "__main__":
    main(
        step_only="--step-only" in sys.argv,
        use_cli="--cli" in sys.argv,
    )
