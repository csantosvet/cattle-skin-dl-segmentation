"""Consolidate per-structure CSV exports from Dragonfly into a master measurements CSV.

Reads per-sample Hair, Sweat Gland, and Blood Vessel scalar-value exports produced
by Dragonfly's Multi-ROI "Compute scalar values" step, computes summary statistics
for each structure, and writes them into additional columns of a master measurements
CSV (one row per sample).

Input layout
------------
The --results-dir must contain three subfolders with one CSV per sample:

    <results-dir>/
        Hair/<SampleID>_hair.csv
        SweatGlands/<SampleID>_sg.csv
        BloodVessels/<SampleID>_bv.csv

Each CSV is the Dragonfly "Export scalar values" output (semicolon-delimited).

The --master-csv must already exist and have at minimum a column named Sample_ID
(customizable via --sample-id-column). A backup copy (<name>.csv.bak) is written
before the master file is overwritten.

Column mapping (master CSV <- per-sample CSV)
---------------------------------------------
    Hair_Count               <- row count of hair CSV
    Hair_Individual_Diameter <- mean 2D Maximum Feret Diameter over nonzero values (mm)
    Hair_Min_Diameter        <- min  2D Maximum Feret Diameter (nonzero only, mm)
    Hair_Max_Diameter        <- max  2D Maximum Feret Diameter (nonzero only, mm)
    Hair_Total_Diameter      <- sum of 2D Maximum Feret Diameters (nonzero, mm)
    Hair_SD_Diameter         <- standard deviation of 2D Max Feret (nonzero only, mm)
    Hair_Total_Volume        <- sum of all hair component volumes (mm3)
    Hair_Density_per_mm2     <- Hair_Count / pi  (assuming a 1-mm-radius biopsy cylinder)

    SW_Count                 <- row count of SG CSV
    SG_Individual_Diameter   <- mean Equivalent Spherical Diameter (mm)
    SG_Min_Diameter          <- min  Equivalent Spherical Diameter (mm)
    SG_Max_Diameter          <- max  Equivalent Spherical Diameter (mm)
    SG_Total_Diameter        <- sum of Equivalent Spherical Diameters (mm)
    SG_SD_Diameter           <- standard deviation of Equivalent Spherical Diameter (mm)
    SG_Total_Volume          <- sum of all sweat gland component volumes (mm3)
    SG_Density_per_mm2       <- SW_Count / pi  (same cylinder assumption)
    SG_Depth                 <- mean of per-gland "Min Intensity" column, interpreted as
                                the shortest distance to the epidermis in mm. Populated
                                only when the SG CSV is exported against an epidermis
                                distance map (see Protocol 02 Part C).

    BV_Diameter              <- mean Equivalent Spherical Diameter across BV components (mm)
    BV_Count                 <- number of BV components
    BV_Total_Volume          <- sum of all BV component volumes (mm3)

Usage
-----
    python populate_master_csv.py \\
        --results-dir /path/to/03_RESULTS \\
        --master-csv /path/to/master_measurements.csv

Notes
-----
- The cylinder-area assumption (pi mm^2) matches the 2-mm-diameter biopsy mask
  defined in Protocol 02. If your mask differs, override the density columns
  downstream.
- Hair diameter statistics are computed over nonzero 2D Maximum Feret values only,
  because single-slice hair cross-sections can produce a Feret of 0 mm and would
  otherwise bias the mean. See Protocol 02 for the rationale.
"""
from __future__ import annotations

import argparse
import csv
import math
import shutil
import statistics
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Consolidate per-structure Dragonfly CSV exports into a master measurements CSV.",
    )
    p.add_argument(
        "--results-dir",
        type=Path,
        required=True,
        help="Directory containing Hair/, SweatGlands/, and BloodVessels/ subfolders.",
    )
    p.add_argument(
        "--master-csv",
        type=Path,
        required=True,
        help="Path to the master measurements CSV to update (must already exist).",
    )
    p.add_argument(
        "--sample-id-column",
        default="Sample_ID",
        help="Name of the sample-id column in the master CSV (default: Sample_ID).",
    )
    return p.parse_args()


def _read_structure_csv(csv_path: Path) -> list[dict[str, str]] | None:
    if not csv_path.exists():
        return None
    with csv_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    return rows or None


def read_hair_stats(hair_dir: Path, sample_id: str) -> dict[str, float] | None:
    rows = _read_structure_csv(hair_dir / f"{sample_id}_hair.csv")
    if rows is None:
        return None
    feret = [float(r["2D Maximum Feret Diameter (mm)"]) for r in rows]
    feret_pos = [x for x in feret if x > 0]
    volumes = [float(r["Volume (mm\u00b3)"]) for r in rows]
    count = len(rows)
    return {
        "Hair_Count": count,
        "Hair_Individual_Diameter": sum(feret_pos) / len(feret_pos) if feret_pos else 0.0,
        "Hair_Min_Diameter": min(feret_pos) if feret_pos else 0.0,
        "Hair_Max_Diameter": max(feret_pos) if feret_pos else 0.0,
        "Hair_Total_Diameter": sum(feret_pos),
        "Hair_SD_Diameter": statistics.stdev(feret_pos) if len(feret_pos) > 1 else 0.0,
        "Hair_Total_Volume": sum(volumes),
        "Hair_Density_per_mm2": count / math.pi,
    }


def read_sg_stats(sg_dir: Path, sample_id: str) -> dict[str, float] | None:
    rows = _read_structure_csv(sg_dir / f"{sample_id}_sg.csv")
    if rows is None:
        return None
    eq_sph = [float(r["Equivalent Spherical Diameter (mm)"]) for r in rows]
    volumes = [float(r["Volume (mm\u00b3)"]) for r in rows]
    count = len(rows)
    result: dict[str, float] = {
        "SW_Count": count,
        "SG_Individual_Diameter": sum(eq_sph) / len(eq_sph),
        "SG_Min_Diameter": min(eq_sph),
        "SG_Max_Diameter": max(eq_sph),
        "SG_Total_Diameter": sum(eq_sph),
        "SG_SD_Diameter": statistics.stdev(eq_sph) if len(eq_sph) > 1 else 0.0,
        "SG_Total_Volume": sum(volumes),
        "SG_Density_per_mm2": count / math.pi,
    }
    # Populated only if the SG CSV was exported against an epidermis distance map.
    # Dragonfly's "Basic Measurements with Dataset" emits a "Min Intensity" column
    # whose values are the minimum distance (mm) from each gland to the epidermis.
    depth_col = "Min Intensity"
    if depth_col in rows[0]:
        depths = [float(r[depth_col]) for r in rows]
        result["SG_Depth"] = sum(depths) / len(depths)
    return result


def read_bv_stats(bv_dir: Path, sample_id: str) -> dict[str, float] | None:
    rows = _read_structure_csv(bv_dir / f"{sample_id}_bv.csv")
    if rows is None:
        return None
    volumes = [float(r["Volume (mm\u00b3)"]) for r in rows]
    eq_sph = [float(r["Equivalent Spherical Diameter (mm)"]) for r in rows]
    return {
        "BV_Diameter": sum(eq_sph) / len(eq_sph),
        "BV_Count": len(rows),
        "BV_Total_Volume": sum(volumes),
    }


def main() -> int:
    args = parse_args()

    if not args.master_csv.exists():
        print(f"ERROR: master CSV not found at {args.master_csv}", file=sys.stderr)
        return 1
    if not args.results_dir.exists():
        print(f"ERROR: results dir not found at {args.results_dir}", file=sys.stderr)
        return 1

    hair_dir = args.results_dir / "Hair"
    sg_dir = args.results_dir / "SweatGlands"
    bv_dir = args.results_dir / "BloodVessels"

    backup = args.master_csv.with_suffix(args.master_csv.suffix + ".bak")
    shutil.copy2(args.master_csv, backup)
    print(f"Backup created: {backup}")

    with args.master_csv.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if args.sample_id_column not in fieldnames:
        print(
            f"ERROR: column {args.sample_id_column!r} not found in master CSV. "
            f"Available columns: {fieldnames}",
            file=sys.stderr,
        )
        return 1

    new_columns = [
        "Hair_Count", "Hair_Individual_Diameter", "Hair_Min_Diameter",
        "Hair_Max_Diameter", "Hair_Total_Diameter", "Hair_SD_Diameter",
        "Hair_Total_Volume", "Hair_Density_per_mm2",
        "SW_Count", "SG_Individual_Diameter", "SG_Min_Diameter",
        "SG_Max_Diameter", "SG_Total_Diameter", "SG_SD_Diameter",
        "SG_Total_Volume", "SG_Density_per_mm2", "SG_Depth",
        "BV_Diameter", "BV_Count", "BV_Total_Volume",
    ]
    for col in new_columns:
        if col not in fieldnames:
            fieldnames.append(col)

    updated = 0
    for row in rows:
        sample_id = row[args.sample_id_column].strip()
        if not sample_id:
            continue

        hair = read_hair_stats(hair_dir, sample_id)
        if hair:
            for key, val in hair.items():
                row[key] = str(val)

        sg = read_sg_stats(sg_dir, sample_id)
        if sg:
            for key, val in sg.items():
                row[key] = str(val)

        bv = read_bv_stats(bv_dir, sample_id)
        if bv:
            for key, val in bv.items():
                row[key] = str(val)

        if hair or sg or bv:
            updated += 1
            structures: list[str] = []
            if hair:
                structures.append(f"Hair({hair['Hair_Count']:.0f})")
            if sg:
                structures.append(f"SG({sg['SW_Count']:.0f})")
            if bv:
                structures.append(f"BV({bv['BV_Count']:.0f})")
            print(f"  {sample_id}: {', '.join(structures)}")

    for row in rows:
        row.pop(None, None)

    with args.master_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. Updated {updated} samples in {args.master_csv.name}")
    print(f"Backup at: {backup.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
