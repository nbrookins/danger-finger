#!/usr/bin/env python3
"""
Post-process Anycubic / Orca-style multi-material G-code: strip existing toolchanges
and inject T0/T1/… swaps on a repeating per-tool layer schedule (1–4 tools).

Use --every N for uniform spacing (same as N layers per tool for each color), or
--layers-per-tool n0,n1,… for different thicknesses per color in cycle order.

Optional: M220 feedrate percentage, F-word scaling in the executable block, absolute bed/tool
temperature overrides during the print phase (after first ;LAYER_CHANGE until end gcode), and
--inspect to summarize the file.

Standalone: Python 3.8+ only, no third-party deps.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

# --- Markers (AnycubicSlicerNext / Bambu-style) ---
RE_LAYER_CHANGE = re.compile(r"^;LAYER_CHANGE\s*$")
RE_LAYER_Z = re.compile(r"^;Z:([0-9.]+)\s*$")
RE_AFTER_LAYER = re.compile(r"^; AFTER_LAYER_CHANGE\s+(\d+)")
RE_TOOL_LINE = re.compile(r"^T(\d+)\s*$")
RE_TOOLCHANGE_START = re.compile(r"^;\s*CP TOOLCHANGE START\s*$")
RE_TOOLCHANGE_END = re.compile(r"^;\s*CP TOOLCHANGE END\s*$")
RE_WIPE_TOWER_START = re.compile(r"^;\s*WIPE_TOWER_START\s*$")
RE_WIPE_TOWER_END = re.compile(r"^;\s*WIPE_TOWER_END\s*$")
RE_FILAMENT_CHANGE = re.compile(r"^;\s*total filament change\s*=\s*(\d+)\s*$", re.I)
RE_G1_Z = re.compile(r"^(?P<prefix>G1\s+Z)(?P<num>[0-9]*\.?[0-9]+)(?P<suffix>.*)$", re.I)
RE_PAINT_INFO = re.compile(r"^(;)\s*paint_info\s*=\s*(.+)\s*$")
RE_EXTRUDER_COLOUR = re.compile(r"^;\s*extruder_colour\s*=\s*(.+)\s*$", re.I)
RE_EXECUTABLE_START = re.compile(r"^; EXECUTABLE_BLOCK_START\s*$")
RE_EXECUTABLE_END = re.compile(r"^; EXECUTABLE_BLOCK_END\s*$")
RE_FILAMENT_END = re.compile(r"^;\s*filament end gcode\s*$", re.I)
RE_M_BED = re.compile(r"^M(140|190)\s", re.I)
RE_M_EXTRUDER = re.compile(r"^M(104|109)\s", re.I)
RE_G_MOTION = re.compile(r"^(G0|G1|G2|G3)(\s|$)", re.I)
RE_F_WORD = re.compile(r"\bF([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\b", re.I)
RE_G9111 = re.compile(
    r"^(G9111\s+bedTemp=)(\d+)(\s+extruderTemp=)(\d+)(.*)$",
    re.I,
)
RE_M220 = re.compile(r"^M220\s+S(\d+)\s*$", re.I)


def find_block_ranges(
    lines: Sequence[str],
    start_re: re.Pattern,
    end_re: re.Pattern,
) -> List[Tuple[int, int]]:
    """Inclusive line index ranges [start, end] for each start..end pair."""
    ranges: List[Tuple[int, int]] = []
    i = 0
    n = len(lines)
    while i < n:
        if start_re.match(lines[i].rstrip("\n")):
            start = i
            j = i + 1
            while j < n:
                if end_re.match(lines[j].rstrip("\n")):
                    ranges.append((start, j))
                    i = j + 1
                    break
                j += 1
            else:
                raise ValueError(f"Unclosed block starting at line {start + 1}")
        else:
            i += 1
    return ranges


def merge_intervals(ranges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    if not ranges:
        return []
    ranges = sorted(ranges)
    out = [list(ranges[0])]
    for a, b in ranges[1:]:
        if a <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(x[0], x[1]) for x in out]


def lines_to_skip(merged: List[Tuple[int, int]]) -> Set[int]:
    skip: Set[int] = set()
    for a, b in merged:
        skip.update(range(a, b + 1))
    return skip


def parse_layers_after_layer_change(lines: Sequence[str]) -> List[Tuple[int, float]]:
    """For each ;LAYER_CHANGE, return (line_index_of_LAYER_CHANGE, z_height)."""
    layers: List[Tuple[int, float]] = []
    n = len(lines)
    i = 0
    while i < n:
        if RE_LAYER_CHANGE.match(lines[i].rstrip("\n")):
            z = 0.0
            if i + 1 < n:
                m = RE_LAYER_Z.match(lines[i + 1].rstrip("\n"))
                if m:
                    z = float(m.group(1))
            layers.append((i, z))
        i += 1
    return layers


def find_after_layer_line_index(lines: Sequence[str], layer_change_idx: int) -> Optional[int]:
    """First ; AFTER_LAYER_CHANGE after this ;LAYER_CHANGE."""
    n = len(lines)
    j = layer_change_idx + 1
    while j < n:
        if RE_LAYER_CHANGE.match(lines[j].rstrip("\n")):
            break
        if RE_AFTER_LAYER.match(lines[j].rstrip("\n")):
            return j
        j += 1
    return None


def parse_after_layer_indices(lines: Sequence[str]) -> List[Tuple[int, int, float]]:
    """
    List of (layer_index, line_index_of_AFTER_LAYER, z) in file order.
    layer_index from comment ; AFTER_LAYER_CHANGE N @ ...
    """
    layers_meta: List[Tuple[int, int, float]] = []
    layer_entries = parse_layers_after_layer_change(lines)
    for lc_idx, z in layer_entries:
        after_idx = find_after_layer_line_index(lines, lc_idx)
        if after_idx is None:
            continue
        m = RE_AFTER_LAYER.match(lines[after_idx].rstrip("\n"))
        if not m:
            continue
        layer_i = int(m.group(1))
        layers_meta.append((layer_i, after_idx, z))
    return layers_meta


def infer_start_tool(lines: Sequence[str], first_layer_change_line: int) -> int:
    last = 0
    for i in range(0, min(first_layer_change_line, len(lines))):
        m = RE_TOOL_LINE.match(lines[i].rstrip("\n"))
        if m:
            last = int(m.group(1))
    return last


def next_tool_in_cycle(current: int, tools: Sequence[int]) -> int:
    if current not in tools:
        return tools[0]
    idx = tools.index(current)
    return tools[(idx + 1) % len(tools)]


def format_z_for_g1(z: float, sample: str) -> str:
    """Match style of sample numeric string (e.g. .8 vs 0.8)."""
    samp = sample.strip()
    out = f"{z:.10f}".rstrip("0").rstrip(".")
    if out.startswith("0.") and samp.startswith("."):
        return "." + out[2:]
    return out


def substitute_z_in_line(line: str, old_z: float, new_z: float, tol: float = 1e-3) -> str:
    m = RE_G1_Z.match(line.rstrip("\n"))
    if not m:
        return line
    try:
        val = float(m.group("num"))
    except ValueError:
        return line
    if abs(val - old_z) > tol:
        return line
    new_part = format_z_for_g1(new_z, m.group("num"))
    nl = "\n" if line.endswith("\n") else ""
    return f"{m.group('prefix')}{new_part}{m.group('suffix')}{nl}"


def apply_template(
    template_lines: Sequence[str],
    new_tool: int,
    old_z: float,
    new_z: float,
    toolchange_seq: int,
) -> List[str]:
    out: List[str] = []
    for line in template_lines:
        stripped = line.rstrip("\n")
        if RE_TOOL_LINE.match(stripped):
            out.append(f"T{new_tool}\n")
            continue
        if re.match(r"^;\s*toolchange\s+#\d+", stripped, re.I):
            out.append(re.sub(r"#\d+", f"#{toolchange_seq}", stripped) + "\n")
            continue
        out.append(substitute_z_in_line(line, old_z, new_z))
    return out


def minimal_injection_block(new_tool: int, seq: int) -> List[str]:
    return [
        ";--------------------\n",
        "; CP TOOLCHANGE START\n",
        f"; toolchange #{seq} (injected by gcode-swap)\n",
        f"T{new_tool}\n",
        "G1 E2 F1800 ; prime (gcode-swap)\n",
        "; CP TOOLCHANGE END\n",
        ";--------------------\n",
    ]


def hex_to_rgb(hex_s: str) -> Tuple[int, int, int]:
    h = hex_s.strip().lstrip("#")
    if len(h) != 6:
        raise ValueError(f"Expected #RRGGBB, got {hex_s!r}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def normalize_hex(color: str) -> str:
    p = color.strip()
    if not p.startswith("#"):
        p = "#" + p
    hex_to_rgb(p)
    return "#" + p.lstrip("#").upper()


def parse_extruder_colours_from_lines(lines: Sequence[str]) -> List[str]:
    for line in lines:
        m = RE_EXTRUDER_COLOUR.match(line.rstrip("\n"))
        if m:
            raw = m.group(1).strip()
            out: List[str] = []
            for seg in raw.split(";"):
                seg = seg.strip()
                if seg.startswith("#"):
                    out.append(seg)
            return out
    return []


def parse_tool_colors_arg(spec: str) -> List[str]:
    return [normalize_hex(p) for p in spec.split(",") if p.strip()]


def default_colors_for_tools(tools: Sequence[int], extruder_hex: Sequence[str]) -> Dict[int, str]:
    """Map tool index -> #RRGGBB from slicer extruder_colour or distinct fallbacks."""
    fallback = ["#E91E63", "#2196F3", "#FF9800", "#4CAF50", "#9C27B0", "#00BCD4"]
    out: Dict[int, str] = {}
    fb = 0
    for t in sorted(set(tools)):
        if t < len(extruder_hex) and extruder_hex[t]:
            hx = extruder_hex[t]
            out[t] = hx if hx.startswith("#") else "#" + hx
        else:
            out[t] = fallback[fb % len(fallback)]
            fb += 1
    return out


def parse_paint_material_type(lines: Sequence[str]) -> str:
    for line in lines:
        m = RE_PAINT_INFO.match(line.rstrip("\n"))
        if not m:
            continue
        try:
            data = json.loads(m.group(2).strip())
            if isinstance(data, list) and data and isinstance(data[0], dict):
                mt = data[0].get("material_type")
                if isinstance(mt, str) and mt:
                    return mt
        except json.JSONDecodeError:
            continue
    return "TPU"


def build_paint_info_json(
    tools: Sequence[int],
    color_by_tool: Dict[int, str],
    material_type: str,
) -> str:
    """Distinct paint_color per extruder index — Anycubic Color Match keys off this."""
    order: List[int] = []
    for t in tools:
        if t not in order:
            order.append(t)
    entries = []
    for t in order:
        hx = normalize_hex(color_by_tool.get(t, "#808080"))
        r, g, b = hex_to_rgb(hx)
        entries.append(
            {
                "material_type": material_type,
                "paint_color": [r, g, b],
                "paint_index": t,
            }
        )
    return json.dumps(entries, separators=(",", ":"))


def patch_paint_info_for_color_match(
    out_lines: List[str],
    source_lines: Sequence[str],
    tools: Sequence[int],
    tool_colors: Optional[str],
) -> None:
    extruder = parse_extruder_colours_from_lines(source_lines)
    uniq = sorted(set(tools))
    if tool_colors:
        parsed = parse_tool_colors_arg(tool_colors)
        if len(parsed) < len(uniq):
            raise ValueError(
                f"--tool-colors needs at least {len(uniq)} comma-separated hex colors "
                f"(got {len(parsed)}) for tools {uniq}"
            )
        color_by_tool = {uniq[i]: parsed[i] for i in range(len(uniq))}
    else:
        color_by_tool = default_colors_for_tools(tools, extruder)

    material = parse_paint_material_type(source_lines)
    payload = build_paint_info_json(tools, color_by_tool, material)
    replacement = f"; paint_info = {payload}\n"
    for i, line in enumerate(out_lines):
        if RE_PAINT_INFO.match(line.rstrip("\n")):
            out_lines[i] = replacement


def filter_lines(lines: List[str], skip: Set[int]) -> List[str]:
    return [lines[i] for i in range(len(lines)) if i not in skip]


def update_filament_change_count(lines: List[str], count: int) -> None:
    for i, line in enumerate(lines):
        if RE_FILAMENT_CHANGE.match(line):
            lines[i] = f"; total filament change = {count}\n"
            return
    # append before CONFIG or at end of summary block
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("; CONFIG_BLOCK_START"):
            insert_at = i
            break
    else:
        insert_at = len(lines)
    lines.insert(insert_at, f"; total filament change = {count}\n")


def add_postprocess_comment(
    lines: List[str],
    schedule_desc: str,
    *,
    paint_patched: bool = False,
) -> None:
    marker = f"; post-processed by gcode-swap: {schedule_desc}\n"
    extra = (
        "; gcode-swap: paint_info lists distinct RGB per extruder for Color Match\n"
        if paint_patched
        else ""
    )
    for i, line in enumerate(lines):
        if line.strip() == "; HEADER_BLOCK_END":
            lines.insert(i + 1, marker)
            if extra:
                lines.insert(i + 2, extra)
            return
    lines.insert(0, marker)
    if extra:
        lines.insert(1, extra)


def find_executable_block_bounds(lines: Sequence[str]) -> Tuple[int, int]:
    """Inclusive start, exclusive end line indices; whole file if markers missing."""
    start: Optional[int] = None
    end: Optional[int] = None
    for i, line in enumerate(lines):
        if start is None and RE_EXECUTABLE_START.match(line.rstrip("\n")):
            start = i
        elif RE_EXECUTABLE_END.match(line.rstrip("\n")):
            end = i
            break
    if start is None:
        return 0, len(lines)
    if end is None:
        return start, len(lines)
    return start, end


def find_print_temperature_window(lines: Sequence[str]) -> Tuple[int, int]:
    """
    Inclusive start, exclusive end. Start = first ;LAYER_CHANGE.
    End = first '; filament end gcode' line index, else EXECUTABLE_BLOCK_END, else EOF.
    """
    n = len(lines)
    start = 0
    found_lc = False
    for i, line in enumerate(lines):
        if RE_LAYER_CHANGE.match(line.rstrip("\n")):
            start = i
            found_lc = True
            break
    if not found_lc:
        return 0, n
    end = n
    for i in range(start, n):
        if RE_FILAMENT_END.match(lines[i].rstrip("\n")):
            end = i
            break
    else:
        for i in range(start, n):
            if RE_EXECUTABLE_END.match(lines[i].rstrip("\n")):
                end = i
                break
    return start, end


def _parse_stokens(line: str) -> Tuple[Optional[int], Optional[int]]:
    """M-command: return (T or None, S or None). S is first S token only."""
    t_val: Optional[int] = None
    s_val: Optional[int] = None
    for m in re.finditer(r"\bT(\d+)\b", line, re.I):
        t_val = int(m.group(1))
    for m in re.finditer(r"\bS([-+]?\d+)\b", line, re.I):
        s_val = int(m.group(1))
        break
    return t_val, s_val


def _format_f_scaled(val: float) -> str:
    if abs(val - round(val)) < 1e-4:
        return str(max(1, int(round(val))))
    s = f"{val:.4f}".rstrip("0").rstrip(".")
    return s if s else "1"


def scale_f_words_in_line(line: str, factor: float) -> str:
    if factor == 1.0:
        return line
    raw = line.rstrip("\n")
    if not raw.strip() or raw.lstrip().startswith(";"):
        return line
    if not RE_G_MOTION.match(raw.lstrip()):
        return line

    def repl(m):
        v = float(m.group(1))
        return "F" + _format_f_scaled(max(1.0, v * factor))

    new_raw = RE_F_WORD.sub(repl, raw)
    nl = "\n" if line.endswith("\n") else ""
    return new_raw + nl


def apply_feedrate_f_scale(lines: List[str], lo: int, hi: int, factor: float) -> None:
    for i in range(max(0, lo), min(len(lines), hi)):
        lines[i] = scale_f_words_in_line(lines[i], factor)


def patch_line_temperature(
    line: str,
    last_tool: int,
    bed_temp: Optional[int],
    tool_temps: Optional[Dict[int, int]],
) -> str:
    raw = line.rstrip("\n")
    if not raw.strip():
        return line

    m9111 = RE_G9111.match(raw)
    if m9111 and (bed_temp is not None or tool_temps):
        old_bed = int(m9111.group(2))
        old_ext = int(m9111.group(4))
        new_bed = str(bed_temp if bed_temp is not None else old_bed)
        if tool_temps:
            new_ext = str(
                tool_temps.get(last_tool, tool_temps.get(0, old_ext))
            )
        else:
            new_ext = str(old_ext)
        nl = "\n" if line.endswith("\n") else ""
        return f"{m9111.group(1)}{new_bed}{m9111.group(3)}{new_ext}{m9111.group(5)}{nl}"

    if RE_M_BED.match(raw) and bed_temp is not None:
        _, s_val = _parse_stokens(raw)
        if s_val is not None and s_val > 0:

            def s_sub(m):
                return m.group(1) + str(bed_temp)

            new_raw = re.sub(r"(\bS)([-+]?\d+)\b", s_sub, raw, count=1)
            nl = "\n" if line.endswith("\n") else ""
            return new_raw + nl

    if RE_M_EXTRUDER.match(raw) and tool_temps:
        t_token, s_val = _parse_stokens(raw)
        t_use = t_token if t_token is not None else last_tool
        if s_val is not None and s_val > 0 and t_use in tool_temps:

            def s_sub(m):
                return m.group(1) + str(tool_temps[t_use])

            new_raw = re.sub(r"(\bS)([-+]?\d+)\b", s_sub, raw, count=1)
            nl = "\n" if line.endswith("\n") else ""
            return new_raw + nl

    return line


def apply_print_temperature_overrides(
    lines: List[str],
    bed_temp: Optional[int],
    tool_temps: Optional[Dict[int, int]],
) -> None:
    if bed_temp is None and not tool_temps:
        return
    lo, hi = find_print_temperature_window(lines)
    last_tool = 0
    for i in range(len(lines)):
        stripped = lines[i].rstrip("\n")
        tm = RE_TOOL_LINE.match(stripped)
        if tm:
            last_tool = int(tm.group(1))
        if lo <= i < hi:
            lines[i] = patch_line_temperature(lines[i], last_tool, bed_temp, tool_temps)


def inject_m220_after_first_print_layer(lines: List[str], percent: int) -> None:
    if not (1 <= percent <= 1000):
        raise ValueError("M220 percent must be 1–1000")
    n = len(lines)
    first_lc: Optional[int] = None
    for i in range(n):
        if RE_LAYER_CHANGE.match(lines[i].rstrip("\n")):
            first_lc = i
            break
    if first_lc is None:
        lines.insert(0, f"M220 S{percent} ; gcode-swap\n")
        return
    insert_at = first_lc + 1
    for j in range(first_lc + 1, n):
        if RE_AFTER_LAYER.match(lines[j].rstrip("\n")):
            insert_at = j + 1
            break
    lines.insert(insert_at, f"M220 S{percent} ; gcode-swap feedrate %\n")


def inject_m220_before_filament_end(lines: List[str], percent: int) -> None:
    if not (1 <= percent <= 1000):
        raise ValueError("M220 reset percent must be 1–1000")
    for i, line in enumerate(lines):
        if RE_FILAMENT_END.match(line.rstrip("\n")):
            lines.insert(i, f"M220 S{percent} ; gcode-swap reset feedrate %\n")
            return
    lines.append(f"M220 S{percent} ; gcode-swap reset feedrate %\n")


def parse_tool_temps_arg(spec: str) -> Dict[int, int]:
    out: Dict[int, int] = {}
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            a, b = part.split(":", 1)
            out[int(a.strip())] = int(b.strip())
        else:
            next_i = len(out)
            out[next_i] = int(part)
    return out


def apply_speed_and_temperature_post(
    lines: List[str],
    *,
    m220_percent: Optional[int],
    feedrate_f_factor: Optional[float],
    bed_temp: Optional[int],
    tool_temps: Optional[Dict[int, int]],
    m220_reset_end: Optional[int],
) -> None:
    apply_print_temperature_overrides(lines, bed_temp, tool_temps)

    ex_lo, ex_hi = find_executable_block_bounds(lines)
    if feedrate_f_factor is not None and abs(feedrate_f_factor - 1.0) > 1e-9:
        apply_feedrate_f_scale(lines, ex_lo, ex_hi, feedrate_f_factor)

    if m220_percent is not None:
        inject_m220_after_first_print_layer(lines, m220_percent)
    if m220_reset_end is not None:
        inject_m220_before_filament_end(lines, m220_reset_end)


def collect_m220_values(lines: Sequence[str]) -> List[int]:
    found: List[int] = []
    for line in lines:
        m = RE_M220.match(line.rstrip("\n"))
        if m:
            found.append(int(m.group(1)))
    return found


def collect_f_stats(lines: Sequence[str], lo: int, hi: int) -> Tuple[int, float, float, float]:
    """Count of F values, min, max, mean (0,0,0,0 if none)."""
    vals: List[float] = []
    for i in range(max(0, lo), min(len(lines), hi)):
        raw = lines[i].rstrip("\n")
        if not raw.strip() or raw.lstrip().startswith(";"):
            continue
        if not RE_G_MOTION.match(raw.lstrip()):
            continue
        for m in RE_F_WORD.finditer(raw):
            vals.append(float(m.group(1)))
    if not vals:
        return 0, 0.0, 0.0, 0.0
    return len(vals), min(vals), max(vals), sum(vals) / len(vals)


def collect_temps_in_window(
    lines: Sequence[str], lo: int, hi: int
) -> Tuple[Dict[int, Set[int]], Set[int]]:
    """Extruder S by tool (best-effort), bed S values."""
    ext_by_tool: Dict[int, Set[int]] = {}
    bed_vals: Set[int] = set()
    last_tool = 0
    for i in range(len(lines)):
        raw = lines[i].rstrip("\n")
        tm = RE_TOOL_LINE.match(raw)
        if tm:
            last_tool = int(tm.group(1))
        if not (lo <= i < hi):
            continue
        m9111 = RE_G9111.match(raw)
        if m9111:
            bed_vals.add(int(m9111.group(2)))
            ext_by_tool.setdefault(0, set()).add(int(m9111.group(4)))
            continue
        if RE_M_BED.match(raw):
            _, s_val = _parse_stokens(raw)
            if s_val is not None:
                bed_vals.add(s_val)
        if RE_M_EXTRUDER.match(raw):
            t_tok, s_val = _parse_stokens(raw)
            tu = t_tok if t_tok is not None else last_tool
            if s_val is not None:
                ext_by_tool.setdefault(tu, set()).add(s_val)
    return ext_by_tool, bed_vals


def run_inspect(lines: List[str]) -> None:
    ex_lo, ex_hi = find_executable_block_bounds(lines)
    pt_lo, pt_hi = find_print_temperature_window(lines)
    layers_lc = parse_layers_after_layer_change(lines)
    if not layers_lc:
        print("WARNING: no ;LAYER_CHANGE found — layer count and print window are unreliable")
    meta = parse_after_layer_indices(lines)
    max_layer = max((m[0] for m in meta), default=-1)
    layer_count = max_layer + 1 if max_layer >= 0 else len(layers_lc)

    print("=== gcode-swap inspect ===")
    print(f"Executable block: lines [{ex_lo}, {ex_hi}) of {len(lines)}")
    print(
        f"Print phase (temp window): lines [{pt_lo}, {pt_hi}) "
        f"(first ;LAYER_CHANGE → before end gcode / block end)"
    )
    print(f"Layer changes: {len(layers_lc)} | max layer index: {max_layer}")
    print(f"Layer count (estimated): {layer_count}")

    m220s = collect_m220_values(lines)
    print(f"M220 S values in file ({len(m220s)}): {m220s if m220s else '—'}")

    n_f, f_min, f_max, f_mean = collect_f_stats(lines, ex_lo, ex_hi)
    print(
        f"Feedrate F in G0–G3 (executable): count={n_f} "
        f"min={f_min:.1f} max={f_max:.1f} mean={f_mean:.1f} mm/min"
    )

    ext_by, beds = collect_temps_in_window(lines, pt_lo, pt_hi)
    print("Temperatures seen in print phase (S>0 extruder/bed; G9111 included):")
    if beds:
        print(f"  Bed S values: {sorted(beds)}")
    else:
        print("  Bed S values: —")
    if ext_by:
        for t in sorted(ext_by.keys()):
            print(f"  Tool T{t} S values: {sorted(ext_by[t])}")
    else:
        print("  Extruder S values: —")

    ext_colors = parse_extruder_colours_from_lines(lines)
    if ext_colors:
        print(f"extruder_colour ({len(ext_colors)}): {', '.join(ext_colors)}")
    else:
        print("extruder_colour: —")

    for line in lines:
        m = RE_PAINT_INFO.match(line.rstrip("\n"))
        if m:
            print(f"paint_info: {m.group(2).strip()[:200]}{'…' if len(m.group(2)) > 200 else ''}")
            break
    else:
        print("paint_info: —")


def build_injection_plan(
    layers_meta: Sequence[Tuple[int, int, float]],
    layers_per: Sequence[int],
    first_layer: int,
    start_tool: int,
    tools: Sequence[int],
) -> List[Tuple[int, int, float, int]]:
    """
    Walk layers in order; inject when the current tool has completed its layer quota.
    layers_per[i] = number of layers printed with tools[i] before switching to the next.
    Matches legacy every-N two-tool behavior when layers_per = [N, N, ...].

    Returns (layer_idx, after_line_index_in_filtered_file, z, new_tool).
    """
    if not layers_meta or len(tools) < 2:
        return []
    if len(layers_per) != len(tools):
        raise ValueError(
            f"layers_per length ({len(layers_per)}) must match tools length ({len(tools)})"
        )
    if any(x < 1 for x in layers_per):
        raise ValueError("each layers-per-tool value must be >= 1")

    sorted_meta = sorted(layers_meta, key=lambda x: x[0])
    num_layers = max(l[0] for l in sorted_meta) + 1
    current = start_tool
    plan: List[Tuple[int, int, float, int]] = []
    phase = 0
    completed = 0

    for layer_idx, after_idx, z in sorted_meta:
        if layer_idx <= 0 or layer_idx >= num_layers or layer_idx < first_layer:
            continue
        if completed >= layers_per[phase]:
            nxt = next_tool_in_cycle(current, tools)
            plan.append((layer_idx, after_idx, z, nxt))
            current = nxt
            completed = 0
            phase = (phase + 1) % len(tools)
        completed += 1

    return plan


def process_gcode(
    lines: List[str],
    first_layer: int,
    tools: Sequence[int],
    layers_per: Sequence[int],
    start_tool: Optional[int],
    no_flush: bool,
    no_wipe_tower: bool,
    dry_run: bool,
    patch_paint: bool = True,
    tool_colors: Optional[str] = None,
    m220_percent: Optional[int] = None,
    feedrate_f_factor: Optional[float] = None,
    bed_temp: Optional[int] = None,
    tool_temps: Optional[Dict[int, int]] = None,
    m220_reset_end: Optional[int] = None,
) -> Tuple[Optional[List[str]], List[Tuple[int, float, int]], str]:
    """
    Returns (output_lines or None if dry_run), plan rows (layer, z, new_tool), message.
    """
    layers_lc = parse_layers_after_layer_change(lines)
    if not layers_lc:
        raise ValueError("No ;LAYER_CHANGE markers found — not a supported G-code file?")

    first_lc_line = layers_lc[0][0]
    inferred = infer_start_tool(lines, first_lc_line)
    st = start_tool if start_tool is not None else inferred

    tc_ranges = find_block_ranges(lines, RE_TOOLCHANGE_START, RE_TOOLCHANGE_END)
    wt_ranges = find_block_ranges(lines, RE_WIPE_TOWER_START, RE_WIPE_TOWER_END)

    to_delete: List[Tuple[int, int]] = list(tc_ranges)
    if no_wipe_tower:
        to_delete.extend(wt_ranges)

    skip = lines_to_skip(merge_intervals(to_delete))
    filtered = filter_lines(lines, skip)

    layers_meta = parse_after_layer_indices(filtered)
    plan = build_injection_plan(layers_meta, layers_per, first_layer, st, tools)

    dry_rows = [(layer_idx, z, new_tool) for layer_idx, _, z, new_tool in plan]

    if dry_run:
        return None, dry_rows, ""

    # Extract template from first original toolchange block
    template_lines: List[str] = []
    old_template_z = 0.0
    if tc_ranges and not no_flush:
        start, end = tc_ranges[0]
        template_lines = lines[start + 1 : end]
        # Z from layer where this toolchange sat (search backward for ;Z:)
        for k in range(start, -1, -1):
            m = RE_LAYER_Z.match(lines[k].rstrip("\n"))
            if m:
                old_template_z = float(m.group(1))
                break

    inject_after_filtered_line: Dict[int, Tuple[float, int]] = {
        after_idx: (z, new_tool) for layer_idx, after_idx, z, new_tool in plan
    }

    out_lines: List[str] = []
    seq = 1
    for fi, line in enumerate(filtered):
        out_lines.append(line)
        if fi in inject_after_filtered_line:
            z_new, new_tool = inject_after_filtered_line[fi]
            if no_flush or not template_lines:
                out_lines.extend(minimal_injection_block(new_tool, seq))
            else:
                out_lines.extend(
                    apply_template(template_lines, new_tool, old_template_z, z_new, seq)
                )
            seq += 1

    paint_done = False
    if patch_paint and len(tools) >= 1:
        patch_paint_info_for_color_match(out_lines, lines, tools, tool_colors)
        paint_done = True

    update_filament_change_count(out_lines, len(plan))
    if len(tools) < 2:
        sched = f"single tool T{tools[0]} (no injected swaps)"
    elif len(set(layers_per)) == 1:
        sched = f"every {layers_per[0]} layers ({len(tools)} tools)"
    else:
        sched = (
            f"layers per tool {'/'.join(str(x) for x in layers_per)} "
            f"(tools {','.join(str(t) for t in tools)})"
        )
    add_postprocess_comment(out_lines, sched, paint_patched=paint_done)

    apply_speed_and_temperature_post(
        out_lines,
        m220_percent=m220_percent,
        feedrate_f_factor=feedrate_f_factor,
        bed_temp=bed_temp,
        tool_temps=tool_temps,
        m220_reset_end=m220_reset_end,
    )

    return out_lines, dry_rows, ""


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Inject periodic toolchanges into sliced G-code (1–4 tools, per-tool layer counts).",
    )
    p.add_argument("input", type=Path, help="Input .gcode file")
    p.add_argument(
        "--inspect",
        action="store_true",
        help="Print layers, speeds (M220, F stats), temps in print phase, colors; no output file",
    )
    p.add_argument(
        "-n",
        "--every",
        type=int,
        default=None,
        metavar="N",
        help="Same layer count for every tool in the cycle (use with 2–4 tools). "
        "Alternative: --layers-per-tool.",
    )
    p.add_argument(
        "--layers-per-tool",
        type=str,
        default=None,
        metavar="N0,N1,...",
        help="Comma-separated layer counts, one per --tools entry in order; cycle repeats. "
        "Example: --tools 0,1,2 --layers-per-tool 8,3,5",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output path (default: <input_stem>_swapped.gcode)",
    )
    p.add_argument(
        "--start-tool",
        type=int,
        default=None,
        help="Active tool before first layer (default: infer from T command before first layer)",
    )
    p.add_argument(
        "--tools",
        type=str,
        default="0,1",
        help="Comma-separated tool indices to cycle, 1–4 entries (default: 0,1)",
    )
    p.add_argument(
        "--no-flush",
        action="store_true",
        help="Skip copied flush/wipe template; only T + short prime",
    )
    p.add_argument(
        "--no-wipe-tower",
        action="store_true",
        help="Remove all ; WIPE_TOWER_* sections from output",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned layer / Z / new tool; do not write",
    )
    p.add_argument(
        "--first-layer",
        type=int,
        default=0,
        metavar="N",
        help="Layer index to align the every-N pattern (default: 0 → inject at N, 2N, …)",
    )
    p.add_argument(
        "--no-patch-paint",
        action="store_true",
        help="Do not rewrite paint_info (Color Match may show duplicate colors)",
    )
    p.add_argument(
        "--tool-colors",
        type=str,
        default=None,
        metavar="HEX,HEX,...",
        help="Override colors for Color Match, one #RRGGBB per unique --tools index in sorted order",
    )
    p.add_argument(
        "--m220-percent",
        type=int,
        default=None,
        metavar="PCT",
        help="Inject M220 S<PCT> after first layer (firmware feedrate scale, e.g. 60)",
    )
    p.add_argument(
        "--f-percent",
        type=int,
        default=None,
        metavar="PCT",
        help="Multiply every F in the executable block by PCT/100 (e.g. 60 → 0.6×)",
    )
    p.add_argument(
        "--f-factor",
        type=float,
        default=None,
        metavar="K",
        help="Multiply every F in the executable block by K (overrides --f-percent if both set)",
    )
    p.add_argument(
        "--bed-temp",
        type=int,
        default=None,
        metavar="C",
        help="Replace bed M140/M190 S (>0) in print phase with this °C",
    )
    p.add_argument(
        "--tool-temps",
        type=str,
        default=None,
        metavar="SPEC",
        help="Extruder temps in print phase: comma list 220,225 (T0,T1,…) or 0:220,1:225",
    )
    p.add_argument(
        "--m220-reset-end",
        type=int,
        default=None,
        metavar="PCT",
        help="Insert M220 S<PCT> before '; filament end gcode' (e.g. 100 to reset)",
    )

    args = p.parse_args(list(argv) if argv is not None else None)

    inp = args.input.expanduser()
    if not inp.is_file():
        print(f"Error: input not found: {inp}", file=sys.stderr)
        return 1

    text = inp.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)

    if args.inspect:
        try:
            run_inspect(lines)
        except (ValueError, OSError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        return 0

    if args.layers_per_tool and args.every is not None:
        p.error("use either --every or --layers-per-tool, not both")

    if args.f_factor is not None and args.f_percent is not None:
        p.error("use either --f-factor or --f-percent, not both")

    feedrate_f_factor: Optional[float] = None
    if args.f_factor is not None:
        if args.f_factor <= 0:
            p.error("--f-factor must be > 0")
        feedrate_f_factor = args.f_factor
    elif args.f_percent is not None:
        if not (1 <= args.f_percent <= 1000):
            p.error("--f-percent must be 1–1000")
        feedrate_f_factor = args.f_percent / 100.0

    if args.m220_percent is not None and not (1 <= args.m220_percent <= 1000):
        p.error("--m220-percent must be 1–1000")
    if args.m220_reset_end is not None and not (1 <= args.m220_reset_end <= 1000):
        p.error("--m220-reset-end must be 1–1000")

    tool_temp_map: Optional[Dict[int, int]] = None
    if args.tool_temps:
        tool_temp_map = parse_tool_temps_arg(args.tool_temps)

    tools = [int(x.strip()) for x in args.tools.split(",") if x.strip()]
    if len(tools) < 1 or len(tools) > 4:
        p.error("--tools must list 1–4 tool indices")

    layers_per: List[int]
    if args.layers_per_tool:
        layers_per = [int(x.strip()) for x in args.layers_per_tool.split(",") if x.strip()]
        if len(layers_per) != len(tools):
            p.error("--layers-per-tool must have exactly as many integers as --tools")
        if any(x < 1 for x in layers_per):
            p.error("--layers-per-tool values must be >= 1")
    elif len(tools) == 1:
        layers_per = [1]
    else:
        if args.every is None:
            p.error("with 2–4 tools, pass --every N or --layers-per-tool n0,n1,…")
        if args.every < 1:
            p.error("--every must be >= 1")
        layers_per = [args.every] * len(tools)

    try:
        out_lines, rows, _ = process_gcode(
            lines,
            first_layer=args.first_layer,
            tools=tools,
            layers_per=layers_per,
            start_tool=args.start_tool,
            no_flush=args.no_flush,
            no_wipe_tower=args.no_wipe_tower,
            dry_run=args.dry_run,
            patch_paint=not args.no_patch_paint,
            tool_colors=args.tool_colors,
            m220_percent=args.m220_percent,
            feedrate_f_factor=feedrate_f_factor,
            bed_temp=args.bed_temp,
            tool_temps=tool_temp_map,
            m220_reset_end=args.m220_reset_end,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"{'Layer':>6}  {'Z':>8}  -> T")
    print("-" * 28)
    for layer_idx, z, new_tool in rows:
        print(f"{layer_idx:6d}  {z:8.4f}  -> T{new_tool}")
    print(f"Total swaps: {len(rows)}")

    if args.dry_run:
        return 0

    out_path = args.output
    if out_path is None:
        out_path = inp.with_name(f"{inp.stem}_swapped{inp.suffix}")

    out_path.write_text("".join(out_lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
