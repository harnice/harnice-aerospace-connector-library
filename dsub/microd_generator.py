"""
microd_dimensions.py
=====================

Programmatic access to Micro-D (MIL-DTL-83513) connector shell dimensions,
for the two termination families the user asked about:
    MIL-DTL-83513/01, /02  - solder cup, metal shell
    MIL-DTL-83513/03, /04  - pigtail (pre-wired), metal shell

Panel-cutout / PCB-mount dimensions are intentionally NOT included here --
this module is scoped to the connector body itself.

PRIMARY SOURCE
--------------
Amphenol India, "Micro-D Series Connectors" catalog, Rev 04-22, page 10,
table "Solder & Wire Type":
https://amphenol-in.com/wp-content/uploads/2024/12/Micro-D-Connector-and-Backshells-Rev-04-22.pdf
The page carries both sub-headings "Wire Termination: (As per MIL-STD-
83513/1&/2)" and "Solder Termination: (As per MIL-STD-83513/3&/4)" [sic --
the source itself swaps "MIL-STD" for "MIL-DTL", a typo in the catalog,
not introduced here], confirming this single table covers both the
solder-cup (/01,/02) and pigtail (/03,/04) families in one place: they
share the same metal shell, differing only in how the wire is terminated
at the rear, so the shell's outer geometry is common to both specs.
Catalog page 3 independently confirms the same pairing: "1) MDC-AL Series
Solder Cup, Metal Shell Type: (Similar to MIL-DTL-83513/01,02)" and
"2) MDC-AL Series Pigtail Connector, Metal Shell Type: (Similar to
MIL-DTL-83513/03,04)".

The catalog's "/1&/2 = wire, /3&/4 = solder" labels are swapped relative
to the official slash sheets (MIL-DTL-83513/01 and /02 are solder cup;
/03 and /04 are pigtail). Part numbers in this generator follow the
official specification, not the catalog's swapped labels.

CORRECTION FROM AN EARLIER VERSION OF THIS MODULE
-----------------------------------------------------
An earlier pass at this same table silently dropped an entire dimension
column. The table's raw OCR text lists nine size-scaling values (10.16mm
for the 9-position shell, up to 36.63mm for the 100-position shell)
between the D and G columns below; that block was skipped over the first
time, which also caused the G column to be mis-assigned to where F should
have been. Re-reading the label sequence in the source text -- values
always appear before their label, and a "PLUG / RCPT" marker always
applies to the two blocks immediately preceding it -- gives a consistent
7-column read (A, B, C-split, D, E, F, G-split) instead of the previous
6-column read that quietly lost data. See LETTER MEANINGS below for what
each column is now understood to represent.

CROSS-VALIDATION AGAINST MIL-DTL-83513/1H
------------------------------------------
MIL-DTL-83513/1H w/Amendment 1 (14 December 2011), Figure 1 table, was
read after the Amphenol dataset was transcribed. Official plug letters
do not use the same A-G names as the catalog. Numeric matches:

    Amphenol A (overall length)     ~= official A  (e.g. shell 9:
                                       19.94 mm catalog vs 19.68 mm spec)
    Amphenol B (short-axis width)    = official D  (14.35 mm / .565 in
                                       at 9 positions; 45.72 mm / 1.800 in
                                       at 100 -- exact)
    Amphenol C plug                  = official B  (8.48 mm / .3338 in
                                       at 9 positions -- exact)

This supports using Amphenol B as side-view height and Amphenol C as
solder-cup depth. Official /01 has no 69-position insert; QPL insert
letters are A-H only (9, 15, 21, 25, 31, 37, 51, 100). Shell 69 remains
in the lookup table as catalog-only and is not emitted as an M83513 PIN.

WHAT WAS NOT CROSS-VALIDATED (read this before trusting a number)
-------------------------------------------------------------------
This is still primarily a single-source catalog dataset. The D-sub module
had three independent manufacturer catalogs cross-checked against each
other; that was not repeated here. Column meanings below are inferred
from internal structure (label order, numeric consistency across shell
sizes) within the Amphenol document, then spot-checked against
MIL-DTL-83513/1H as noted above. Treat F and G as more provisional
than A/B/C.

LETTER MEANINGS
----------------
    A - overall shell length (MAX), along the pin row
    B - shell width (short axis); tolerance given as +0.005in/+0.13mm
        rather than a MAX callout like the other columns.
        Confirmed against official D on MIL-DTL-83513/1H.
    C - a depth/length dimension, split Plug vs Receptacle (Receptacle
        consistently ~1.5-2.5mm larger than Plug at every shell size --
        plausible if this is shell depth on the mating/shroud side, where
        a receptacle needs a bit more shell to house the socket contacts
        that receive the mating pin). Plug C matches official B on
        MIL-DTL-83513/1H.
    D - a small dimension, constant within groups of shell sizes (sizes
        9-37 share one value, 51/69 share a second, 100 has its own) --
        not split by gender
    E - another small dimension with the same size-grouping pattern as D,
        also not gender-split
    F - a depth/length dimension, NOT gender-split, whose values sit
        within ~0.05mm of the Receptacle-side C value at every shell size
        (e.g. shell 9: F=10.16mm vs C-Receptacle=10.21mm; shell 100:
        F=36.63mm vs C-Receptacle=38.10mm at the low end of the pattern).
        Given the table's dual /01,02 vs /03,04 framing, the leading
        candidate interpretation is that C is the equivalent dimension
        for the solder-cup family and F for the pigtail family (same
        shell, marginally different rear geometry) -- but this is a
        pattern-matching inference, not a source-confirmed label, and is
        flagged as such rather than asserted.
    G - a small dimension, gender-split (Plug vs Receptacle), with the
        same size-grouping pattern as D and E. Meaning not confirmed;
        candidate guesses (mounting-hole edge distance, insert step)
        were considered but none confirmed, so it's presented as raw
        data without a physical-meaning claim.

MATERIAL / COLOR
------------------
Insulator: "P - LCP Plastic" (liquid crystal polymer) per the catalog's
ordering-information section -- a MATERIAL code, not a color code. No
insulator color is stated anywhere in this document; do not assume black
(unlike D-sub, where black was explicitly published) without checking a
source that states it.

LIMITATIONS
------------
  - Single-source catalog dataset, spot-checked against MIL-DTL-83513/1H
    on A/B/C only.
  - Physical meaning of F and G are inferred, not confirmed -- see above.
  - Two values had obvious OCR digit-drop errors, corrected against the
    mm figure printed alongside them or the shell-to-shell step pattern
    (both flagged per-row in `note`): shell 25's A, and shell 31/shell
    100's B.
  - This covers the metal-shell MDC-AL family (/01-/04 equivalent) only.
    Micro-D also exists in stainless steel (dimensionally identical per
    the catalog) and PCB-mount variants (/10 through /33) -- not included
    here since the user asked specifically about /01-/04.
  - Shell 69 is catalog-only; MIL-DTL-83513/01-/04 insert letters are
    A-H and do not include 69.

USAGE
-----
    from microd_generator import get_dimension, list_shell_sizes

    get_dimension(25, "A")                         # -> 30.10 (mm)
    get_dimension(25, "C", gender="Receptacle")     # -> 20.37 (mm)
    get_dimension(25, "F")                          # -> 20.32 (mm)
"""

import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional, Literal

from harnice import state
from harnice.lists import rev_history


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

Letter = Literal["A", "B", "C", "D", "E", "F", "G"]

GENDER_SPLIT_DIMS = {"C", "G"}
SINGLE_VALUE_DIMS = {"A", "B", "D", "E", "F"}


@dataclass(frozen=True)
class MicroDShellRow:
    shell_size: int  # position/pin count: 9,15,21,25,31,37,51,69,100
    A_mm: float
    B_mm: float
    C_plug_mm: float
    C_rcpt_mm: float
    D_mm: float
    E_mm: float
    F_mm: float
    G_plug_mm: float
    G_rcpt_mm: float
    note: str = ""


_ROWS = [
    MicroDShellRow(9, 19.94, 14.35, 8.48, 10.21, 6.86, 7.82, 10.16, 4.70, 6.43),
    MicroDShellRow(15, 23.75, 18.16, 12.29, 13.97, 6.86, 7.82, 13.97, 4.70, 6.43),
    MicroDShellRow(21, 27.58, 21.97, 16.10, 17.83, 6.86, 7.82, 17.78, 4.70, 6.43),
    MicroDShellRow(
        25,
        30.10,
        24.51,
        18.64,
        20.37,
        6.86,
        7.82,
        20.32,
        4.70,
        6.43,
        note="A corrected from OCR '1.85in' to 30.10mm (=1.185in), "
        "matching the mm figure printed alongside it and the "
        "step pattern between shell 21 (27.58mm) and shell 31 "
        "(33.91mm).",
    ),
    MicroDShellRow(
        31,
        33.91,
        28.32,
        22.45,
        24.18,
        6.86,
        7.82,
        24.13,
        4.70,
        6.43,
        note="B corrected from OCR '26.32mm' to 28.32mm, "
        "recomputed from the printed inch value 1.115in "
        "(1.115 x 25.4 = 28.32mm), since 26.32mm breaks the "
        "step pattern between shells 25 (24.51mm) and 37 "
        "(32.13mm).",
    ),
    MicroDShellRow(37, 37.72, 32.13, 26.26, 27.99, 6.86, 7.82, 27.94, 4.70, 6.43),
    MicroDShellRow(51, 36.45, 30.86, 24.99, 26.72, 7.87, 8.92, 26.67, 5.82, 7.52),
    MicroDShellRow(69, 44.07, 38.48, 32.74, 34.47, 7.87, 8.92, 34.29, 5.82, 7.52),
    MicroDShellRow(
        100,
        55.12,
        45.72,
        35.13,
        38.10,
        9.14,
        10.10,
        36.63,
        6.88,
        10.01,
        note="B corrected from OCR '15.72mm' to 45.72mm "
        "(=1.800in x 25.4) -- an obvious dropped leading "
        "digit; 15.72mm would make the largest shell's "
        "width smaller than every other shell size's, "
        "which isn't physically plausible.",
    ),
]


def _row(shell_size: int) -> MicroDShellRow:
    row = next((r for r in _ROWS if r.shell_size == shell_size), None)
    if row is None:
        raise ValueError(
            f"No data for shell_size={shell_size!r}. "
            f"Available sizes: {[r.shell_size for r in _ROWS]}"
        )
    return row


def get_dimension(
    shell_size: int, dim: Letter, gender: Optional[str] = None
) -> float:
    """
    Return a Micro-D shell dimension in mm.

    shell_size : position/pin count (9, 15, 21, 25, 31, 37, 51, 69, or 100)
    dim        : "A".."G" -- see module docstring for what each represents
                 and how confidently that's known
    gender     : required for dim in {"C", "G"} ("Plug" or "Receptacle");
                 omit (or pass None) for dim in {"A","B","D","E","F"}
    """
    row = _row(shell_size)

    if dim in GENDER_SPLIT_DIMS:
        if gender is None:
            raise ValueError(
                f"dim={dim!r} is gender-split; pass gender='Plug' or 'Receptacle'."
            )
        g = gender.strip().lower()
        if g == "plug":
            return getattr(row, f"{dim}_plug_mm")
        elif g in ("receptacle", "rcpt", "socket"):
            return getattr(row, f"{dim}_rcpt_mm")
        else:
            raise ValueError(
                f"Unknown gender {gender!r}. Use 'Plug' or 'Receptacle'."
            )
    elif dim in SINGLE_VALUE_DIMS:
        return getattr(row, f"{dim}_mm")
    else:
        raise ValueError(f"Unknown dimension {dim!r}. Valid options: A,B,C,D,E,F,G")


def get_note(shell_size: int) -> str:
    """Return the provenance/correction note for a shell size's row, if any."""
    return _row(shell_size).note


def list_shell_sizes() -> list:
    """Return every shell size (pin/position count) available."""
    return [r.shell_size for r in _ROWS]


# ---------------------------------------------------------------------------
# Part family generator (same pipeline as D38999 / dsub)
# ---------------------------------------------------------------------------
# Official PIN, solder cup:  M83513/{slash}-{insert}{finish}
#   e.g. M83513/01-AN
# Official PIN, pigtail:     M83513/{slash}-{insert}{wire}{finish}
#   e.g. M83513/03-A01N
# Library PN replaces the spec slash with underscore: M83513_01-AN
#
#   /01 = plug, pin contacts, solder cup, metal shell
#   /02 = receptacle, socket contacts, solder cup, metal shell
#   /03 = plug, pin contacts, pigtail, metal shell
#   /04 = receptacle, socket contacts, pigtail, metal shell
#   insert letters from MIL-DTL-83513/1H Figure 2 / PIN block:
#     A=9 B=15 C=21 D=25 E=31 F=37 G=51 H=100
#   finish letters from MIL-DTL-83513/1H PIN block (metal shell):
#     A = pure electrodeposited aluminum
#     C = cadmium
#     K = zinc nickel
#     N = electroless nickel (space applications only)
#     P = passivated stainless steel
#     T = nickel fluorocarbon polymer
#   pigtail wire codes from NASA NPSL MIL-PRF-83513 ordering table
#   (https://nepp.nasa.gov/npsl/connectors/m83513/83513pn1.htm)
# ---------------------------------------------------------------------------

REVISION = "1"
DATE_STARTED = "8/16/26"
delete_pngs = True

PX_PER_IN = 96.0
MM_PER_IN = 25.4
# Flange thickness is not a confirmed A-G letter. 1.00 mm is a drawing-only
# estimate so the side silhouette has a step.
FLANGE_THICKNESS_MM = 1.00

# Official QPL insert letters. 69 is catalog-only (no MIL-DTL-83513/01-04 letter).
INSERT_LETTERS = {
    9: "A",
    15: "B",
    21: "C",
    25: "D",
    31: "E",
    37: "F",
    51: "G",
    100: "H",
}

SLASH_SHEETS = {
    ("Solder Cup", "Plug"): "01",
    ("Solder Cup", "Receptacle"): "02",
    ("Pigtail", "Plug"): "03",
    ("Pigtail", "Receptacle"): "04",
}

# MIL-DTL-83513/1H metal-shell finish suffixes.
FINISHES = {
    "A": "pure electrodeposited aluminum",
    "C": "cadmium",
    "K": "zinc nickel",
    "N": "electroless nickel",
    "P": "passivated stainless steel",
    "T": "nickel fluorocarbon polymer",
}

# NASA NPSL MIL-PRF-83513 pigtail termination codes.
WIRE_TYPES = {
    "01": "M22759/11-26-9, 18 in, white",
    "02": "M22759/11-26-9, 36 in, white",
    "03": "M22759/11-26-X, 18 in, 10-color repeating",
    "04": "M22759/11-26-X, 36 in, 10-color repeating",
    "05": "A-A-59551 25 AWG solid, 0.5 in, gold plated",
    "06": "A-A-59551 25 AWG solid, 1.0 in, gold plated",
    "07": "A-A-59551 25 AWG solid, 0.5 in, tin plated",
    "08": "A-A-59551 25 AWG solid, 1.0 in, tin plated",
    "09": "M22759/33-26-9, 18 in, white",
    "10": "M22759/33-26-9, 36 in, white",
    "11": "M22759/33-26-X, 18 in, 10-color repeating",
    "12": "M22759/33-26-X, 36 in, 10-color repeating",
    "13": "M22759/11-26-9, 72 in, white",
    "14": "M22759/11-26-X, 72 in, 10-color repeating",
    "15": "M22759/33-26-9, 72 in, white",
    "16": "M22759/33-26-X, 72 in, 10-color repeating",
}

CONTACT_SIZE = {
    "size": "24",
    "awg_min": 26,
    "awg_max": 32,
    "current_rating": 3.0,
}

# Flagnotes sit on a circle centered at the cable-side origin, 15 deg
# apart, alternating up/down from due-right like D38999. Notes left of
# the mating face are omitted. Leader destinations are spaced evenly
# along the mating-face outline (shroud height).
FLAGNOTE_CENTER_X_IN = 0.0
FLAGNOTE_CENTER_Y_IN = 0.0
FLAGNOTE_RADIUS_IN = 3.0
FLAGNOTE_ANGLES_DEG = (
    0, 15, -15, 30, -30, 45, -45, 60, -60, 75, -75, 90, -90
)


def _flagnote_note_polar(theta_deg):
    """Angle/distance from the flagnote center, clamped to x >= 0."""
    rad = math.radians(theta_deg)
    nx = FLAGNOTE_CENTER_X_IN + FLAGNOTE_RADIUS_IN * math.cos(rad)
    ny = FLAGNOTE_CENTER_Y_IN + FLAGNOTE_RADIUS_IN * math.sin(rad)
    if nx < 0.0:
        nx = 0.0
        radial = math.sqrt(
            max(
                FLAGNOTE_RADIUS_IN ** 2
                - (nx - FLAGNOTE_CENTER_X_IN) ** 2,
                0.0,
            )
        )
        ny = math.copysign(radial, math.sin(rad) or theta_deg)
    return (
        math.degrees(math.atan2(ny - FLAGNOTE_CENTER_Y_IN, nx - FLAGNOTE_CENTER_X_IN)),
        math.hypot(nx - FLAGNOTE_CENTER_X_IN, ny - FLAGNOTE_CENTER_Y_IN),
    )


def _even_face_ys(half_h, count):
    """Center-out stations from -half_h to +half_h (0, +step, -step, ...)."""
    if count <= 1:
        return [0.0]
    step = (2.0 * half_h) / (count - 1)
    ys = [0.0]
    for j in range(1, (count + 1) // 2):
        ys.append(j * step)
        ys.append(-j * step)
    if len(ys) < count:
        ys.append((count // 2) * step)
    return ys


def flagnote_csys_children(mating_face_x_in, mating_face_half_height_mm):
    """Polar flagnotes from the origin; leaders spaced along the mating face.

    Harnice treats cartesian (x/y) and polar (angle/distance) as exclusive:
    if x/y are present, even as 0.0, polar is ignored. Emit polar only.
    """
    half_h_in = mating_face_half_height_mm / MM_PER_IN
    dx = mating_face_x_in - FLAGNOTE_CENTER_X_IN
    kept = []
    for theta in FLAGNOTE_ANGLES_DEG:
        note_angle, note_dist = _flagnote_note_polar(theta)
        note_x = (
            FLAGNOTE_CENTER_X_IN
            + note_dist * math.cos(math.radians(note_angle))
        )
        if note_x < mating_face_x_in:
            continue
        kept.append((note_angle, note_dist))
    children = {}
    for i, ((note_angle, note_dist), y_face) in enumerate(
        zip(kept, _even_face_ys(half_h_in, len(kept))), start=1
    ):
        theta_dest = math.degrees(
            math.atan2(y_face - FLAGNOTE_CENTER_Y_IN, dx)
        )
        dist_face = math.hypot(dx, y_face - FLAGNOTE_CENTER_Y_IN)
        children[f"flagnote-{i}-leader_dest"] = {
            "angle": theta_dest,
            "distance": dist_face,
            "rotation": 0,
        }
        children[f"flagnote-{i}"] = {
            "angle": note_angle,
            "distance": note_dist,
            "rotation": 0,
        }
    return children


def _px_mm(mm):
    return (mm / MM_PER_IN) * PX_PER_IN


def _poly(points, fill="#C0C0C0"):
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polygon points="{pts}" fill="{fill}" stroke="black" stroke-width="1"/>'


def insert_letter(shell_size):
    try:
        return INSERT_LETTERS[shell_size]
    except KeyError:
        raise ValueError(
            f"Shell size {shell_size} has no MIL-DTL-83513/01-/04 insert letter. "
            f"QPL inserts: {INSERT_LETTERS}"
        )


def slash_sheet(connector_type, gender):
    try:
        return SLASH_SHEETS[(connector_type, gender)]
    except KeyError:
        raise ValueError(
            f"No MIL-DTL-83513 slash sheet for "
            f"connector_type={connector_type!r}, gender={gender!r}."
        )


def official_pin(part_configuration):
    slash = slash_sheet(
        part_configuration["connector_type"], part_configuration["gender"]
    )
    insert = insert_letter(part_configuration["shell_size"])
    finish = part_configuration["finish"]
    if part_configuration["connector_type"] == "Pigtail":
        wire = part_configuration["wire_type"]
        return f"M83513/{slash}-{insert}{wire}{finish}"
    return f"M83513/{slash}-{insert}{finish}"


def make_part_number(part_configuration):
    return official_pin(part_configuration).replace("M83513/", "M83513_", 1)


def mating_shroud_mm(shell_size, gender):
    # G is gender-split like official shroud depth; it is constant for
    # sizes 9–37 and then drifts with pin count. Use the 9-position
    # value so large shells stay ~8–10mm deep.
    return get_dimension(9, "G", gender=gender)


def connector_depth_mm(shell_size, connector_type, gender):
    # Official /01 B is the mating-axis envelope and does not grow with
    # shell size. Catalog C matches it at 9 positions, then tracks the
    # pin row — use the size-9 value for every shell.
    if connector_type == "Pigtail":
        return get_dimension(9, "F")
    return get_dimension(9, "C", gender=gender)


def cable_side_mm(shell_size, connector_type, gender):
    rear = (
        connector_depth_mm(shell_size, connector_type, gender)
        - FLANGE_THICKNESS_MM
        - mating_shroud_mm(shell_size, gender)
    )
    return max(rear, 1.0)


def microd_connector_svg(part_number, part_configuration):
    """
    Side silhouette along the mating axis (origin at the cable side, +X
    toward the mating face; same convention as D38999).

    Stack-up: insulator (cable) | mounting flange | mating shroud.
    Height is Amphenol B / official D.
    """
    shell_size = part_configuration["shell_size"]
    gender = part_configuration["gender"]
    height = get_dimension(shell_size, "B")
    cable_px = _px_mm(
        cable_side_mm(shell_size, part_configuration["connector_type"], gender)
    )
    flange_px = _px_mm(FLANGE_THICKNESS_MM)
    shroud_px = _px_mm(mating_shroud_mm(shell_size, gender))
    flange_rear = cable_px
    flange_front = cable_px + flange_px
    mating_x = flange_front + shroud_px
    half_h = _px_mm(height) / 2.0
    body_half = half_h * 0.72

    outline = [
        (0.0, -body_half),
        (flange_rear, -body_half),
        (flange_rear, -half_h),
        (flange_front, -half_h),
        (flange_front, -body_half),
        (mating_x, -body_half),
        (mating_x, body_half),
        (flange_front, body_half),
        (flange_front, half_h),
        (flange_rear, half_h),
        (flange_rear, body_half),
        (0.0, body_half),
    ]

    insulator = (
        f'<rect x="0.00" y="{-body_half:.2f}" '
        f'width="{cable_px:.2f}" height="{2 * body_half:.2f}" '
        f'fill="#2C2C2C" stroke="black" stroke-width="1"/>'
    )

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="400" height="400">
<g id="{part_number}-drawing-contents-start">
{_poly(outline)}
{insulator}
</g>
<g id="{part_number}-drawing-contents-end">
</g>
</svg>'''


DSUB_SIDE_TAPER_DEG = 12.0
_EPS = 1e-9


def _arc_yz(cx, cz, radius, a0, a1, n):
    pts = []
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / n
        pts.append((cx + radius * math.cos(t), cz + radius * math.sin(t)))
    return pts


def _fillet_vertex_yz(p0, p1, p2, radius, n):
    """Arc replacing corner p1 of a CCW YZ polygon."""
    y0, z0 = p0
    y1, z1 = p1
    y2, z2 = p2
    v1 = (y0 - y1, z0 - z1)
    v2 = (y2 - y1, z2 - z1)
    l1 = math.hypot(*v1)
    l2 = math.hypot(*v2)
    if l1 < _EPS or l2 < _EPS or radius < _EPS:
        return [p1]
    u1 = (v1[0] / l1, v1[1] / l1)
    u2 = (v2[0] / l2, v2[1] / l2)
    turn = math.atan2(u1[0] * u2[1] - u1[1] * u2[0], u1[0] * u2[0] + u1[1] * u2[1])
    half = abs(turn) / 2.0
    if half < 1e-6:
        return [p1]
    t = min(radius / math.tan(half), l1 * 0.45, l2 * 0.45)
    r = t * math.tan(half)
    t1 = (y1 + u1[0] * t, z1 + u1[1] * t)
    t2 = (y1 + u2[0] * t, z1 + u2[1] * t)
    bis = (u1[0] + u2[0], u1[1] + u2[1])
    bl = math.hypot(*bis)
    if bl < _EPS:
        return [t1, t2]
    dist = r / math.sin(half)
    cy = y1 + bis[0] / bl * dist
    cz = z1 + bis[1] / bl * dist
    a0 = math.atan2(t1[1] - cz, t1[0] - cy)
    a1 = math.atan2(t2[1] - cz, t2[0] - cy)
    sweep = a1 - a0
    while sweep <= 0.0:
        sweep += 2.0 * math.pi
    while sweep > 2.0 * math.pi:
        sweep -= 2.0 * math.pi
    return [
        (cy + r * math.cos(a0 + sweep * i / n), cz + r * math.sin(a0 + sweep * i / n))
        for i in range(n + 1)
    ]


def _rounded_rect_yz(width_mm, height_mm, radius_mm=None, n=6):
    hw, hh = width_mm / 2.0, height_mm / 2.0
    r = min(
        radius_mm if radius_mm is not None else min(hw, hh) * 0.18,
        hw * 0.45,
        hh * 0.45,
    )
    if r < 0.05:
        return [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    pts = []
    pts += _arc_yz(hw - r, -hh + r, r, -math.pi / 2, 0.0, n)
    pts += _arc_yz(hw - r, hh - r, r, 0.0, math.pi / 2, n)
    pts += _arc_yz(-hw + r, hh - r, r, math.pi / 2, math.pi, n)
    pts += _arc_yz(-hw + r, -hh + r, r, math.pi, 3.0 * math.pi / 2, n)
    return pts


def _d_shell_yz(wide_mm, height_mm, n=8):
    """D-sub mating outline: isosceles trapezoid (wide at −Z), rounded corners."""
    inset = height_mm * math.tan(math.radians(DSUB_SIDE_TAPER_DEG))
    narrow = max(wide_mm - 2.0 * inset, wide_mm * 0.55)
    hw, hn, hh = wide_mm / 2.0, narrow / 2.0, height_mm / 2.0
    r = min(height_mm * 0.15, hw * 0.25, hn * 0.25)
    verts = [(-hw, -hh), (hw, -hh), (hn, hh), (-hn, hh)]
    pts = []
    m = len(verts)
    for i in range(m):
        pts.extend(
            _fillet_vertex_yz(
                verts[(i - 1) % m], verts[i], verts[(i + 1) % m], r, n
            )
        )
    return pts


def envelope_prisms_mm(part_configuration):
    """Cable-side D-shell, A×B collar, mating-face D-shell (mm)."""
    shell_size = part_configuration["shell_size"]
    gender = part_configuration["gender"]
    connector_type = part_configuration["connector_type"]
    cable = cable_side_mm(shell_size, connector_type, gender)
    flange = FLANGE_THICKNESS_MM
    shroud = mating_shroud_mm(shell_size, gender)
    wide = get_dimension(shell_size, "A")
    height = get_dimension(shell_size, "B")
    shell = _d_shell_yz(wide, height * 0.72)
    plate = _rounded_rect_yz(wide, height)
    x1 = cable
    x2 = cable + flange
    x3 = x2 + shroud
    return [
        (0.0, x1, shell),
        (x1, x2, plate),
        (x2, x3, shell),
    ]


def write_part_step(rev_dir, part_number, part_configuration):
    path = os.path.join(rev_dir, f"{part_number}-rev{REVISION}-model.step")
    step_utils.write_prism_segments_step(
        path,
        part_number,
        envelope_prisms_mm(part_configuration),
        description="MIL-DTL-83513 low-fidelity envelope",
    )
    return path


def compile_part_attributes(part_configuration):
    shell_size = part_configuration["shell_size"]
    contacts = [
        {"name": str(i), "size": CONTACT_SIZE["size"]}
        for i in range(1, shell_size + 1)
    ]

    if part_configuration["connector_type"] == "Solder Cup":
        tools = ["Soldering iron"]
    else:
        tools = []

    return {
        "tools": tools,
        "build_notes": [],
        "csys_children": {
            **flagnote_csys_children(
                connector_depth_mm(
                    shell_size,
                    part_configuration["connector_type"],
                    part_configuration["gender"],
                )
                / MM_PER_IN,
                get_dimension(shell_size, "B") * 0.72 / 2.0,
            ),
        },
        "contacts": contacts,
    }


def iter_part_configurations():
    for shell_size in INSERT_LETTERS:
        for (connector_type, gender), _slash in SLASH_SHEETS.items():
            for finish in FINISHES:
                if connector_type == "Pigtail":
                    for wire_type in WIRE_TYPES:
                        yield {
                            "connector_type": connector_type,
                            "gender": gender,
                            "shell_size": shell_size,
                            "finish": finish,
                            "wire_type": wire_type,
                        }
                else:
                    yield {
                        "connector_type": connector_type,
                        "gender": gender,
                        "shell_size": shell_size,
                        "finish": finish,
                        "wire_type": None,
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


def make_part(part_configuration):
    """Write one Micro-D part folder, attributes, SVG, and run harnice -b."""
    part_number = make_part_number(part_configuration)
    print("Preparing part number: ", part_number)

    family_dir = os.path.dirname(os.path.abspath(__file__))
    part_dir = os.path.join(family_dir, part_number)
    os.makedirs(part_dir, exist_ok=True)

    revision_history_content_dict = {
        "product": state.product,
        "mfg": "mil spec",
        "pn": part_number,
        "rev": REVISION,
        "desc": "",
        "status": "",
        "datestarted": DATE_STARTED,
        "library_repo": "https://github.com/harnice/harnice-aerospace-connector-library",
        "library_subpath": "dsub",
    }
    revision_history_csv_path = os.path.join(
        part_dir, f"{part_number}-revision_history.tsv"
    )
    rev_history.part_family_append(
        revision_history_content_dict, revision_history_csv_path
    )

    rev_dir = os.path.join(part_dir, f"{part_number}-rev{REVISION}")
    if os.path.exists(rev_dir):
        for item in os.listdir(rev_dir):
            item_path = os.path.join(rev_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
    else:
        os.makedirs(rev_dir)

    json_path = os.path.join(rev_dir, f"{part_number}-rev{REVISION}-attributes.json")
    attributes = compile_part_attributes(part_configuration)
    with open(json_path, "w") as f:
        json.dump(attributes, f, indent=2)

    svg_content = microd_connector_svg(part_number, part_configuration)
    svg_path = os.path.join(rev_dir, f"{part_number}-rev{REVISION}-drawing.svg")
    with open(svg_path, "w") as f:
        f.write(svg_content)

    write_part_step(rev_dir, part_number, part_configuration)

    subprocess.run(["harnice", "-b"], cwd=rev_dir, check=True)
    if delete_pngs:
        for item in os.listdir(rev_dir):
            if item.endswith(".png"):
                os.remove(os.path.join(rev_dir, item))

    return part_number


def main(step_only=False):
    state.set_rev(REVISION)
    state.set_product("part")

    configs = list(iter_part_configurations())
    total = len(configs)
    for i, part_configuration in enumerate(configs, start=1):
        if step_only:
            part_number = make_part_number(part_configuration)
            print("Preparing part number: ", part_number)
            family_dir = os.path.dirname(os.path.abspath(__file__))
            rev_dir = os.path.join(
                family_dir, part_number, f"{part_number}-rev{REVISION}"
            )
            os.makedirs(rev_dir, exist_ok=True)
            json_path = os.path.join(
                rev_dir, f"{part_number}-rev{REVISION}-attributes.json"
            )
            with open(json_path, "w") as f:
                json.dump(compile_part_attributes(part_configuration), f, indent=2)
            svg_path = os.path.join(
                rev_dir, f"{part_number}-rev{REVISION}-drawing.svg"
            )
            with open(svg_path, "w") as f:
                f.write(microd_connector_svg(part_number, part_configuration))
            write_part_step(rev_dir, part_number, part_configuration)
            print(_progress_bar(i, total))
            continue
        make_part(part_configuration)
        print(_progress_bar(i, total))

    print("Finished rendering all parts in family.")


if __name__ == "__main__":
    main(step_only="--step-only" in sys.argv)
