"""Audit per-structure CSV exports for misplaced files.

Scans the three results folders (BloodVessels, Hair, SweatGlands) under a
--results-dir and flags any CSV whose content is inconsistent with the folder it
lives in. This catches manual-naming mistakes (e.g. a Hair export saved into
SweatGlands, or an SG file saved as _bv.csv).

Detection strategy
------------------
Two independent checks are applied to every CSV:

1. **Row-count heuristic** — robust, does not depend on your cohort:
   - BV: typically 1–5 rows per sample. Anything beyond --bv-max-rows (default 8)
     in the BV folder is almost certainly a Hair or SG file mis-saved as BV.
   - Hair/SG: typically tens to low-hundreds of rows per sample. Anything below
     --structure-min-rows (default 20) in Hair/ or SG/ is almost certainly a BV
     file mis-saved there.

2. **Distribution heuristic** (optional, requires cohort-specific calibration):
   Mean Equivalent Spherical Diameter and mean sphericity thresholds flag files
   whose content distribution looks inconsistent with the folder. Default
   threshold values are illustrative; **calibrate them on your own cohort** before
   relying on them. Disable with --skip-distribution-check.

Cross-folder checks
-------------------
Additionally flags:
- Identical file contents in two different folders (same MD5), which indicates a
  copy/paste mistake rather than a naming mistake.
- Samples whose Hair and SG CSVs look near-identical (same row count and mean
  EqSphD), which can indicate a duplicated export.

Usage
-----
    python audit_csv_placement.py --results-dir /path/to/03_RESULTS

The --results-dir must contain Hair/, SweatGlands/, and BloodVessels/ subfolders
with semicolon-delimited Dragonfly "scalar values" CSVs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
from typing import Literal

FolderKind = Literal["BV", "HAIR", "SG"]

# Dragonfly scalar-values export column indices (0-based, semicolon-delimited).
COL_FERET_MAX = 4
COL_FERET_MIN = 5
COL_VOLUME = 6
COL_EQSPHD = 7
COL_SPHERICITY = 9


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Audit per-structure Dragonfly CSV exports for misplaced files.",
    )
    p.add_argument("--results-dir", type=Path, required=True,
                   help="Directory containing Hair/, SweatGlands/, BloodVessels/ subfolders.")
    p.add_argument("--bv-max-rows", type=int, default=8,
                   help="Max row count allowed in BV folder (default: 8).")
    p.add_argument("--structure-min-rows", type=int, default=20,
                   help="Min row count expected in Hair/SG folders (default: 20).")
    p.add_argument("--hair-max-mean-eqsphd", type=float, default=0.180,
                   help="Mean EqSphD (mm) above which a Hair-folder file is flagged as "
                        "probable SG. Default (0.180 mm) is illustrative; calibrate on your cohort.")
    p.add_argument("--hair-min-mean-sphericity", type=float, default=0.45,
                   help="Mean sphericity below which a Hair-folder file is flagged as "
                        "probable SG. Default (0.45) is illustrative; calibrate on your cohort.")
    p.add_argument("--skip-distribution-check", action="store_true",
                   help="Skip the distribution heuristic entirely and rely on row counts only.")
    return p.parse_args()


@dataclass
class CsvStats:
    path: Path
    n_rows: int
    mean_eqsphd: float | None
    median_eqsphd: float | None
    max_eqsphd: float | None
    feret_zero_frac: float | None
    mean_sphericity: float | None
    content_hash: str = ""
    parse_error: str | None = None


def _safe_float(s: str) -> float | None:
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def read_stats(csv_path: Path) -> CsvStats:
    try:
        raw = csv_path.read_bytes()
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f, delimiter=";"))
    except (OSError, UnicodeDecodeError) as exc:
        return CsvStats(csv_path, 0, None, None, None, None, None, "", str(exc))

    data = [r for r in rows[1:] if any(c.strip() for c in r)]
    n = len(data)
    content_hash = hashlib.md5(raw).hexdigest()

    eqsphd: list[float] = []
    feret_min: list[float] = []
    sphericity: list[float] = []

    for r in data:
        if len(r) <= COL_SPHERICITY:
            continue
        v = _safe_float(r[COL_EQSPHD])
        if v is not None:
            eqsphd.append(v)
        v = _safe_float(r[COL_FERET_MIN])
        if v is not None:
            feret_min.append(v)
        v = _safe_float(r[COL_SPHERICITY])
        if v is not None:
            sphericity.append(v)

    return CsvStats(
        path=csv_path,
        n_rows=n,
        mean_eqsphd=mean(eqsphd) if eqsphd else None,
        median_eqsphd=median(eqsphd) if eqsphd else None,
        max_eqsphd=max(eqsphd) if eqsphd else None,
        feret_zero_frac=(sum(1 for v in feret_min if v == 0) / len(feret_min))
        if feret_min
        else None,
        mean_sphericity=mean(sphericity) if sphericity else None,
        content_hash=content_hash,
    )


SAMPLE_ID_RE = re.compile(r"^([A-Za-z0-9]+-[A-Za-z0-9]+)")


def sample_id_of(path: Path) -> str | None:
    m = SAMPLE_ID_RE.match(path.name)
    return m.group(1) if m else None


def audit_bv(stats: CsvStats, args: argparse.Namespace) -> list[str]:
    reasons: list[str] = []
    if stats.n_rows > args.bv_max_rows:
        reasons.append(
            f"rows={stats.n_rows} exceeds BV max ({args.bv_max_rows}) — "
            "likely a Hair or SG file mis-saved as BV"
        )
    return reasons


def audit_hair(stats: CsvStats, args: argparse.Namespace) -> list[str]:
    reasons: list[str] = []
    if stats.n_rows < args.structure_min_rows:
        reasons.append(
            f"rows={stats.n_rows} below Hair min ({args.structure_min_rows}) — "
            "likely a BV file mis-saved as Hair"
        )
        return reasons
    if args.skip_distribution_check:
        return reasons
    eq = stats.mean_eqsphd
    sph = stats.mean_sphericity
    if eq is not None and eq > args.hair_max_mean_eqsphd:
        reasons.append(
            f"mean EqSphD = {eq:.3f} mm exceeds --hair-max-mean-eqsphd "
            f"({args.hair_max_mean_eqsphd:.3f}) — looks like SG"
        )
    if sph is not None and sph < args.hair_min_mean_sphericity:
        reasons.append(
            f"mean sphericity = {sph:.3f} below --hair-min-mean-sphericity "
            f"({args.hair_min_mean_sphericity:.3f}) — looks like SG"
        )
    return reasons


def audit_sg(stats: CsvStats, args: argparse.Namespace) -> list[str]:
    reasons: list[str] = []
    if stats.n_rows < args.structure_min_rows:
        reasons.append(
            f"rows={stats.n_rows} below SG min ({args.structure_min_rows}) — "
            "likely a BV file mis-saved as SG"
        )
    return reasons


def fmt(v: float | None, digits: int = 3) -> str:
    if v is None:
        return "  n/a"
    return f"{v:.{digits}f}"


def check_cross_folder_duplicates(folders: dict[FolderKind, Path]) -> None:
    """Flag identical file contents across folders (copy-paste mistakes) and
    samples whose Hair/SG files look weirdly similar to each other."""
    print("\n" + "=" * 100)
    print("CROSS-FOLDER CHECKS")
    print("=" * 100)

    hash_map: dict[str, list[Path]] = {}
    per_sample: dict[str, dict[str, list[CsvStats]]] = {}

    for kind, folder in folders.items():
        for f in sorted(folder.glob("*.csv")):
            s = read_stats(f)
            hash_map.setdefault(s.content_hash, []).append(f)
            sid = sample_id_of(f)
            if sid is not None:
                per_sample.setdefault(sid, {}).setdefault(kind, []).append(s)

    dup_cross = [
        paths
        for paths in hash_map.values()
        if len(paths) > 1 and len({p.parent.name for p in paths}) > 1
    ]
    if dup_cross:
        print("\n!! Identical file contents found in MULTIPLE folders (copy/paste mistakes):")
        for paths in dup_cross:
            for p in paths:
                print(f"    {p.parent.name}/{p.name}")
            print("    " + "-" * 60)
    else:
        print("\n  OK - no identical files spanning folders")

    print("\nPer-sample cross-check (Hair vs SG):")
    suspicious_pairs: list[tuple[str, CsvStats, CsvStats]] = []
    for sid, by_kind in sorted(per_sample.items()):
        hair_files = by_kind.get("HAIR", [])
        sg_files = by_kind.get("SG", [])
        if not hair_files or not sg_files:
            continue
        h = hair_files[0]
        s = sg_files[0]
        if (
            h.n_rows
            and s.n_rows
            and h.mean_eqsphd is not None
            and s.mean_eqsphd is not None
        ):
            eq_diff = abs(h.mean_eqsphd - s.mean_eqsphd)
            rows_diff = abs(h.n_rows - s.n_rows)
            if eq_diff < 0.003 and rows_diff < 5:
                suspicious_pairs.append((sid, h, s))

    if suspicious_pairs:
        print("  !! Hair and SG files for same sample look near-identical:")
        for sid, h, s in suspicious_pairs:
            print(
                f"    {sid}  Hair rows={h.n_rows} meanEq={h.mean_eqsphd:.4f}  "
                f"SG rows={s.n_rows} meanEq={s.mean_eqsphd:.4f}"
            )
    else:
        print("  OK - Hair and SG files differ as expected for every sample")


def main() -> int:
    args = parse_args()

    folders: dict[FolderKind, Path] = {
        "BV": args.results_dir / "BloodVessels",
        "HAIR": args.results_dir / "Hair",
        "SG": args.results_dir / "SweatGlands",
    }
    for kind, folder in folders.items():
        if not folder.is_dir():
            print(f"ERROR: expected folder not found: {folder}", file=sys.stderr)
            return 1

    auditors = {"BV": audit_bv, "HAIR": audit_hair, "SG": audit_sg}

    print("=" * 100)
    print("CSV PLACEMENT AUDIT")
    print(f"Root: {args.results_dir}")
    print("=" * 100)

    total_flagged = 0
    grand_summary: list[tuple[str, str, str]] = []

    for kind, folder in folders.items():
        files = sorted(folder.glob("*.csv"))
        print(f"\n### {kind} folder: {folder.name} ({len(files)} files)")
        auditor = auditors[kind]

        all_stats = [read_stats(f) for f in files]
        counts = [s.n_rows for s in all_stats]
        if counts:
            print(
                f"  row counts: min={min(counts)} median={median(counts):.0f} "
                f"mean={mean(counts):.1f} max={max(counts)}"
            )

        flagged = [(s, auditor(s, args)) for s in all_stats]
        flagged = [(s, r) for s, r in flagged if r]

        if not flagged:
            print("  OK - no suspicious files")
            continue

        total_flagged += len(flagged)
        print(f"  !! {len(flagged)} suspicious file(s):")
        header = (
            f"    {'file':<45} {'rows':>5} {'meanEq':>7} {'maxEq':>7} "
            f"{'Fer=0%':>7} {'meanSph':>8}  reason"
        )
        print(header)
        print("    " + "-" * (len(header) - 4))
        for s, reasons in flagged:
            fz_pct = (
                f"{s.feret_zero_frac * 100:5.1f}"
                if s.feret_zero_frac is not None
                else "  n/a"
            )
            reason_text = " | ".join(reasons)
            print(
                f"    {s.path.name:<45} {s.n_rows:>5} {fmt(s.mean_eqsphd):>7} "
                f"{fmt(s.max_eqsphd):>7} {fz_pct:>7} {fmt(s.mean_sphericity):>8}  {reason_text}"
            )
            grand_summary.append((kind, s.path.name, reason_text))

    print("\n" + "=" * 100)
    print(f"TOTAL FLAGGED (content heuristics): {total_flagged}")
    if grand_summary:
        print("-" * 100)
        print("Summary (folder -> file -> reason)")
        for k, n, r in grand_summary:
            print(f"  [{k}] {n}  ::  {r}")
    print("=" * 100)

    check_cross_folder_duplicates(folders)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
