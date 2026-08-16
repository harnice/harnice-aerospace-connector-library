"""
dsub_dimensions.py
===================

Programmatic access to D-subminiature (MIL-DTL-24308) connector shell
dimensions, sourced from a manufacturer's published mechanical drawings.

PRIMARY SOURCE
--------------
Amphenol Pcd, "D-Sub Connectors" catalog (MIL-DTL-24308), Dec. 2018.
Retrieved via Mouser: https://www.mouser.com/datasheet/2/18/1/DSUB_2018-1651582.pdf
Pages 16-21: dimension tables for
    p16 - Standard Density Crimp   - Receptacle
    p17 - High     Density Crimp   - Receptacle
    p18 - Standard Density Crimp   - Plug
    p19 - High     Density Crimp   - Plug
    p20 - Standard Density Solder Cup - Receptacle
    p21 - Standard Density Solder Cup - Plug
Each page gives an "A" through "L" lettered dimension table per shell size,
per the source's own note: "Dimensions A-L: Top # = min., Bottom # = max."

CROSS-VALIDATION (used to confirm which letter means what, since the PDF
was read via OCR rather than viewed as a rendered image):
  - ITT Cannon / DigiKey "D Subminiature Full Line Catalog"
    https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/1364/d-sub_full_line_catalog.pdf
    Gave an independent front-face A-E table that matched Amphenol's A-E
    columns almost exactly, and separately gave solder-cup "MAX" depth
    call-outs (10.72mm plug / 9.91mm receptacle) used to sanity-check the
    depth-axis dimensions.
  - Positronic Catalog C-001 (MD/ED/SD/HDC/RD/ODD series)
    https://www.connectpositronic.com/wp-content/uploads/2023/04/C001Rev13_DSub.pdf
    Independently confirmed the same A-E front-face envelope values, and
    gave the insulator material/color call-outs used for
    `insulator_color` below (glass-filled polyester, UL94V-0, black;
    green DAP specifically on the military Rhapso-D line).
  - RS PRO product listing (RS Online, part 5443749 and similar)
    Used once, early on, to confirm which catalog letter corresponds to
    physical "depth" (front-to-back, mating axis) vs "height" (front-face,
    vertical axis) -- the two are easy to confuse from a table alone.

WHAT EACH LETTER MEANS (established by cross-referencing three sources'
diagrams/tables against each other; nothing here is a guess made in
isolation -- see the notes above for how each was confirmed):
    A - overall shell length, incl. mounting ears (along the pin row)
    B - shell body width, excl. mounting ears (along the pin row)
    C - mounting hole spacing (screw-to-screw)
    D - shell body height, excl. mounting ears (short axis)
    E - overall height, incl. mounting ears (short axis)
    F - mating-face shroud depth (front-to-back, mating axis)
    G - a secondary short-axis dimension near the shroud opening
        (likely a step/relief -- not independently confirmed against a
        second source; treat with more caution than A-F)
    H - a dimension that scales with shell size roughly in proportion to
        B, not to A or F. Earlier drafts of this dataset assumed H was
        the rear (cable-side) insulator depth -- checking the ratio
        H/B (~1.05-1.18, roughly constant) vs H/A (0.63-0.83, not
        constant) across all five/six shell sizes showed this is WRONG:
        H tracks the B (width) axis, not any front-to-back depth axis.
        It is most likely a width-adjacent dimension for an optional
        hardware configuration (e.g. a float-mount bracket) rather than
        a depth. Included for completeness but NOT mapped to
        `cable_side_depth` below -- that field is left as None pending a
        proper visual read of the drawing (see LIMITATIONS).
    J - did not vary across shell sizes in any of the six source tables
        (only ever restated for shell 1); modeled as a true constant.
    K - a small mounting-hardware dimension for shells 1-4, jumping by
        roughly 10x for shells 5-6 (50/104-pin), consistent across every
        table that reports it -- accepted as read, not flagged.
    L - a small edge/chamfer-scale dimension. Never restated by the
        source past shell 3, so modeled as constant beyond that point
        (see JUDGMENT CALLS).
    MAX_total_depth - a separate "MAX" call-out in the drawing (not part
        of the A-L table), constant per gender: 9.91mm for solder-cup
        receptacles across all shell sizes; 11.23mm for solder-cup plugs
        on shells 1-4, but 9.91mm specifically for the 50-pin/3-row plug
        (see JUDGMENT CALLS for why the plug value is split by shell).

JUDGMENT CALLS (made where the OCR'd source text was ambiguous or
incomplete; the user accepted these as final rather than requiring a
by-hand visual re-check of the PDF -- see conversation history if you
need to revisit one):
  1. Standard-density crimp PLUG, shell 1, dimension D: source text gave
     "8.23-8.23" (no spread), almost certainly an OCR/transcription gap.
     Corrected to 8.23-8.48mm to match the high-density plug's shell-1 D,
     since shell 1's outer envelope should not depend on contact density.
  2. K vs L, shells 3-4: receptacle K (0.74-1.25mm) and plug K
     (1.27-1.78mm) genuinely differ in the source and were kept as-read
     (plausible: socket vs. pin shells can need different hole/tab
     geometry there). L was standardized to 0.74-1.25mm for both genders
     at shells 3-4, since two independent plug tables agreed on it and no
     receptacle table contradicted it.
  3. J: never restated past shell 1 in any of six tables -> modeled as a
     constant (10.46-10.97mm) for every shell size and gender.
  4. L, shells 5-6: never given anywhere in the source. Modeled as
     constant at the shell-3/4 value (0.74-1.25mm) on the reasoning that
     L behaves like a small fixed machining feature (e.g. an edge break),
     unlike K, which clearly scales with shell size in every table that
     reports it.
  5. F/G, standard-density RECEPTACLE, shell 5: missing from source for
     the receptacle specifically. Filled from the shell-5 PLUG values
     (F=11.07-11.33mm, G=14.99-15.75mm), which were internally consistent
     across two independent plug tables (crimp and solder-cup) -- best
     available proxy, not an independent receptacle measurement.
  6. Solder-cup MAX_total_depth conflict: the source text contained two
     different "MAX" call-outs near the plug drawing (11.23mm and
     9.91mm). Resolved by shell size rather than discarding one: 11.23mm
     for shells 1-4 (matches a "SEE NOTE 1" annotation in the source),
     9.91mm for shell 5 specifically (matches a distinct "50 PIN (3 ROWS)"
     annotation, and also matches the receptacle's flat 9.91mm -- physically
     plausible that plug and receptacle depth converge at the largest
     shell size).

LIMITATIONS -- READ BEFORE TRUSTING A NUMBER FOR MANUFACTURING
----------------------------------------------------------------
  - This entire dataset was built from OCR'd/extracted TEXT off a PDF,
    not from a visually-inspected rendering of the drawing. Column
    assignment (which letter = which physical dimension) was inferred by
    cross-referencing three catalogs and checking numeric ratios, not by
    looking at the actual diagram. It has held together consistently,
    but "consistent" is not the same guarantee as "confirmed by eye."
  - `cable_side_depth` and `flange_thickness`, both requested by the user
    as parameters of interest, are NOT reliably present in this dataset.
    `flange_thickness` has no clean candidate letter at all. See the "H"
    note above for why `cable_side_depth` specifically was left unmapped
    rather than populated with a wrong-but-plausible-looking number.
  - Tolerances are given as published min-max ranges in millimeters. No
    unit conversion errors are expected (source gives mm primary, inch
    secondary; mm values were used throughout) but this has not been
    independently re-derived from the inch column.
  - Values are for MIL-DTL-24308 shells specifically; commercial-grade
    D-sub shells from other manufacturers may differ slightly (the
    DigiKey/Positronic cross-checks suggest differences are usually
    <0.5mm, but that was only spot-checked on the A-E envelope, not on
    F/G/H/J/K/L).

USAGE
-----
    from dsub_dimensions import get_dimension, list_variants

    # Get dimension "A" for a standard-density crimp receptacle, 25-pin,
    # as a (min, max) tuple in mm:
    get_dimension("Crimp", "Receptacle", "Standard", pin_count=25, dim="A")
    # -> (52.65, 53.42)

    # Same, but get the midpoint as a single float:
    get_dimension("Crimp", "Receptacle", "Standard", pin_count=25,
                  dim="A", agg="mid")
    # -> 53.035

    # Look up by shell number instead of pin count:
    get_dimension("Solder Cup", "Plug", "Standard", shell_no=3, dim="MAX_total_depth")
    # -> (11.23, 11.23)
"""

import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import Optional, Union, Literal

from harnice import state
from harnice.lists import rev_history

Aggregation = Literal["range", "min", "max", "mid"]

DIMENSION_LETTERS = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "J",
    "K",
    "L",
    "MAX_total_depth",
]


@dataclass(frozen=True)
class ShellVariant:
    page: int
    connector_type: str  # "Crimp" or "Solder Cup"
    gender: str  # "Plug" or "Receptacle"
    density: str  # "Standard" or "High"
    shell_no: int
    pin_count: int
    dims: dict  # letter -> (min_mm, max_mm) or None
    resolution_note: str = ""


def _r(spec: Optional[str]):
    """Parse a 'min-max' string into a (min, max) float tuple, or None."""
    if not spec:
        return None
    lo, hi = spec.split("-")
    return (float(lo), float(hi))


# ---------------------------------------------------------------------------
# The dataset itself. One row per connector variant, transcribed from
# Amphenol Pcd catalog pages 16-21 (see module docstring for citations and
# the full list of judgment calls applied to fill gaps in the source text).
# ---------------------------------------------------------------------------
_ROWS = [
    # page, conn_type,     gender,       density,    shell, pins,
    #   A,               B,               C,               D,              E,
    #   F,               G,               H,                J,               K,               L,             MAX_depth, note
    (
        16,
        "Crimp",
        "Receptacle",
        "Standard",
        1,
        9,
        "30.43-31.19",
        "16.21-16.46",
        "24.87-25.12",
        "7.67-8.03",
        "12.17-12.93",
        "10.64-11.15",
        "6.05-6.30",
        "19.02-19.53",
        "10.46-10.97",
        "0.89-1.52",
        "0.51-1.02",
        None,
        "source",
    ),
    (
        16,
        "Crimp",
        "Receptacle",
        "Standard",
        2,
        15,
        "38.76-39.52",
        "24.54-24.79",
        "33.20-33.45",
        "7.67-8.03",
        "12.17-12.93",
        "10.64-11.15",
        "6.05-6.30",
        "27.25-27.76",
        "10.46-10.97",
        "0.89-1.52",
        "0.51-1.02",
        None,
        "D/E/F/G/J/K/L inherited from shell 1",
    ),
    (
        16,
        "Crimp",
        "Receptacle",
        "Standard",
        3,
        25,
        "52.65-53.42",
        "38.25-38.51",
        "46.91-47.17",
        "7.67-8.03",
        "12.17-12.93",
        "10.64-11.15",
        "6.05-6.30",
        "41.02-41.53",
        "10.46-10.97",
        "0.74-1.25",
        "0.74-1.25",
        None,
        "D/E/F/G/J from shell1; K,L per shell3-4 step (source)",
    ),
    (
        16,
        "Crimp",
        "Receptacle",
        "Standard",
        4,
        37,
        "68.94-69.70",
        "54.71-54.97",
        "63.37-63.63",
        "7.67-8.03",
        "12.17-12.93",
        "10.64-11.15",
        "6.05-6.30",
        "57.45-57.96",
        "10.46-10.97",
        "0.74-1.25",
        "0.74-1.25",
        None,
        "D/E/F/G/J from shell1; K,L per shell3-4 step (source)",
    ),
    (
        16,
        "Crimp",
        "Receptacle",
        "Standard",
        5,
        50,
        "66.55-67.31",
        "52.30-52.55",
        "60.99-61.24",
        "10.62-10.87",
        "14.99-15.75",
        "11.07-11.33",
        "14.99-15.75",
        "55.07-55.58",
        "10.46-10.97",
        "13.31-13.82",
        "0.74-1.25",
        None,
        "F,G proxied from plug shell5; J constant; L carried from shell3-4",
    ),
    (
        17,
        "Crimp",
        "Receptacle",
        "High",
        1,
        15,
        "30.43-31.19",
        "16.21-16.46",
        "24.87-25.12",
        "7.67-8.03",
        "12.17-12.93",
        "10.64-11.15",
        "6.05-6.30",
        "19.02-19.53",
        "10.46-10.97",
        "0.89-1.52",
        "0.51-1.02",
        None,
        "source",
    ),
    (
        17,
        "Crimp",
        "Receptacle",
        "High",
        2,
        26,
        "38.76-39.52",
        "24.54-24.79",
        "33.20-33.45",
        "7.67-8.03",
        "12.17-12.93",
        "10.64-11.15",
        "6.05-6.30",
        "27.25-27.76",
        "10.46-10.97",
        "0.89-1.52",
        "0.51-1.02",
        None,
        "inherited from shell1",
    ),
    (
        17,
        "Crimp",
        "Receptacle",
        "High",
        3,
        44,
        "52.65-53.42",
        "38.25-38.51",
        "46.91-47.17",
        "7.67-8.03",
        "12.17-12.93",
        "10.64-11.15",
        "6.05-6.30",
        "41.02-41.53",
        "10.46-10.97",
        "0.74-1.25",
        "0.74-1.25",
        None,
        "D/E/F/G/J from shell1; K,L per shell3-4 step",
    ),
    (
        17,
        "Crimp",
        "Receptacle",
        "High",
        4,
        62,
        "68.94-69.70",
        "54.71-54.97",
        "63.37-63.63",
        "7.67-8.03",
        "12.17-12.93",
        "10.64-11.15",
        "6.05-6.30",
        "57.45-57.96",
        "10.46-10.97",
        "0.74-1.25",
        "0.74-1.25",
        None,
        "D/E/F/G/J from shell1; K,L per shell3-4 step",
    ),
    (
        17,
        "Crimp",
        "Receptacle",
        "High",
        5,
        78,
        "66.55-67.31",
        "52.30-52.55",
        "60.99-61.24",
        "10.62-10.87",
        "14.99-15.75",
        "11.07-11.33",
        "14.99-15.75",
        "55.07-55.58",
        "10.46-10.97",
        "13.31-13.82",
        "0.74-1.25",
        None,
        "F,G proxied from plug shell5; J constant; L carried",
    ),
    (
        17,
        "Crimp",
        "Receptacle",
        "High",
        6,
        104,
        "68.94-69.70",
        "55.47-55.73",
        "63.37-63.63",
        "12.19-12.45",
        "16.59-17.35",
        "12.65-12.90",
        "16.59-17.35",
        "58.22-58.72",
        "10.46-10.97",
        "14.88-15.39",
        "0.74-1.25",
        None,
        "F,G proxied from plug shell6; J constant; L carried",
    ),
    (
        18,
        "Crimp",
        "Plug",
        "Standard",
        1,
        9,
        "30.43-31.19",
        "16.79-17.04",
        "24.87-25.12",
        "8.23-8.48",
        "12.17-12.93",
        "10.46-10.97",
        "5.82-6.12",
        "19.02-19.53",
        "10.46-10.97",
        "0.89-1.52",
        "0.51-1.02",
        None,
        "D corrected to match High-Density Plug shell1 (same outer shell)",
    ),
    (
        18,
        "Crimp",
        "Plug",
        "Standard",
        2,
        15,
        "38.76-39.52",
        "25.12-25.37",
        "33.20-33.45",
        "8.23-8.48",
        "12.17-12.93",
        "10.46-10.97",
        "5.82-6.12",
        "27.25-27.76",
        "10.46-10.97",
        "0.89-1.52",
        "0.51-1.02",
        None,
        "inherited from shell1",
    ),
    (
        18,
        "Crimp",
        "Plug",
        "Standard",
        3,
        25,
        "52.65-53.42",
        "38.84-39.09",
        "46.91-47.17",
        "8.23-8.48",
        "12.17-12.93",
        "10.57-11.07",
        "5.69-5.99",
        "41.02-41.53",
        "10.46-10.97",
        "1.27-1.78",
        "0.74-1.25",
        None,
        "D/E/J from shell1; F,G,H,K per source; L per shell3-4 step",
    ),
    (
        18,
        "Crimp",
        "Plug",
        "Standard",
        4,
        37,
        "68.94-69.70",
        "55.30-55.55",
        "63.37-63.63",
        "8.23-8.48",
        "12.17-12.93",
        "10.57-11.07",
        "5.69-5.99",
        "57.45-57.96",
        "10.46-10.97",
        "1.27-1.78",
        "0.74-1.25",
        None,
        "D/E/J from shell1; F,G,K carried from shell3; L per step",
    ),
    (
        18,
        "Crimp",
        "Plug",
        "Standard",
        5,
        50,
        "66.55-67.31",
        "52.68-52.93",
        "60.99-61.24",
        "8.23-8.48",
        "12.17-12.93",
        "11.07-11.33",
        "14.99-15.75",
        "55.07-55.58",
        "10.46-10.97",
        "13.31-13.82",
        "0.74-1.25",
        None,
        "D,J inherited/constant; L carried",
    ),
    (
        19,
        "Crimp",
        "Plug",
        "High",
        1,
        15,
        "30.43-31.19",
        "16.79-17.04",
        "24.87-25.12",
        "8.23-8.48",
        "12.17-12.93",
        "10.64-10.97",
        "5.82-6.12",
        "19.02-19.53",
        "10.46-10.97",
        "0.89-1.52",
        "0.51-1.02",
        None,
        "source",
    ),
    (
        19,
        "Crimp",
        "Plug",
        "High",
        2,
        26,
        "38.76-39.52",
        "25.12-25.37",
        "33.20-33.45",
        "8.23-8.48",
        "12.17-12.93",
        "10.64-10.97",
        "5.82-6.12",
        "27.25-27.76",
        "10.46-10.97",
        "0.89-1.52",
        "0.51-1.02",
        None,
        "inherited from shell1",
    ),
    (
        19,
        "Crimp",
        "Plug",
        "High",
        3,
        44,
        "52.65-53.42",
        "38.84-39.09",
        "46.91-47.17",
        "8.23-8.48",
        "12.17-12.93",
        "10.57-11.07",
        "5.69-5.99",
        "41.02-41.53",
        "10.46-10.97",
        "1.27-1.78",
        "0.74-1.25",
        None,
        "source (D/E/J inherited)",
    ),
    (
        19,
        "Crimp",
        "Plug",
        "High",
        4,
        62,
        "68.94-69.70",
        "55.30-55.55",
        "63.37-63.63",
        "8.23-8.48",
        "12.17-12.93",
        "10.57-11.07",
        "5.69-5.99",
        "57.45-57.96",
        "10.46-10.97",
        "1.27-1.78",
        "0.74-1.25",
        None,
        "D/E/J inherited; F,G,K carried from shell3",
    ),
    (
        19,
        "Crimp",
        "Plug",
        "High",
        5,
        78,
        "66.55-67.31",
        "52.68-52.93",
        "60.99-61.24",
        "8.23-8.48",
        "12.17-12.93",
        "11.07-11.33",
        "14.99-15.75",
        "55.07-55.58",
        "10.46-10.97",
        "13.31-13.82",
        "0.74-1.25",
        None,
        "source (D,J inherited/constant; L carried)",
    ),
    (
        19,
        "Crimp",
        "Plug",
        "High",
        6,
        104,
        "68.94-69.70",
        "56.06-56.31",
        "63.37-63.63",
        "8.23-8.48",
        "12.17-12.93",
        "12.65-12.90",
        "16.59-17.35",
        "58.22-58.72",
        "10.46-10.97",
        "14.88-15.39",
        "0.74-1.25",
        None,
        "source (D,J inherited/constant; L carried)",
    ),
    (
        20,
        "Solder Cup",
        "Receptacle",
        "Standard",
        1,
        9,
        "30.43-31.19",
        "16.21-16.46",
        "24.87-25.12",
        "7.67-8.03",
        "12.17-12.93",
        "10.64-11.15",
        "6.05-6.30",
        "19.02-19.53",
        "10.46-10.97",
        "0.89-1.52",
        "0.51-1.02",
        "9.91-9.91",
        "source",
    ),
    (
        20,
        "Solder Cup",
        "Receptacle",
        "Standard",
        2,
        15,
        "38.76-39.52",
        "24.54-24.79",
        "33.20-33.45",
        "7.67-8.03",
        "12.17-12.93",
        "10.64-11.15",
        "6.05-6.30",
        "27.25-27.76",
        "10.46-10.97",
        "0.89-1.52",
        "0.51-1.02",
        "9.91-9.91",
        "inherited from shell1",
    ),
    (
        20,
        "Solder Cup",
        "Receptacle",
        "Standard",
        3,
        25,
        "52.65-53.42",
        "38.25-38.51",
        "46.91-47.17",
        "7.67-8.03",
        "12.17-12.93",
        "10.64-11.15",
        "6.05-6.30",
        "41.02-41.53",
        "10.46-10.97",
        "0.74-1.25",
        "0.74-1.25",
        "9.91-9.91",
        "D/E/F/G/J from shell1; K,L per shell3-4 step",
    ),
    (
        20,
        "Solder Cup",
        "Receptacle",
        "Standard",
        4,
        37,
        "68.94-69.70",
        "54.71-54.97",
        "63.37-63.63",
        "7.67-8.03",
        "12.17-12.93",
        "10.64-11.15",
        "6.05-6.30",
        "57.45-57.96",
        "10.46-10.97",
        "0.74-1.25",
        "0.74-1.25",
        "9.91-9.91",
        "D/E/F/G/J from shell1; K,L per shell3-4 step",
    ),
    (
        20,
        "Solder Cup",
        "Receptacle",
        "Standard",
        5,
        50,
        "66.55-67.31",
        "52.30-52.55",
        "60.99-61.24",
        "10.62-10.87",
        "14.99-15.75",
        "11.07-11.33",
        "14.99-15.75",
        "55.07-55.58",
        "10.46-10.97",
        "13.31-13.82",
        "0.74-1.25",
        "9.91-9.91",
        "F,G proxied from plug shell5; J constant; L carried",
    ),
    (
        21,
        "Solder Cup",
        "Plug",
        "Standard",
        1,
        9,
        "30.43-31.19",
        "16.79-17.04",
        "24.87-25.12",
        "8.23-8.48",
        "12.17-12.93",
        "10.46-10.97",
        "5.82-6.05",
        "19.02-19.53",
        "10.46-10.97",
        "0.89-1.52",
        "0.51-1.02",
        "11.23-11.23",
        "source",
    ),
    (
        21,
        "Solder Cup",
        "Plug",
        "Standard",
        2,
        15,
        "38.76-39.52",
        "25.12-25.37",
        "33.20-33.45",
        "8.23-8.48",
        "12.17-12.93",
        "10.46-10.97",
        "5.82-6.05",
        "27.25-27.76",
        "10.46-10.97",
        "0.89-1.52",
        "0.51-1.02",
        "11.23-11.23",
        "inherited from shell1",
    ),
    (
        21,
        "Solder Cup",
        "Plug",
        "Standard",
        3,
        25,
        "52.65-53.42",
        "38.84-39.09",
        "46.91-47.17",
        "8.23-8.48",
        "12.17-12.93",
        "10.57-11.07",
        "5.69-5.99",
        "41.02-41.53",
        "10.46-10.97",
        "1.27-1.78",
        "0.74-1.24",
        "11.23-11.23",
        "D/E/J from shell1; F,G,H,K,L per source",
    ),
    (
        21,
        "Solder Cup",
        "Plug",
        "Standard",
        4,
        37,
        "68.94-69.70",
        "55.30-55.55",
        "63.37-63.63",
        "8.23-8.48",
        "12.17-12.93",
        "10.57-11.07",
        "5.69-5.99",
        "57.45-57.96",
        "10.46-10.97",
        "1.27-1.78",
        "0.74-1.24",
        "11.23-11.23",
        "D/E/J from shell1; F,G,K carried from shell3",
    ),
    (
        21,
        "Solder Cup",
        "Plug",
        "Standard",
        5,
        50,
        "66.55-67.31",
        "52.68-52.93",
        "60.99-61.24",
        "8.23-8.48",
        "12.17-12.93",
        "11.07-11.33",
        "14.99-15.75",
        "55.07-55.58",
        "10.46-10.97",
        "13.31-13.82",
        "0.74-1.24",
        "9.91-9.91",
        "D,J inherited/constant; L carried; MAX depth uses the 50-pin/3-row "
        "note (9.91) rather than the 09-37 pin note (11.23)",
    ),
]


def _build_variants():
    variants = []
    for row in _ROWS:
        (
            page,
            ctype,
            gender,
            density,
            shell_no,
            pins,
            A,
            B,
            C,
            D,
            E,
            F,
            G,
            H,
            J,
            K,
            L,
            maxd,
            note,
        ) = row
        dims = {
            "A": _r(A),
            "B": _r(B),
            "C": _r(C),
            "D": _r(D),
            "E": _r(E),
            "F": _r(F),
            "G": _r(G),
            "H": _r(H),
            "J": _r(J),
            "K": _r(K),
            "L": _r(L),
            "MAX_total_depth": _r(maxd),
        }
        variants.append(
            ShellVariant(page, ctype, gender, density, shell_no, pins, dims, note)
        )
    return variants


_VARIANTS = _build_variants()


def _normalize(s: str) -> str:
    return s.strip().lower().replace("_", " ")


def _matches(
    v: ShellVariant, connector_type, gender, density, shell_no, pin_count
) -> bool:
    if connector_type is not None and _normalize(v.connector_type) != _normalize(
        connector_type
    ):
        return False
    if gender is not None and _normalize(v.gender) != _normalize(gender):
        return False
    if density is not None and _normalize(v.density) != _normalize(density):
        return False
    if shell_no is not None and v.shell_no != shell_no:
        return False
    if pin_count is not None and v.pin_count != pin_count:
        return False
    return True


def find_variant(
    connector_type: str,
    gender: str,
    density: str,
    shell_no: Optional[int] = None,
    pin_count: Optional[int] = None,
) -> ShellVariant:
    """
    Locate a single ShellVariant. Identify the shell either by shell_no
    (1-6) or pin_count (e.g. 9, 15, 25, 37, 50, 78, 104) -- provide
    exactly one of the two.

    Raises ValueError if zero or more than one row matches (e.g. if
    density is ambiguous for a shell/pin_count that exists in both
    Standard and High density -- pin_count alone disambiguates this in
    practice since Standard and High density use different pin counts
    for the same shell_no).
    """
    if (shell_no is None) == (pin_count is None):
        raise ValueError("Provide exactly one of shell_no or pin_count.")

    matches = [
        v
        for v in _VARIANTS
        if _matches(v, connector_type, gender, density, shell_no, pin_count)
    ]
    if not matches:
        raise ValueError(
            f"No variant found for connector_type={connector_type!r}, "
            f"gender={gender!r}, density={density!r}, "
            f"shell_no={shell_no!r}, pin_count={pin_count!r}. "
            f"Call list_variants() to see everything available."
        )
    if len(matches) > 1:
        raise ValueError(
            f"{len(matches)} variants matched -- request is ambiguous. "
            f"Matches: {[(m.connector_type, m.gender, m.density, m.shell_no, m.pin_count) for m in matches]}"
        )
    return matches[0]


def get_dimension(
    connector_type: str,
    gender: str,
    density: str,
    dim: str,
    shell_no: Optional[int] = None,
    pin_count: Optional[int] = None,
    agg: Aggregation = "range",
) -> Union[tuple, float, None]:
    """
    Return a dimension for a specific D-sub shell variant.

    Parameters
    ----------
    connector_type : "Crimp" or "Solder Cup"
    gender          : "Plug" or "Receptacle"
    density         : "Standard" or "High"
    dim             : one of A,B,C,D,E,F,G,H,J,K,L,MAX_total_depth
                       (see module docstring for what each letter means,
                       and its LIMITATIONS section for which ones are
                       well-confirmed vs. best-effort)
    shell_no        : 1-6 (provide this OR pin_count, not both)
    pin_count       : 9,15,25,37,50,26,44,62,78,104 (provide this OR shell_no)
    agg             : "range" (default) -> (min_mm, max_mm) tuple
                       "min"  -> just the minimum
                       "max"  -> just the maximum
                       "mid"  -> midpoint float, (min+max)/2

    Returns None if the requested dimension isn't defined for that variant
    (e.g. MAX_total_depth is only defined for Solder Cup connectors).

    Example
    -------
    >>> get_dimension("Crimp", "Receptacle", "Standard", "A", pin_count=25)
    (52.65, 53.42)
    >>> get_dimension("Crimp", "Receptacle", "Standard", "A", pin_count=25, agg="mid")
    53.035
    """
    if dim not in DIMENSION_LETTERS:
        raise ValueError(
            f"Unknown dimension {dim!r}. Valid options: {DIMENSION_LETTERS}"
        )

    variant = find_variant(connector_type, gender, density, shell_no, pin_count)
    value = variant.dims.get(dim)
    if value is None:
        return None

    lo, hi = value
    if agg == "range":
        return (lo, hi)
    elif agg == "min":
        return lo
    elif agg == "max":
        return hi
    elif agg == "mid":
        return (lo + hi) / 2.0
    else:
        raise ValueError(f"Unknown agg {agg!r}. Use 'range', 'min', 'max', or 'mid'.")


def get_resolution_note(
    connector_type: str,
    gender: str,
    density: str,
    shell_no: Optional[int] = None,
    pin_count: Optional[int] = None,
) -> str:
    """
    Return the provenance note for a variant -- says whether each row's
    values came straight from the source or were filled in via one of the
    documented judgment calls (see module docstring).
    """
    return find_variant(
        connector_type, gender, density, shell_no, pin_count
    ).resolution_note


def list_variants():
    """Return every (connector_type, gender, density, shell_no, pin_count) combo available."""
    return [
        (v.connector_type, v.gender, v.density, v.shell_no, v.pin_count)
        for v in _VARIANTS
    ]


# ---------------------------------------------------------------------------
# Part family generator (same pipeline as D38999/d38999_generator.py)
# ---------------------------------------------------------------------------
# PIN: M24308-{slash}_{dash}{finish}  e.g. M24308-2_3F
#   slash 1 = solder-cup receptacle (socket), Class D/G
#   slash 2 = crimp receptacle (socket), Class D/G
#   slash 3 = solder-cup plug (pin), Class D/G
#   slash 4 = crimp plug (pin), Class D/G
#   dash   = shell_no for Standard density; shell_no+10 for High density
#            (Class G, no float mount — Amphenol Pcd 2018 QPL listing)
#   finish F = cadmium YP, Z = zinc YP, K = zinc-nickel black
# ---------------------------------------------------------------------------

REVISION = "1"
DATE_STARTED = "8/16/26"
delete_pngs = True

PX_PER_IN = 96.0
MM_PER_IN = 25.4
# Flange thickness is not a mapped A-L letter (see module LIMITATIONS).
# 1.25 mm is a drawing-only estimate so the side silhouette has a step.
FLANGE_THICKNESS_MM = 1.25

SLASH_SHEETS = {
    ("Solder Cup", "Receptacle"): "1",
    ("Crimp", "Receptacle"): "2",
    ("Solder Cup", "Plug"): "3",
    ("Crimp", "Plug"): "4",
}

FINISHES = ["F", "Z", "K"]

CONTACT_SIZES = {
    "20": {
        "awg_min": 20,
        "awg_max": 26,
        "current_rating": 7.5,
        "crimp_tool": "M22520/2-01",
        "extraction_tool": "M81969/14-01",
    },
    "22": {
        "awg_min": 22,
        "awg_max": 28,
        "current_rating": 5.0,
        "crimp_tool": "M22520/2-01",
        "extraction_tool": "M81969/39-01",
    },
}

STANDARD_CSYS_CHILDREN = {
    "flagnote-1": {"angle": 0, "distance": 3, "rotation": 0},
    "flagnote-1-leader_dest": {"angle": 0, "distance": 1, "rotation": 0},
    "flagnote-2": {"angle": 15, "distance": 3, "rotation": 0},
    "flagnote-2-leader_dest": {"angle": 15, "distance": 1.03, "rotation": 0},
    "flagnote-3": {"angle": -15, "distance": 3, "rotation": 0},
    "flagnote-3-leader_dest": {"angle": -15, "distance": 1.03, "rotation": 0},
    "flagnote-4": {"angle": 30, "distance": 3, "rotation": 0},
    "flagnote-4-leader_dest": {"angle": 30, "distance": 1, "rotation": 0},
    "flagnote-5": {"angle": -30, "distance": 3, "rotation": 0},
    "flagnote-5-leader_dest": {"angle": -30, "distance": 1, "rotation": 0},
    "flagnote-6": {"angle": 45, "distance": 3, "rotation": 0},
    "flagnote-6-leader_dest": {"angle": 45, "distance": 0.72, "rotation": 0},
    "flagnote-7": {"angle": -45, "distance": 3, "rotation": 0},
    "flagnote-7-leader_dest": {"angle": -45, "distance": 0.72, "rotation": 0},
    "flagnote-8": {"angle": 60, "distance": 3, "rotation": 0},
    "flagnote-8-leader_dest": {"angle": 60, "distance": 0.58, "rotation": 0},
    "flagnote-9": {"angle": -60, "distance": 3, "rotation": 0},
    "flagnote-9-leader_dest": {"angle": -60, "distance": 0.58, "rotation": 0},
    "flagnote-10": {"angle": -75, "distance": 3, "rotation": 0},
    "flagnote-10-leader_dest": {"angle": -75, "distance": 0.52, "rotation": 0},
    "flagnote-11": {"angle": 75, "distance": 3, "rotation": 0},
    "flagnote-11-leader_dest": {"angle": 75, "distance": 0.52, "rotation": 0},
    "flagnote-12": {"angle": -90, "distance": 3, "rotation": 0},
    "flagnote-12-leader_dest": {"angle": -90, "distance": 0.52, "rotation": 0},
    "flagnote-13": {"angle": 90, "distance": 3, "rotation": 0},
    "flagnote-13-leader_dest": {"angle": 90, "distance": 0.5, "rotation": 0},
}


def _mid(rng):
    if rng is None:
        return None
    return (rng[0] + rng[1]) / 2.0


def _px_mm(mm):
    return (mm / MM_PER_IN) * PX_PER_IN


def _poly(points, fill="#C0C0C0"):
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polygon points="{pts}" fill="{fill}" stroke="black" stroke-width="1"/>'


def contact_size_for(density):
    return "20" if density == "Standard" else "22"


def dash_number(density, shell_no):
    if density == "High":
        return shell_no + 10
    return shell_no


def slash_sheet(connector_type, gender):
    try:
        return SLASH_SHEETS[(connector_type, gender)]
    except KeyError:
        raise ValueError(
            f"No MIL-DTL-24308 slash sheet for "
            f"connector_type={connector_type!r}, gender={gender!r}."
        )


def make_part_number(part_configuration):
    slash = slash_sheet(
        part_configuration["connector_type"], part_configuration["gender"]
    )
    dash = dash_number(
        part_configuration["density"], part_configuration["shell_no"]
    )
    return f"M24308-{slash}_{dash}{part_configuration['finish']}"


def variant_from_configuration(part_configuration):
    return find_variant(
        part_configuration["connector_type"],
        part_configuration["gender"],
        part_configuration["density"],
        shell_no=part_configuration["shell_no"],
    )


def connector_depth_mm(variant):
    maxd = _mid(variant.dims.get("MAX_total_depth"))
    if maxd is not None:
        return maxd
    return _mid(variant.dims["F"])


def dsub_connector_svg(part_number, variant):
    """
    Side silhouette along the mating axis (origin at the mating face, +X
    toward the cable), using midpoints of D, E, F / MAX_total_depth.
    """
    d = _mid(variant.dims["D"])
    e = _mid(variant.dims["E"])
    depth = connector_depth_mm(variant)

    depth_px = _px_mm(depth)
    half_e = _px_mm(e) / 2.0
    half_d = _px_mm(d) / 2.0
    flange_px = min(_px_mm(FLANGE_THICKNESS_MM), depth_px * 0.2)

    outline = [
        (0.0, -half_e),
        (flange_px, -half_e),
        (flange_px, -half_d),
        (depth_px, -half_d),
        (depth_px, half_d),
        (flange_px, half_d),
        (flange_px, half_e),
        (0.0, half_e),
    ]

    insulator_x = flange_px
    insulator_w = max(depth_px - flange_px, 0.0)
    insulator = (
        f'<rect x="{insulator_x:.2f}" y="{-half_d:.2f}" '
        f'width="{insulator_w:.2f}" height="{2 * half_d:.2f}" '
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


def compile_part_attributes(part_configuration):
    variant = variant_from_configuration(part_configuration)
    size = contact_size_for(variant.density)
    size_info = CONTACT_SIZES[size]
    slash = slash_sheet(variant.connector_type, variant.gender)

    contacts = [{"name": str(i), "size": size} for i in range(1, variant.pin_count + 1)]

    if variant.connector_type == "Crimp":
        tools = [
            f"{size_info['crimp_tool']} crimp tool",
            f"{size_info['extraction_tool']} extraction tool",
        ]
    else:
        tools = ["Soldering iron"]

    attributes = {
        "tools": tools,
        "build_notes": [
            f"MIL-DTL-24308/{slash} Class G, no float mount",
        ],
        "csys_children": STANDARD_CSYS_CHILDREN,
        "contacts": contacts,
        "shell_size": variant.shell_no,
        "pin_count": variant.pin_count,
        "density": variant.density,
        "gender": variant.gender,
        "connector_type": variant.connector_type,
    }
    return attributes


def iter_part_configurations():
    for variant in _VARIANTS:
        for finish in FINISHES:
            yield {
                "connector_type": variant.connector_type,
                "gender": variant.gender,
                "density": variant.density,
                "shell_no": variant.shell_no,
                "pin_count": variant.pin_count,
                "finish": finish,
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
    """Write one D-sub part folder, attributes, SVG, and run harnice -b."""
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
        "library_subpath": "Dsub",
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

    variant = variant_from_configuration(part_configuration)
    svg_content = dsub_connector_svg(part_number, variant)
    svg_path = os.path.join(rev_dir, f"{part_number}-rev{REVISION}-drawing.svg")
    with open(svg_path, "w") as f:
        f.write(svg_content)

    subprocess.run(["harnice", "-b"], cwd=rev_dir, check=True)
    if delete_pngs:
        for item in os.listdir(rev_dir):
            if item.endswith(".png"):
                os.remove(os.path.join(rev_dir, item))

    return part_number


def main():
    state.set_rev(REVISION)
    state.set_product("part")

    configs = list(iter_part_configurations())
    total = len(configs)
    for i, part_configuration in enumerate(configs, start=1):
        make_part(part_configuration)
        print(_progress_bar(i, total))

    print("Finished rendering all parts in family.")


if __name__ == "__main__":
    main()
