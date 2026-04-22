# Protocol 04: Data Management and Scripts

## Purpose

This document describes the data-management workflow that ties the segmentation outputs together: how per-structure CSV exports from Dragonfly flow into a consolidated "master measurements" spreadsheet, how that spreadsheet is organized, and how the included analysis scripts are used. Follow this protocol each time you finish segmenting a new sample.

---

## Part A: Master Measurements CSV

### A.1 Overview

The master measurements CSV is the single source of truth for per-sample results. It contains **one row per sample** (or per animal, if you track one biopsy per animal) with three groups of columns:

- **Sample metadata** (filled by the user before running any script): at minimum a `Sample_ID` column matching the per-structure CSV file names produced by Dragonfly. Additional metadata columns (e.g. breed, age, treatment group, external animal identifier) are freely added by the user and preserved by the scripts.
- **External phenotype columns** (optional, filled by the user): any animal- or sample-level traits derived from external analyses outside this pipeline (body temperature, thermal tolerance, behavioral scores, etc.).
- **Measurement columns** (filled automatically by `populate_master_csv.py`): hair counts and diameters, sweat gland counts and diameters, blood vessel diameter and counts, and optional sweat gland depth.

The only column required by `populate_master_csv.py` is `Sample_ID` (override with the `--sample-id-column` flag if your spreadsheet uses a different name). Every other column is user-defined and left untouched.

### A.2 Recommended Metadata Columns

Choose whichever columns are useful to your study. The table below shows a minimal metadata schema that works well with the analysis downstream:

| Column          | Description                                           | Example      |
| --------------- | ----------------------------------------------------- | ------------ |
| Sample_ID       | Sample identifier, must match the per-structure CSV file names | `S01`         |
| External_Animal_ID | Optional link back to your animal records         | (user-defined) |
| Set             | Collection set or batch number                        | 1            |
| Year            | Collection year                                       | 2023         |
| Herd / Group    | Herd, breed, or treatment designation                 | `group_A`    |
| Trait_pct       | Any continuous animal-level trait, if applicable      | 14.5         |

The specific set of metadata columns is entirely up to the user; the pipeline neither requires nor interprets any of them.

### A.3 Measurement Columns

These columns are populated automatically by `scripts/populate_master_csv.py` from the per-sample CSVs exported from Dragonfly.

| Master CSV column        | Source metric                                          | Units    | Notes                               |
| ------------------------ | ------------------------------------------------------ | -------- | ----------------------------------- |
| Hair_Count               | Row count of `<SampleID>_hair.csv`                     | count    |                                      |
| Hair_Total_Diameter      | Sum of 2D Maximum Feret Diameters (nonzero only)       | mm       |                                      |
| Hair_Individual_Diameter | Mean 2D Maximum Feret Diameter (nonzero only)          | mm       | Primary hair diameter metric         |
| Hair_Min_Diameter        | Minimum 2D Maximum Feret Diameter (nonzero only)       | mm       |                                      |
| Hair_Max_Diameter        | Maximum 2D Maximum Feret Diameter (nonzero only)       | mm       |                                      |
| Hair_SD_Diameter         | Std. dev. of 2D Maximum Feret Diameter (nonzero only)  | mm       | Within-sample variability            |
| Hair_Total_Volume        | Sum of hair-component volumes                          | mm³      |                                      |
| Hair_Density_per_mm2     | Hair_Count / cross-sectional area                      | per mm²  | Cylinder-area assumption (π mm²)     |
| SW_Count                 | Row count of `<SampleID>_sg.csv`                       | count    | Sweat glands                         |
| SG_Total_Diameter        | Sum of Equivalent Spherical Diameters                  | mm       |                                      |
| SG_Individual_Diameter   | Mean Equivalent Spherical Diameter                     | mm       | Primary SG size metric (3D)          |
| SG_Min_Diameter          | Minimum Equivalent Spherical Diameter                  | mm       |                                      |
| SG_Max_Diameter          | Maximum Equivalent Spherical Diameter                  | mm       |                                      |
| SG_SD_Diameter           | Std. dev. of Equivalent Spherical Diameter             | mm       |                                      |
| SG_Total_Volume          | Sum of sweat-gland-component volumes                   | mm³      |                                      |
| SG_Density_per_mm2       | SW_Count / cross-sectional area                        | per mm²  | Cylinder-area assumption (π mm²)     |
| SG_Depth                 | Mean per-gland "Min Intensity" from Distance Map       | mm       | Populated only if CSV includes the Distance Map column (see Protocol 02 Part E) |
| BV_Count                 | Row count of `<SampleID>_bv.csv`                       | count    | Blood vessels                        |
| BV_Diameter              | Mean Equivalent Spherical Diameter across BV components | mm      | Per-component, not per-network       |
| BV_Total_Volume          | Sum of blood-vessel-component volumes                  | mm³      |                                      |

The **cylinder-area assumption** (π mm²) assumes a 2 mm diameter biopsy mask, as documented in Protocol 02. If your mask differs, override the density columns downstream.

Hair diameter statistics are computed over **nonzero 2D Maximum Feret values only**, because single-slice hair cross-sections can produce a Feret of 0 mm and would otherwise bias the mean. See Protocol 02 Part B for the full rationale.

### A.4 Sample ID Convention

Per-sample CSVs are named by their sample identifier:

- `<SampleID>_hair.csv`
- `<SampleID>_sg.csv`
- `<SampleID>_bv.csv`

The string before the first underscore is treated as the sample identifier and must match an entry in the `Sample_ID` column of the master CSV. Choose whatever scheme works for your project (e.g. `S01`, `S01_A03`, `animal-091`); the scripts only require consistency between the master CSV column and the file names.

---

## Part B: Workflow — Updating the Master CSV

After completing segmentation of a new sample, follow these steps:

### B.1 Export Per-Structure CSVs from Dragonfly

1. **Hair**: right-click the Hair Multi-ROI → Measurements and Scalar Values → Export Scalar Values. Save to `<project_root>/03_RESULTS/Hair/<SampleID>_hair.csv`.
2. **Sweat Glands**: same process for the SG Multi-ROI. Save to `<project_root>/03_RESULTS/SweatGlands/<SampleID>_sg.csv`.
3. **Blood Vessels** (if present): same process for the BV Multi-ROI. Save to `<project_root>/03_RESULTS/BloodVessels/<SampleID>_bv.csv`. Skip if no BV was found.
4. Ensure the CSVs are semicolon-delimited (Dragonfly default) and contain all computed measurement columns.

### B.2 Run the Population Script

**When to run**: the script can be run after every sample or in batches. Both work correctly — the script is **idempotent**, so re-running on the same data produces the same result and will overwrite previous values when a segmentation is corrected.

| Approach                | When to use                                                                                       |
| ----------------------- | ------------------------------------------------------------------------------------------------- |
| Batch (recommended)     | Once per session or once per day, after finishing a group of samples. More efficient.             |
| Per-sample              | After each sample if you need immediate feedback (QC or troubleshooting).                         |
| Before analysis         | Always run before any statistical analysis to make sure the master CSV is current.                |

```
python scripts/populate_master_csv.py \
    --results-dir <project_root>/03_RESULTS \
    --master-csv <path-to-master-measurements.csv>
```

The script will:

- Create a backup (`<master-csv-name>.csv.bak`) before making changes.
- Scan the Hair, SweatGlands, and BloodVessels result folders for CSVs.
- Match each CSV to its `Sample_ID` row in the master CSV.
- Compute and fill the measurement columns listed in A.3.
- Print which samples were updated (with per-structure counts).

### B.3 Verify

After running, spot-check the results in Dragonfly and the master CSV:

- **Row counts** — do the Hair, SG, and BV counts in the master CSV match what Dragonfly reports in the Multi-ROI?
- **Diameter magnitudes** — are the mean hair Feret and mean SG Equivalent Spherical Diameter in the expected range for your tissue type?
- **Cross-folder consistency** — run `scripts/audit_csv_placement.py` (Part D.2) on the results directory to catch cases where a CSV was saved into the wrong folder.

---

## Part C: Per-Sample CSVs (Raw Component Data)

The per-sample CSVs exported from Dragonfly contain **one row per component** (per hair strand, per sweat gland, per blood-vessel component). These are the raw data files and should be preserved as-is.

### C.1 File Locations

| Structure    | Directory                                    | File name             |
| ------------ | -------------------------------------------- | --------------------- |
| Hair         | `<project_root>/03_RESULTS/Hair/`            | `<SampleID>_hair.csv` |
| Sweat Glands | `<project_root>/03_RESULTS/SweatGlands/`     | `<SampleID>_sg.csv`   |
| Blood Vessels| `<project_root>/03_RESULTS/BloodVessels/`    | `<SampleID>_bv.csv`   |

### C.2 CSV Format

- **Delimiter**: semicolon (`;`) — Dragonfly default.
- **Encoding**: UTF-8.

**Columns** (from Dragonfly "Scalar Values" export):

| Column                                  | Description                                            |
| --------------------------------------- | ------------------------------------------------------ |
| Time Step                               | Always 0 for single-time-point scans                   |
| Label Index                             | Component number (1, 2, 3, …)                          |
| Name (NA)                               | Empty for auto-detected components                     |
| 2D Area Equivalent Circle Diameter (mm) | Alternative diameter metric                            |
| 2D Maximum Feret Diameter (mm)          | Widest cross-sectional width — **primary for hair**    |
| 2D Minimum Feret Diameter (mm)          | Narrowest cross-sectional width                        |
| Volume (mm³)                            | 3D volume of the component                             |
| Equivalent Spherical Diameter (mm)      | Sphere-equivalent diameter — **primary for SG and BV** |
| Surface Area (voxel-wise) (mm²)         | Surface area of the component                          |
| Sphericity                              | Roundness (0–1, where 1 = perfect sphere)              |

---

## Part D: Scripts Reference

All analysis scripts in this repository are in `scripts/` (pipeline) and `conversion/` (format conversion). They are designed to be run from the command line with explicit `--flag` arguments — no hardcoded paths.

### D.1 Data consolidation

| Script                   | Purpose                                                                                          |
| ------------------------ | ------------------------------------------------------------------------------------------------ |
| `populate_master_csv.py` | Reads per-structure Dragonfly CSVs and fills the summary columns of the master measurements CSV. |

See `--help` on each script for the full argument list.

### D.2 Quality control

| Script                    | Purpose                                                                                              |
| ------------------------- | ---------------------------------------------------------------------------------------------------- |
| `audit_csv_placement.py`  | Scans the three results folders and flags CSVs whose content doesn't match the folder they sit in (e.g. a Hair file mis-saved as SG). Uses row-count heuristics and optional distribution-based cutoffs. |

### D.3 Preprocessing

| Script                | Purpose                                                                                                                       |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `normalize_volume.py` | Apply a linear intensity transform to a source TIFF volume so its tissue mean/std matches a reference volume's. Useful when intensity drift between scanning sessions causes DL-model out-of-distribution failures (see Protocol 03 Part E). |

### D.4 Bookkeeping (optional)

| Script                      | Purpose                                                                                                                          |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `rebuild_production_csv.py` | Parse a Markdown "production summary" table into two machine-readable CSVs (per-sample disposition + per-fallback failure mode). Useful if you track operator progress in a human-readable Markdown document and want a CSV copy for analysis. |

### D.5 TXM → TIFF conversion

Format-conversion utilities live in `conversion/` (see Protocol 01 for full usage).

| Script                    | Purpose                                                                                |
| ------------------------- | -------------------------------------------------------------------------------------- |
| `convert_txm_to_tiff.py`  | Convert a single Zeiss Xradia reconstructed volume (`.txm`) to an ImageJ-compatible multi-page TIFF. |
| `batch_convert_all.py`    | Safe, resumable batch converter over a directory tree of `.txm` reconstructions.       |

---

## Part E: Per-sample Progress Tracking (Optional)

A simple way to track per-sample progress outside the master CSV is a Markdown table with one row per sample:

| Sample | Group   | Structures completed | Time   | Notes             |
| ------ | ------- | -------------------- | ------ | ----------------- |
| S01    | group_A | Hair / SG / BV       | 12 min |                   |
| S02    | group_B | Hair / SG / BV       | 14 min | zero hair fusions |
| …      |         |                      |        |                   |

If you use this format and wrap it in a section headed `## Production Summary`, `scripts/rebuild_production_csv.py` can parse it into per-sample and per-failure CSVs for downstream analysis.

---

## References

- Protocol 01 — TXM to TIFF conversion
- Protocol 02 — Manual segmentation in Dragonfly
- Protocol 03 — AI Segmentation Wizard automation
