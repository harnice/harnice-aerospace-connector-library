"""STEP cable-side origin and pin set-in for D-sub / Micro-D envelopes."""

from __future__ import annotations

import math


def shift_segments(segments, origin_x):
    return [(x0 - origin_x, x1 - origin_x, yz) for x0, x1, yz in segments]


def face_x_mm(segments):
    return max(float(x1) for _x0, x1, _yz in segments)


def cable_side_x_mm(segments):
    """Rear / cable-side face of the envelope (first prism start)."""
    return min(float(x0) for x0, _x1, _yz in segments)


def step_origin_x_mm(segments, is_pin, cavity_depth_mm):
    """X of the STEP (part) origin in envelope coordinates.

    Always the cable-side face. Pin cups stay at the mating face — they do
    not move the part origin.
    """
    del is_pin, cavity_depth_mm
    return cable_side_x_mm(segments)


def _inset_yz(yz, wall_mm):
    """Uniform scale of a centered YZ profile to leave an approximate rim wall."""
    max_r = max(math.hypot(float(y), float(z)) for y, z in yz)
    if max_r <= wall_mm + 0.2:
        return None
    scale = (max_r - wall_mm) / max_r
    return [(float(y) * scale, float(z) * scale) for y, z in yz]


def _ocp_cut(body, tool, label):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut

    op = BRepAlgoAPI_Cut(body, tool)
    op.SetFuzzyValue(0.05)
    op.Build()
    cut = op.Shape()
    if not op.IsDone() or cut.IsNull():
        raise RuntimeError(f"{label} cut failed")
    return cut


def write_mating_prism_step(
    step_utils,
    path,
    part_number,
    segments,
    is_pin,
    cavity_depth_mm,
    cavity_wall_mm,
    description,
):
    """Write prism envelope with cable-side origin; plugs get a set-in cup."""
    origin_x = step_origin_x_mm(segments, is_pin, cavity_depth_mm)
    shifted = shift_segments(segments, origin_x)
    try:
        body = step_utils._ocp_prism_segments_solid(shifted)
        if is_pin:
            x_face = face_x_mm(shifted)
            inset = _inset_yz(shifted[-1][2], cavity_wall_mm)
            if inset is not None:
                depth = float(cavity_depth_mm)
                tool = step_utils._ocp_prism_segments_solid(
                    [(x_face - depth, x_face + 1.0, inset)]
                )
                body = _ocp_cut(body, tool, f"{part_number} cavity")
        step_utils._ocp_write_shape(body, path, part_number)
        return path
    except ImportError:
        if is_pin:
            # Mesh fallback: shorten the mating shroud so the face steps in.
            x_face = face_x_mm(shifted)
            depth = float(cavity_depth_mm)
            inset = _inset_yz(shifted[-1][2], cavity_wall_mm)
            fallback = list(shifted[:-1])
            x0, _x1, yz = shifted[-1]
            if inset is None or depth <= 0.2:
                fallback.append(shifted[-1])
            else:
                floor = x_face - depth
                if floor > x0 + 0.05:
                    fallback.append((x0, floor, yz))
                fallback.append((floor, x_face, inset))
            return step_utils.write_prism_segments_step(
                path, part_number, fallback, description=description
            )
        return step_utils.write_prism_segments_step(
            path, part_number, shifted, description=description
        )
