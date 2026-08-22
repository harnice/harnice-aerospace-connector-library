"""Repository-wide part-family generator.

Each family still owns its catalog and emitter. This script is the one
entry point that can list, count, check, or run every emitter, and it
is what CI calls.

    python generate.py --list
    python generate.py --dry-run
    python generate.py --check
    python generate.py --family D38999 --step-only
    python generate.py                    # full generate, every family
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Family:
    name: str
    directory: str
    script: str
    kind: str
    aliases: tuple[str, ...] = ()
    pn_prefix: str | None = None
    flags: frozenset[str] = field(default_factory=frozenset)
    catalog_csv: str | None = None

    @property
    def family_dir(self) -> Path:
        return REPO_ROOT / self.directory

    @property
    def script_path(self) -> Path:
        return self.family_dir / self.script

    def accepts(self, flag: str) -> bool:
        return flag in self.flags


FAMILIES: tuple[Family, ...] = (
    Family(
        name="D38999",
        directory="D38999",
        script="d38999_generator.py",
        kind="part",
        aliases=("d38999",),
        pn_prefix="D38999_",
        flags=frozenset(
            {
                "--step-only",
                "--svg-only",
                "--dry-run",
                "--cli",
                "--24-only",
                "--26-only",
                "--pins-only",
                "--sockets-only",
            }
        ),
    ),
    Family(
        name="M85049",
        directory="M85049",
        script="m85049_generator.py",
        kind="part",
        aliases=("m85049",),
        pn_prefix="M85049-",
        flags=frozenset({"--step-only", "--dry-run", "--cli"}),
    ),
    Family(
        name="mighty_mouse",
        directory="mighty_mouse",
        script="mighty_mouse_generator.py",
        kind="part",
        aliases=("mightymouse", "800-006"),
        pn_prefix="800-006-",
        flags=frozenset({"--step-only", "--dry-run"}),
    ),
    Family(
        name="dsub",
        directory="dsub",
        script="dsub_generator.py",
        kind="part",
        aliases=("d-sub", "m24308"),
        pn_prefix="M24308_",
        flags=frozenset({"--step-only", "--csv-only", "--dry-run"}),
        catalog_csv="dsub.csv",
    ),
    Family(
        name="microd",
        directory="dsub",
        script="microd_generator.py",
        kind="part",
        aliases=("micro-d", "m83513"),
        pn_prefix="M83513_",
        flags=frozenset({"--step-only", "--dry-run"}),
    ),
    Family(
        name="thermocouple",
        directory="thermocouple",
        script="thermocouple_generator.py",
        kind="part",
        aliases=("tc", "ost"),
        pn_prefix="OST-",
        flags=frozenset({"--step-only", "--csv-only", "--dry-run"}),
        catalog_csv="thermocouple.csv",
    ),
    Family(
        name="M22759",
        directory="M22759",
        script="m22759_generator.py",
        kind="cable",
        aliases=("m22759",),
        pn_prefix="M22759_",
        flags=frozenset({"--dry-run", "--no-build", "--csv-only"}),
        catalog_csv="M22759.csv",
    ),
    Family(
        name="M27500",
        directory="M27500",
        script="m27500_generator.py",
        kind="cable",
        aliases=("m27500",),
        pn_prefix="M27500-",
        flags=frozenset({"--dry-run", "--no-build", "--csv-only", "--cli"}),
        catalog_csv="M27500.csv",
    ),
)

_FAMILY_BY_KEY = {}
for _family in FAMILIES:
    _FAMILY_BY_KEY[_family.name.lower()] = _family
    for _alias in _family.aliases:
        _FAMILY_BY_KEY[_alias.lower()] = _family


SKIP_DIR_NAMES = frozenset({"__pycache__", ".git"})


def resolve_family(name: str) -> Family:
    try:
        return _FAMILY_BY_KEY[name.lower()]
    except KeyError:
        known = ", ".join(family.name for family in FAMILIES)
        raise SystemExit(f"Unknown family {name!r}. Known families: {known}")


def import_generator(family: Family):
    """Load a family emitter by path so two scripts can share a directory."""
    family_dir = str(family.family_dir)
    if family_dir not in sys.path:
        sys.path.insert(0, family_dir)
    module_name = f"harnice_library_{family.name}"
    spec = importlib.util.spec_from_file_location(module_name, family.script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {family.script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def iter_catalog(family: Family, module):
    """Yield ``(part_number, configuration)`` for every legal SKU."""
    if family.name == "M22759":
        for cfg in module.M22759.iter_part_configurations():
            yield module.M22759.make_part_number(cfg), cfg
        return
    if family.name == "M27500":
        for cfg in module.iter_cable_configurations():
            yield module.configuration_part_number(cfg), cfg
        return
    if family.name == "M85049":
        for cfg in module.iter_part_configurations():
            yield (
                module.make_part_number(
                    cfg["basic"],
                    cfg["detent"],
                    cfg["shell_size"],
                    cfg["finish"],
                    cfg["entry_size"],
                ),
                cfg,
            )
        return
    if family.name == "mighty_mouse":
        for cfg in module.iter_part_configurations():
            yield (
                module.make_part_number(
                    cfg["shell_style"],
                    cfg["finish"],
                    cfg["insert_arrangement"],
                    cfg["contact_type"],
                    cfg["key"],
                ),
                cfg,
            )
        return
    for cfg in module.iter_part_configurations():
        yield module.make_part_number(cfg), cfg


def part_numbers_from_catalog(family: Family, module) -> list[str]:
    return [part_number for part_number, _cfg in iter_catalog(family, module)]


def expected_attributes(family: Family, module, cfg):
    if family.kind == "cable":
        return module.compile_cable_attributes(cfg)
    return module.compile_part_attributes(cfg)


def expected_svg(family: Family, module, part_number, cfg, attributes):
    if family.name == "D38999":
        return module.connector_svg(
            part_number,
            cfg["shell_type"],
            attributes.get("shell_size"),
            cfg.get("finish"),
        )
    if family.name == "M85049":
        return module.backshell_svg(
            part_number,
            module.ORIENTATIONS[cfg["basic"]],
            cfg["shell_size"],
            cfg["entry_size"],
            cfg.get("finish"),
        )
    if family.name == "mighty_mouse":
        return module.plug_svg(
            part_number,
            cfg["shell_size"],
            cfg["shell_style"],
            cfg.get("finish"),
        )
    if family.name == "dsub":
        return module.dsub_connector_svg(
            part_number, module.variant_from_configuration(cfg)
        )
    if family.name == "microd":
        return module.microd_connector_svg(part_number, cfg)
    if family.name == "thermocouple":
        return module.thermocouple_svg(part_number, cfg["tc_type"], cfg["gender"])
    return None


def svg_envelope(svg_text: str, part_number: str) -> str | None:
    """Inner markup of the generator-owned drawing-contents group.

    Harnice -b reindents the file and appends csys overlays. The envelope
    between ``{pn}-drawing-contents-start`` and ``-end`` is what the
    family emitter wrote, and that is what must match locally and in CI.
    """
    start_token = f'id="{part_number}-drawing-contents-start"'
    end_token = f'id="{part_number}-drawing-contents-end"'
    start_at = svg_text.find(start_token)
    end_at = svg_text.find(end_token)
    if start_at < 0 or end_at < 0 or end_at <= start_at:
        return None
    inner_start = svg_text.find(">", start_at)
    inner_end = svg_text.rfind("<", 0, end_at)
    if inner_start < 0 or inner_end < 0:
        return None
    return svg_text[inner_start + 1 : inner_end].strip().replace("\r\n", "\n")


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def catalog_csv_expected(family: Family, module):
    if family.name == "M22759":
        rows = [
            module.csv_row(cfg) for cfg in module.M22759.iter_part_configurations()
        ]
        rows.sort(key=lambda row: row["part_number"])
        return module.CSV_COLUMNS, rows
    if family.name == "M27500":
        rows = [
            module.csv_row(cfg) for cfg in module.iter_cable_configurations()
        ]
        rows.sort(key=lambda row: row["part_number"])
        return module.CSV_COLUMNS, rows
    if family.name == "dsub":
        rows = [module.catalog_row(cfg) for cfg in module.iter_part_configurations()]
        rows.sort(key=lambda row: (int(row["slash_sheet"]), int(row["dash"]), row["finish"]))
        return list(module.CATALOG_COLUMNS), rows
    if family.name == "thermocouple":
        rows = [module.catalog_row(cfg) for cfg in module.iter_part_configurations()]
        return list(module.CATALOG_COLUMNS), rows
    return None, None


def stringify_csv_row(row: dict, columns) -> dict[str, str]:
    return {
        column: "" if row.get(column) is None else str(row[column]) for column in columns
    }


def load_csv_rows(path: Path, columns) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [stringify_csv_row(row, columns) for row in reader]


def on_disk_part_numbers(family: Family) -> set[str]:
    found = set()
    if not family.family_dir.is_dir():
        return found
    for entry in family.family_dir.iterdir():
        if not entry.is_dir() or entry.name in SKIP_DIR_NAMES:
            continue
        if family.pn_prefix and not entry.name.startswith(family.pn_prefix):
            continue
        history = entry / f"{entry.name}-revision_history.tsv"
        if history.is_file() or any(entry.glob(f"{entry.name}-rev*")):
            found.add(entry.name)
    return found


def revision_of(module) -> str:
    return str(getattr(module, "REVISION", "1"))


def required_paths(family: Family, part_number: str, revision: str) -> list[Path]:
    part_dir = family.family_dir / part_number
    rev_dir = part_dir / f"{part_number}-rev{revision}"
    paths = [
        part_dir / f"{part_number}-revision_history.tsv",
        rev_dir / f"{part_number}-rev{revision}-attributes.json",
    ]
    if family.kind == "part":
        paths.extend(
            [
                rev_dir / f"{part_number}-rev{revision}-drawing.svg",
                rev_dir / f"{part_number}-rev{revision}-model.step",
            ]
        )
    else:
        paths.append(rev_dir / f"{part_number}-rev{revision}-conductor_list.tsv")
    return paths


def _print_names(label: str, names: list[str], limit: int = 20) -> None:
    print(f"  {label}: {len(names)}")
    for name in names[:limit]:
        print(f"    {name}")
    if len(names) > limit:
        print(f"    ... and {len(names) - limit} more")


def cmd_list() -> int:
    print(f"{'family':<16} {'kind':<8} {'script'}")
    for family in FAMILIES:
        rel = family.script_path.relative_to(REPO_ROOT)
        print(f"{family.name:<16} {family.kind:<8} {rel}")
    return 0


def cmd_dry_run(families: list[Family]) -> int:
    grand_total = 0
    print(f"{'family':<16} {'kind':<8} {'skus'}")
    for family in families:
        module = import_generator(family)
        count = len(part_numbers_from_catalog(family, module))
        grand_total += count
        print(f"{family.name:<16} {family.kind:<8} {count}")
    print(f"{'total':<16} {'':<8} {grand_total}")
    return 0


def cmd_check(families: list[Family]) -> int:
    """Recompute generator artifacts and require the committed library to match.

    Same code path locally and in CI: no writes, no clock, no OpenCascade.
    A stale attributes.json or drawing envelope fails here in both places.
    """
    failed = False
    grand_expected = 0
    grand_on_disk = 0
    print(f"{'family':<16} {'expected':>8} {'on disk':>8} {'status'}")
    for family in families:
        module = import_generator(family)
        catalog = list(iter_catalog(family, module))
        expected = {part_number for part_number, _cfg in catalog}
        on_disk = on_disk_part_numbers(family)
        revision = revision_of(module)
        missing = sorted(expected - on_disk)
        extra = sorted(on_disk - expected)
        incomplete = []
        stale_attributes = []
        stale_svg = []
        for part_number, cfg in catalog:
            if part_number not in on_disk:
                continue
            paths = required_paths(family, part_number, revision)
            absent = [
                path.relative_to(REPO_ROOT).as_posix()
                for path in paths
                if not path.is_file()
            ]
            if absent:
                incomplete.append((part_number, absent))
                continue
            rev_dir = family.family_dir / part_number / f"{part_number}-rev{revision}"
            attributes_path = rev_dir / f"{part_number}-rev{revision}-attributes.json"
            generated_attributes = expected_attributes(family, module, cfg)
            if load_json(attributes_path) != generated_attributes:
                stale_attributes.append(part_number)
            if family.kind == "part":
                svg_path = rev_dir / f"{part_number}-rev{revision}-drawing.svg"
                generated_svg = expected_svg(
                    family, module, part_number, cfg, generated_attributes
                )
                disk_svg = svg_path.read_text(encoding="utf-8")
                generated_envelope = svg_envelope(generated_svg or "", part_number)
                disk_envelope = svg_envelope(disk_svg, part_number)
                if generated_envelope is None or disk_envelope is None:
                    stale_svg.append(part_number)
                elif generated_envelope != disk_envelope:
                    stale_svg.append(part_number)

        csv_error = None
        if family.catalog_csv:
            csv_path = family.family_dir / family.catalog_csv
            columns, generated_rows = catalog_csv_expected(family, module)
            if not csv_path.is_file():
                csv_error = f"missing {csv_path.relative_to(REPO_ROOT)}"
            elif generated_rows is not None:
                expected_rows = [
                    stringify_csv_row(row, columns) for row in generated_rows
                ]
                if load_csv_rows(csv_path, columns) != expected_rows:
                    csv_error = f"{csv_path.relative_to(REPO_ROOT)} does not match the generator"

        grand_expected += len(expected)
        grand_on_disk += len(on_disk)
        ok = (
            not missing
            and not extra
            and not incomplete
            and not stale_attributes
            and not stale_svg
            and csv_error is None
        )
        status = "ok" if ok else "FAIL"
        print(f"{family.name:<16} {len(expected):>8} {len(on_disk):>8} {status}")
        if missing:
            failed = True
            _print_names("missing folders", missing)
        if extra:
            failed = True
            _print_names("extra folders", extra)
        if incomplete:
            failed = True
            print(f"  incomplete SKUs: {len(incomplete)}")
            for part_number, absent in incomplete[:20]:
                print(f"    {part_number}")
                for path in absent:
                    print(f"      missing {path}")
            if len(incomplete) > 20:
                print(f"    ... and {len(incomplete) - 20} more")
        if stale_attributes:
            failed = True
            _print_names("attributes.json stale vs generator", stale_attributes)
        if stale_svg:
            failed = True
            _print_names("drawing.svg envelope stale vs generator", stale_svg)
        if csv_error:
            failed = True
            print(f"  {csv_error}")

    print(f"{'total':<16} {grand_expected:>8} {grand_on_disk:>8}")
    if failed:
        print(
            "\nCommitted files do not match the Python generators. "
            "This is the same check CI runs. "
            "Run `python generate.py` (or `--family …`) and commit the SKUs."
        )
        return 1
    print("\nEvery committed SKU agrees with its Python generator.")
    return 0


def flags_for_family(family: Family, args: argparse.Namespace) -> list[str]:
    flags: list[str] = []
    if args.dry_run and family.accepts("--dry-run"):
        flags.append("--dry-run")
    if args.csv_only and family.accepts("--csv-only"):
        flags.append("--csv-only")
    if args.svg_only and family.accepts("--svg-only"):
        flags.append("--svg-only")
    if args.cli and family.accepts("--cli"):
        flags.append("--cli")
    if args.step_only:
        if family.accepts("--step-only"):
            flags.append("--step-only")
        elif family.kind == "cable" and family.accepts("--no-build"):
            flags.append("--no-build")
    if args.no_build and family.accepts("--no-build"):
        if "--no-build" not in flags:
            flags.append("--no-build")
    flags.extend(args.passthrough)
    return flags


def cmd_generate(families: list[Family], args: argparse.Namespace) -> int:
    failures = []
    for family in families:
        flags = flags_for_family(family, args)
        command = [sys.executable, str(family.script_path), *flags]
        rel = family.script_path.relative_to(REPO_ROOT)
        print(f"\n=== {family.name}: {' '.join(command[1:])} ===", flush=True)
        result = subprocess.run(command, cwd=family.family_dir)
        if result.returncode != 0:
            failures.append((family.name, result.returncode, rel))
            if args.keep_going:
                print(f"{family.name} failed with exit {result.returncode}", flush=True)
                continue
            return result.returncode
    if failures:
        print("\nFailed families:")
        for name, code, rel in failures:
            print(f"  {name} ({rel}) exited {code}")
        return 1
    print("\nFinished generating selected families.")
    return 0


def git_changed_paths(base: str) -> list[str]:
    commands = (
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        ["git", "diff", "--name-only"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    paths: set[str] = set()
    for command in commands:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            continue
        paths.update(line.strip() for line in result.stdout.splitlines() if line.strip())
    return sorted(paths)


def families_touched_by(paths: list[str]) -> list[Family]:
    touched = []
    for family in FAMILIES:
        prefix = family.directory.rstrip("/") + "/"
        script_rel = family.script_path.relative_to(REPO_ROOT).as_posix()
        if any(
            path == script_rel
            or path.startswith(prefix)
            and Path(path).suffix == ".py"
            for path in paths
        ):
            touched.append(family)
    if any(path in {"generate.py", ".github/workflows/ci.yml"} for path in paths):
        return list(FAMILIES)
    return touched


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run or check every part-family generator in this library."
    )
    parser.add_argument(
        "families",
        nargs="*",
        help="Family names to run (default: all). Aliases: dsub, microd, m27500, …",
    )
    parser.add_argument(
        "--family",
        nargs="+",
        dest="family_opt",
        metavar="NAME",
        help="Same as positional family names",
    )
    parser.add_argument("--list", action="store_true", help="Print families and exit")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count legal SKUs per family without writing files",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Recompute generator artifacts and fail unless the committed "
            "library matches. Same result locally and in CI."
        ),
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Limit to families whose Python changed versus --base",
    )
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Git ref for --changed (default: origin/main)",
    )
    parser.add_argument(
        "--step-only",
        action="store_true",
        help="Parts: envelopes only. Cables: --no-build.",
    )
    parser.add_argument(
        "--svg-only",
        action="store_true",
        help="Forward --svg-only to families that support it",
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Forward --no-build to cable families",
    )
    parser.add_argument(
        "--csv-only",
        action="store_true",
        help="Rewrite family catalog CSVs only",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Forward --cli to families that build via `harnice -b`",
    )
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="Do not stop at the first family that fails",
    )
    parser.add_argument(
        "passthrough",
        nargs=argparse.REMAINDER,
        help="Extra flags after -- are forwarded to each selected emitter",
    )
    args = parser.parse_args(argv)
    if args.passthrough and args.passthrough[0] == "--":
        args.passthrough = args.passthrough[1:]
    return args


def selected_families(args: argparse.Namespace) -> list[Family]:
    names = list(args.families)
    if args.family_opt:
        names.extend(args.family_opt)
    if names:
        # Preserve request order, drop duplicates.
        seen = set()
        families = []
        for name in names:
            family = resolve_family(name)
            if family.name not in seen:
                families.append(family)
                seen.add(family.name)
    else:
        families = list(FAMILIES)

    if args.changed:
        paths = git_changed_paths(args.base)
        touched = families_touched_by(paths)
        touched_names = {family.name for family in touched}
        families = [family for family in families if family.name in touched_names]
        if not families:
            print("No part-family Python changed versus", args.base)
    return families


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.list:
        return cmd_list()
    families = selected_families(args)
    if not families:
        return 0
    if args.check:
        return cmd_check(families)
    if args.dry_run and not (
        args.step_only or args.csv_only or args.no_build or args.svg_only
    ):
        return cmd_dry_run(families)
    return cmd_generate(families, args)


if __name__ == "__main__":
    os.chdir(REPO_ROOT)
    raise SystemExit(main())
