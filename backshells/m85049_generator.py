import os
import json
import math
import subprocess
from harnice.lists import rev_history
from harnice import state

REVISION = "1"
DATE_STARTED = "8/7/26"

# SVG px per inch — must match harnice part.py csys rendering (96 px/in)
PX_PER_IN = 96.0

# Straight (/88) body length callout from Glenair drawing: 1.35 (34.3) Max
# to the start of the banding platform. Banding platform length is not tabulated.
STRAIGHT_BODY_IN = 1.35
BAND_PLATFORM_IN = 0.35

# TABLE I — inches (mm). E entry 02/03; F/G for 45°; H/J for 90°.
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

# TABLE II — aluminum finish codes (composite codes omitted from family gen)
FINISHES = {
    "G": "Electroless Nickel (Space Grade)",
    "N": "Electroless Nickel",
    "P": "Cadmium Olive Drab over Electroless Nickel, Selective Plating",
    "W": "Cadmium Olive Drab",
    "X": "Nickel Fluorocarbon Polymer",
    "YP": "Pure Dense Electrodeposited Aluminum, Selective Plating",
    "Z": "Zinc Nickel",
    "ZP": "Zinc Nickel, Selective Plating",
}

ORIENTATIONS = {
    "88": "straight",
    "89": "45",
    "90": "90",
}

# Polar flagnotes: same ray from origin through leader_dest and flagnote.
# Angles match the original every-15° layout (degrees, math +Y up).
FLAGNOTE_ANGLES_DEG = [0, 15, -15, 30, -30, 45, -45, 60, -60, -75, 75, -90, 90]
FLAGNOTE_OFFSET_IN = 2.0  # flagnote sits this far beyond the perimeter hit


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


def _rect(x, y, w, h, fill="#C0C0C0"):
    return (
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
        f'fill="{fill}" stroke="black" stroke-width="2"/>'
    )


def _poly(points, fill="#C0C0C0"):
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polygon points="{pts}" fill="{fill}" stroke="black" stroke-width="2"/>'


def banding_ribs(x0, y_top, y_bot, length, count=5):
    """Short vertical rib marks on the banding platform."""
    if length <= 0 or count < 1:
        return ""
    step = length / (count + 1)
    lines = []
    for i in range(1, count + 1):
        x = x0 + i * step
        lines.append(
            f'<line x1="{x:.2f}" y1="{y_top:.2f}" x2="{x:.2f}" y2="{y_bot:.2f}" '
            f'stroke="black" stroke-width="1"/>'
        )
    return "\n".join(lines)


def platform_od_in(shell_size, entry_size):
    """Banding platform outer diameter (inches), slightly over E dia."""
    e_in, _ = entry_dia(shell_size, entry_size)
    c_in = SHELL_DATA[shell_size]["c_in"]
    return max(e_in + 0.16, c_in * 0.45)


def straight_backshell_svg(part_number, shell_size, entry_size):
    """Cable −X from origin; body inline with cable extends +X to connector."""
    data = SHELL_DATA[shell_size]

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

    # x=0 at cable entry face; body +X; cable extends −X
    x0 = 0.0
    x1 = band_len
    x2 = band_len + taper_len
    x3 = band_len + taper_len + mid_len
    x4 = band_len + body_len

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

    ribs = banding_ribs(x0, -half_e, half_e, band_len)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="400" height="400">
<g id="{part_number}-drawing-contents-start">
{_poly(outline)}
{_rect(x3, -half_c, nut_len, c, fill="#A8A8A8")}
{ribs}
</g>
<g id="{part_number}-drawing-contents-end">
</g>
</svg>'''


def fortyfive_backshell_svg(part_number, shell_size, entry_size):
    """Cable −X from origin; body +X along G, then 45° up along F to connector."""
    data = SHELL_DATA[shell_size]

    c = px_in(data["c_in"])
    e_od = px_in(platform_od_in(shell_size, entry_size))
    f = px_in(data["f_in"])
    g = px_in(data["g_in"])
    nut_len = f * 0.35

    half_c = c / 2
    half_e = e_od / 2
    angle = math.radians(45)
    cos_a, sin_a = math.cos(angle), math.sin(angle)

    # SVG y is down; negative Y is up
    def offset_point(cx, cy, tx, ty, dist):
        nx, ny = -ty, tx
        return cx + nx * dist, cy + ny * dist

    # Centerline: cable (0,0) → +X by G → 45° up-right by F to connector
    c0 = (0.0, 0.0)
    c1 = (g, 0.0)
    c2 = (g + f * cos_a, -f * sin_a)

    w0, w1, w2 = half_e, (half_c + half_e) / 2, half_c

    top = [
        offset_point(*c0, 1, 0, w0),
        offset_point(*c1, 1, 0, w1),
        offset_point(c2[0] - nut_len * cos_a, c2[1] + nut_len * sin_a, cos_a, -sin_a, w2),
        offset_point(*c2, cos_a, -sin_a, w2),
    ]
    bot = [
        offset_point(*c2, cos_a, -sin_a, -w2),
        offset_point(c2[0] - nut_len * cos_a, c2[1] + nut_len * sin_a, cos_a, -sin_a, -w2),
        offset_point(*c1, 1, 0, -w1),
        offset_point(*c0, 1, 0, -w0),
    ]
    outline = top + bot

    rib_lines = []
    for i in range(1, 5):
        t = i * 0.04
        cx = g * t
        p1 = offset_point(cx, 0.0, 1, 0, w0)
        p2 = offset_point(cx, 0.0, 1, 0, -w0)
        rib_lines.append(
            f'<line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
            f'stroke="black" stroke-width="1"/>'
        )

    nut_x = c2[0] - nut_len * cos_a
    nut_y = c2[1] + nut_len * sin_a
    # Approximate nut as a rect aligned to the 45° exit (axis-aligned bbox of nut segment)
    nut_pts = [
        offset_point(nut_x, nut_y, cos_a, -sin_a, half_c),
        offset_point(*c2, cos_a, -sin_a, half_c),
        offset_point(*c2, cos_a, -sin_a, -half_c),
        offset_point(nut_x, nut_y, cos_a, -sin_a, -half_c),
    ]

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="400" height="400">
<g id="{part_number}-drawing-contents-start">
{_poly(outline)}
{_poly(nut_pts, fill="#A8A8A8")}
{chr(10).join(rib_lines)}
</g>
<g id="{part_number}-drawing-contents-end">
</g>
</svg>'''


def ninety_backshell_svg(part_number, shell_size, entry_size):
    """Cable −X from origin; body +X along J, then +Y along H to connector."""
    data = SHELL_DATA[shell_size]

    c = px_in(data["c_in"])
    e_od = px_in(platform_od_in(shell_size, entry_size))
    h = px_in(data["h_in"])
    j = px_in(data["j_in"])
    nut_len = h * 0.30

    half_c = c / 2
    half_e = e_od / 2

    # Cable at (0,0); bend at (J, 0); connector face at (J, H) facing +Y
    x_bend = j
    y_conn = -h  # SVG: negative Y is up

    outline = [
        (0.0, -half_e),
        (x_bend - half_c, -half_e),
        (x_bend - half_c, y_conn),
        (x_bend + half_c, y_conn),
        (x_bend + half_c, half_e),
        (0.0, half_e),
    ]

    inset = min(half_e, half_c) * 0.45
    inner = [
        (inset, -half_e + inset),
        (x_bend - half_c + inset, -half_e + inset),
        (x_bend - half_c + inset, y_conn + inset),
        (x_bend + half_c - inset, y_conn + inset),
        (x_bend + half_c - inset, half_e - inset),
        (inset, half_e - inset),
    ]

    rib_lines = []
    band = px_in(BAND_PLATFORM_IN)
    for i in range(1, 5):
        x = i * (band / 5)
        rib_lines.append(
            f'<line x1="{x:.2f}" y1="{-half_e:.2f}" '
            f'x2="{x:.2f}" y2="{half_e:.2f}" stroke="black" stroke-width="1"/>'
        )

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="400" height="400">
<g id="{part_number}-drawing-contents-start">
{_poly(outline)}
{_poly(inner, fill="#D8D8D8")}
{_rect(x_bend - half_c, y_conn, c, nut_len, fill="#A8A8A8")}
{chr(10).join(rib_lines)}
</g>
<g id="{part_number}-drawing-contents-end">
</g>
</svg>'''


def backshell_svg(part_number, orientation, shell_size, entry_size):
    if orientation == "straight":
        return straight_backshell_svg(part_number, shell_size, entry_size)
    if orientation == "45":
        return fortyfive_backshell_svg(part_number, shell_size, entry_size)
    if orientation == "90":
        return ninety_backshell_svg(part_number, shell_size, entry_size)
    raise ValueError(f"Unknown orientation '{orientation}'")


def connector_csys(orientation, shell_size):
    """Connector mating face csys in inches; origin is cable entry.

    Cable extends −X from origin; body inline with cable extends +X.
    """
    data = SHELL_DATA[shell_size]
    if orientation == "straight":
        length_in = STRAIGHT_BODY_IN + BAND_PLATFORM_IN
        return {"x": length_in, "y": 0, "angle": 0, "rotation": 0}
    if orientation == "45":
        f, g = data["f_in"], data["g_in"]
        return {
            "x": g + f * math.cos(math.radians(45)),
            "y": f * math.sin(math.radians(45)),
            "angle": 0,
            "rotation": 45,
        }
    if orientation == "90":
        # +X along J (cable-inline), +Y along H to connector face
        return {
            "x": data["j_in"],
            "y": data["h_in"],
            "angle": 0,
            "rotation": 90,
        }
    raise ValueError(f"Unknown orientation '{orientation}'")


def part_perimeter_inches(orientation, shell_size, entry_size):
    """Outer silhouette vertices in inches (math coords, +Y up), CCW, closed."""
    data = SHELL_DATA[shell_size]
    half_c = data["c_in"] / 2
    half_e = platform_od_in(shell_size, entry_size) / 2

    if orientation == "straight":
        length = STRAIGHT_BODY_IN + BAND_PLATFORM_IN
        band = BAND_PLATFORM_IN
        taper = STRAIGHT_BODY_IN * 0.12
        # Stepped body matching the drawing outline
        pts = [
            (0.0, half_e),
            (band, half_e),
            (band + taper, half_c),
            (length, half_c),
            (length, -half_c),
            (band + taper, -half_c),
            (band, -half_e),
            (0.0, -half_e),
        ]
    elif orientation == "45":
        f, g = data["f_in"], data["g_in"]
        a = math.radians(45)
        cos_a, sin_a = math.cos(a), math.sin(a)
        # Centerline: (0,0) → (G,0) → (G+F·cos45, F·sin45)
        # Outer offsets roughly at half_e along exit, half_c at connector
        def off(cx, cy, tx, ty, dist):
            nx, ny = -ty, tx
            return (cx + nx * dist, cy + ny * dist)

        c0 = (0.0, 0.0)
        c1 = (g, 0.0)
        c2 = (g + f * cos_a, f * sin_a)
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
        # Cable at (0,0); bend at (J,0); connector at (J,H)
        pts = [
            (0.0, half_e),
            (j - half_c, half_e),
            (j - half_c, h),
            (j + half_c, h),
            (j + half_c, -half_e),
            (0.0, -half_e),
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
        length = STRAIGHT_BODY_IN + BAND_PLATFORM_IN
        return (length, half_c), (length, -half_c)

    if orientation == "45":
        f, g = data["f_in"], data["g_in"]
        a = math.radians(45)
        cos_a, sin_a = math.cos(a), math.sin(a)
        c2 = (g + f * cos_a, f * sin_a)
        # Face is perpendicular to the F centerline at the connector end
        nx, ny = -sin_a, cos_a
        return (
            (c2[0] + nx * half_c, c2[1] + ny * half_c),
            (c2[0] - nx * half_c, c2[1] - ny * half_c),
        )

    if orientation == "90":
        h, j = data["h_in"], data["j_in"]
        return (j - half_c, h), (j + half_c, h)

    raise ValueError(f"Unknown orientation '{orientation}'")


def _points_close(a, b, tol=1e-4):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def _same_segment(a0, a1, b0, b1, tol=1e-4):
    return (
        (_points_close(a0, b0, tol) and _points_close(a1, b1, tol))
        or (_points_close(a0, b1, tol) and _points_close(a1, b0, tol))
    )


def _ray_edge_intersection_t(angle_rad, p0, p1, eps=1e-9):
    """Distance t>=0 along ray from origin at angle_rad to segment p0→p1, or None."""
    dx, dy = math.cos(angle_rad), math.sin(angle_rad)
    ex, ey = p1[0] - p0[0], p1[1] - p0[1]
    # Solve t*(dx,dy) = p0 + u*(ex,ey),  t>=0, u in [0,1]
    det = dx * ey - dy * ex
    if abs(det) < eps:
        return None  # parallel
    # t = (p0 × edge) / det   using 2D cross
    t = (p0[0] * ey - p0[1] * ex) / det
    u = (p0[0] * dy - p0[1] * dx) / det
    if t < -eps or u < -eps or u > 1 + eps:
        return None
    return max(0.0, t)


def _ray_perimeter_exit_distance(angle_deg, perimeter, exclude_edges=None):
    """Farthest intersection of a polar ray with the part perimeter (inches).

    Edges in exclude_edges (list of (p0, p1)) are skipped — used to keep
    leaders off the connector mating face.
    """
    if perimeter[0] != perimeter[-1]:
        perimeter = perimeter + [perimeter[0]]
    exclude_edges = exclude_edges or []
    angle_rad = math.radians(angle_deg)
    hits = []
    for i in range(len(perimeter) - 1):
        p0, p1 = perimeter[i], perimeter[i + 1]
        if any(_same_segment(p0, p1, e0, e1) for e0, e1 in exclude_edges):
            continue
        t = _ray_edge_intersection_t(angle_rad, p0, p1)
        if t is not None and t > 1e-6:
            hits.append(t)
    if not hits:
        return None
    return max(hits)


def flagnote_csys_children(orientation, shell_size, entry_size):
    """Polar flagnotes on one shared radius; leaders at each ray's perimeter hit.

    Flagnotes sit on a circle: r_flag = max(perimeter hits) + FLAGNOTE_OFFSET_IN.
    Leaders keep per-angle radii from the part geometry, never on the connector face.
    """
    perimeter = part_perimeter_inches(orientation, shell_size, entry_size)
    mating = connector_mating_face_inches(orientation, shell_size, entry_size)
    exclude = [mating]

    leaders = []
    for angle in FLAGNOTE_ANGLES_DEG:
        r_leader = _ray_perimeter_exit_distance(angle, perimeter, exclude_edges=exclude)
        if r_leader is None:
            continue
        leaders.append((angle, r_leader))

    if not leaders:
        return {}

    r_flag = max(r for _, r in leaders) + FLAGNOTE_OFFSET_IN

    children = {}
    for i, (angle, r_leader) in enumerate(leaders, start=1):
        children[f"flagnote-{i}-leader_dest"] = {
            "angle": angle,
            "distance": round(r_leader, 4),
            "rotation": 0,
        }
        children[f"flagnote-{i}"] = {
            "angle": angle,
            "distance": round(r_flag, 4),
            "rotation": 0,
        }
    return children


def compile_part_attributes(part_configuration):
    shell_size = part_configuration["shell_size"]
    entry_size = part_configuration["entry_size"]
    orientation = ORIENTATIONS[part_configuration["basic"]]
    finish = part_configuration["finish"]
    detent = part_configuration["detent"]
    data = SHELL_DATA[shell_size]
    e_in, e_mm = entry_dia(shell_size, entry_size)

    csys = {
        # Origin = cable entry; cable −X; body +X (then up for angled)
        "connector": connector_csys(orientation, shell_size),
    }
    csys.update(flagnote_csys_children(orientation, shell_size, entry_size))

    attributes = {
        "tools": ["AS85049/128 band"],
        "build_notes": [
            "Banding backshell with self-locking coupling for MIL-DTL-38999 Series III/IV (designator H).",
        ],
        "csys_children": csys,
        "item_type": "backshell",
        "connector_designator": "H",
        "orientation": orientation,
        "shell_size": shell_size,
        "entry_size": entry_size,
        "finish": finish,
        "finish_description": FINISHES[finish],
        "detent": "non-detented" if detent == "N" else "detented",
        "a_thread": data["a_thread"],
        "c_dia_in": data["c_in"],
        "c_dia_mm": data["c_mm"],
        "e_dia_in": e_in,
        "e_dia_mm": e_mm,
        "f_max_in": data["f_in"],
        "g_max_in": data["g_in"],
        "h_max_in": data["h_in"],
        "j_max_in": data["j_in"],
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


def main():
    state.set_rev(REVISION)
    state.set_product("part")

    for part_configuration in iter_part_configurations():
        part_number = make_part_number(
            part_configuration["basic"],
            part_configuration["detent"],
            part_configuration["shell_size"],
            part_configuration["finish"],
            part_configuration["entry_size"],
        )
        print("Preparing part number: ", part_number)

        part_dir = os.path.join(os.getcwd(), part_number)
        os.makedirs(part_dir, exist_ok=True)

        revision_history_content_dict = {
            "product": state.product,
            "mfg": "mil spec",
            "pn": part_number,
            "rev": REVISION,
            "desc": "",
            "status": "",
            "datestarted": DATE_STARTED,
            "library_repo": "https://github.com/harnice/d38999",
            "library_subpath": "Backshell",
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

        json_path = os.path.join(
            rev_dir, f"{part_number}-rev{REVISION}-attributes.json"
        )
        attributes = compile_part_attributes(part_configuration)
        with open(json_path, "w") as f:
            json.dump(attributes, f, indent=2)

        orientation = ORIENTATIONS[part_configuration["basic"]]
        svg_content = backshell_svg(
            part_number,
            orientation,
            part_configuration["shell_size"],
            part_configuration["entry_size"],
        )
        svg_path = os.path.join(rev_dir, f"{part_number}-rev{REVISION}-drawing.svg")
        with open(svg_path, "w") as f:
            f.write(svg_content)

        # d38999_generator used `harnice -r`; current CLI builds with -b
        subprocess.run(["harnice", "-b"], cwd=rev_dir, check=True)

    print("Finished rendering all parts in family.")


if __name__ == "__main__":
    main()
