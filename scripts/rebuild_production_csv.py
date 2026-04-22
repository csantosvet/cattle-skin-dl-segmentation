"""Rebuild a per-sample production-summary CSV from a markdown summary table.

Parses a Markdown file that contains a `## Production Summary` section with a
table describing per-sample dispositions (DL-accepted, DL+cleanup, manual
fallback) and per-structure timing, and emits two CSVs:

- `<output>.csv`           — one row per sample with parsed disposition and timing
- `<failure-output>.csv`   — one row per (sample, fallback structure); dual-
                              fallback samples appear twice

This is useful when you track production progress in a human-readable Markdown
spreadsheet and want a machine-readable copy for analysis without duplicating
the source of truth.

Expected source structure
-------------------------
The source Markdown file must contain a section headed `## Production Summary`
followed by a Markdown table with at least these columns (column order is
irrelevant, but column names are matched literally):

    | Sample | Breed | Brahman % | Hair time | SG time | BV time | Total | Speedup vs manual | Notes |

Each disposition cell can contain free text; the parser recognizes these cues:
    - `manual re-seg`, `MANUAL ...`, `(manual)`   -> manual fallback
    - `DL + manual ...`, `DL + cleanup`           -> DL with cleanup
    - `training`                                   -> pre-production training
    - otherwise                                    -> DL accepted

Time cells may use any of: `14 min`, `~14 min`, `14-17 min`, `11:54`, `8 min 53 s`.

Usage
-----
    python rebuild_production_csv.py \\
        --source        production_summary.md \\
        --output        production_summary.csv \\
        --failure-output failure_modes.csv
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


CELL_BOLD = re.compile(r"\*\*(.*?)\*\*")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Parse a production-summary Markdown table into machine-readable CSVs.",
    )
    p.add_argument("--source", type=Path, required=True,
                   help="Path to the source Markdown file containing a ## Production Summary section.")
    p.add_argument("--output", type=Path, required=True,
                   help="Path to write the per-sample CSV.")
    p.add_argument("--failure-output", type=Path, required=True,
                   help="Path to write the per-(sample, fallback-structure) CSV.")
    return p.parse_args()


def strip_md(text: str) -> str:
    """Strip bold markers and collapse whitespace."""
    text = CELL_BOLD.sub(r"\1", text)
    return text.strip()


def parse_minutes(time_str: str) -> float | None:
    """Best-effort conversion of a free-text time cell to float minutes.

    Handles: '14 min', '11:54', '8:53', '8 min 53 s', '~17 min', '~14-17 min',
    '--' or '-' (returns None).
    """
    if not time_str:
        return None
    t = strip_md(time_str).strip().lower().replace("\u2014", "-").replace("\u2013", "-")
    if t in {"-", "--", "tbd", "n/a"}:
        return None
    m = re.fullmatch(r"~?\s*(\d+):(\d+)(?:\s*(?:min|s))?", t)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 60.0
    m = re.fullmatch(r"~?\s*(\d+)\s*min\s*(\d+)\s*s", t)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 60.0
    m = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*min", t)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2
    m = re.search(r"~?\s*(\d+(?:\.\d+)?)\s*min", t)
    if m:
        return float(m.group(1))
    return None


def classify_disposition(cell: str, structure: str) -> tuple[str, str]:
    """Return (disposition, failure_mode) for a hair/sg/bv cell.

    `structure` is one of {'hair', 'sg', 'bv'}. The disposition is one of:
      'DL'              - DL output adopted with at most routine cleanup
      'DL+cleanup'      - DL adopted but with substantive operator cleanup
      'manual'          - DL discarded, manual re-segmentation
      'manual_only'     - Always manual (used for BV)
      'manual_from_sg'  - BV traced opportunistically from the SG segmentation
      'none'            - No measurement (e.g. BV not segmentable)
      'training'        - Pre-production manual training row (excluded from tallies)
      'unknown'         - Cell could not be classified
    """
    if not cell or cell.strip() in {"-", "--", "\u2014", ""}:
        return ("unknown", "")
    raw = strip_md(cell).lower()
    if "training" in raw:
        return ("training", "")
    if structure == "bv":
        if "none" in raw or "no bv" in raw or "no usable bv" in raw or "biopsy damage" in raw:
            return ("none", "")
        if "from sg" in raw:
            return ("manual_from_sg", "")
        return ("manual_only", "")
    if re.search(r"\bmanual\s+re-?seg\b", raw):
        return ("manual", _extract_failure(raw))
    if re.search(r"\(manual\s*[)\-]", raw):
        return ("manual", _extract_failure(raw))
    if raw.startswith("manual") or raw.startswith("**manual**"):
        return ("manual", _extract_failure(raw))
    first_token = re.split(r"[\s(]", raw, maxsplit=1)[0]
    if first_token == "manual":
        return ("manual", _extract_failure(raw))
    if "+" in raw or "cleanup" in raw or "unfusion" in raw or "unfused" in raw or "6-conn" in raw:
        return ("DL+cleanup", "")
    return ("DL", "")


def _extract_failure(raw: str) -> str:
    if "split" in raw:
        return "splitting"
    if "fusion" in raw or "fused" in raw:
        return "fusion"
    if "frag" in raw:
        return "fragmentation"
    if "merg" in raw:
        return "merging"
    if "under-detect" in raw or "underdetect" in raw or "under-detected" in raw:
        return "under_detection"
    if "ood" in raw or "total failure" in raw or "failed" in raw:
        return "ood_or_total_failure"
    if "incomplete" in raw:
        return "incomplete"
    return "unspecified"


def parse_speedup(cell: str) -> str:
    if not cell or cell.strip() in {"-", "--", "\u2014"}:
        return ""
    return strip_md(cell)


def parse_brahman_pct(cell: str) -> str:
    if not cell:
        return ""
    s = strip_md(cell).replace("%", "").strip()
    if s in {"?", "\u2014", "-", "unknown", ""}:
        return ""
    return s


def find_summary_section(text: str) -> str:
    start = text.find("## Production Summary")
    if start < 0:
        raise RuntimeError("'## Production Summary' heading not found in source")
    end = text.find("\n## ", start + 1)
    if end < 0:
        end = len(text)
    return text[start:end]


def parse_table(section_text: str) -> list[dict[str, str]]:
    """Parse the markdown table inside the Production Summary section."""
    rows: list[dict[str, str]] = []
    in_table = False
    header: list[str] = []
    for line in section_text.splitlines():
        if not line.strip().startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in line.split("|")][1:-1]
        if not in_table:
            if any("Sample" in c for c in cells) and any("Hair" in c for c in cells):
                header = cells
                in_table = True
            continue
        if all(re.fullmatch(r":?-+:?", c.replace(" ", "")) for c in cells if c):
            continue
        if not cells or not re.fullmatch(r"[A-Za-z0-9]+-[A-Za-z0-9]+", cells[0]):
            continue
        rows.append(dict(zip(header, cells)))
    return rows


def build_csv_rows(parsed: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in parsed:
        sample = row.get("Sample", "").strip()
        if not sample:
            continue
        set_id = sample.split("-")[0]
        breed = strip_md(row.get("Breed", ""))
        brahman = parse_brahman_pct(row.get("Brahman %", ""))
        hair_cell = row.get("Hair time", "")
        sg_cell = row.get("SG time", "")
        bv_cell = row.get("BV time", "")
        total_cell = row.get("Total", "")
        speedup_cell = row.get("Speedup vs manual", "")
        notes = strip_md(row.get("Notes", ""))

        hair_disp, hair_fail = classify_disposition(hair_cell, "hair")
        sg_disp, sg_fail = classify_disposition(sg_cell, "sg")
        bv_disp, _ = classify_disposition(bv_cell, "bv")

        total_minutes = parse_minutes(total_cell)

        out.append({
            "sample_id": sample,
            "set": set_id,
            "breed": breed,
            "brahman_pct": brahman,
            "hair_disposition": hair_disp,
            "sg_disposition": sg_disp,
            "bv_disposition": bv_disp,
            "hair_failure_mode": hair_fail,
            "sg_failure_mode": sg_fail,
            "hair_time_text": strip_md(hair_cell),
            "sg_time_text": strip_md(sg_cell),
            "bv_time_text": strip_md(bv_cell),
            "total_time_text": strip_md(total_cell),
            "total_minutes": f"{total_minutes:.2f}" if total_minutes is not None else "",
            "speedup": parse_speedup(speedup_cell),
            "hair_manual_fallback": "1" if hair_disp == "manual" else "0",
            "sg_manual_fallback": "1" if sg_disp == "manual" else "0",
            "dual_manual_fallback": "1" if hair_disp == "manual" and sg_disp == "manual" else "0",
            "notes": notes,
        })
    return out


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    if not rows:
        raise RuntimeError("No rows to write")
    cols = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def build_failure_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for r in rows:
        for structure, disp_key, fail_key in (
            ("hair", "hair_disposition", "hair_failure_mode"),
            ("sg", "sg_disposition", "sg_failure_mode"),
        ):
            if r[disp_key] != "manual":
                continue
            out.append({
                "sample_id": r["sample_id"],
                "set": r["set"],
                "breed": r["breed"],
                "brahman_pct": r["brahman_pct"],
                "structure": structure,
                "failure_mode": r[fail_key] or "unspecified",
                "dual_fallback": r["dual_manual_fallback"],
                "time_text": r["hair_time_text"] if structure == "hair" else r["sg_time_text"],
                "notes": r["notes"],
            })
    out.sort(key=lambda x: (x["set"], x["sample_id"], x["structure"]))
    return out


def write_failure_csv(rows: list[dict[str, str]], path: Path) -> None:
    if not rows:
        print("No manual-fallback rows to emit; --failure-output will not be written.")
        return
    cols = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("# One row per (sample, fallback structure).\n")
        f.write("# Dual-fallback samples appear twice (once for hair, once for sg).\n")
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    args = parse_args()

    if not args.source.exists():
        print(f"ERROR: source file not found: {args.source}", file=sys.stderr)
        return 1

    text = args.source.read_text(encoding="utf-8")
    section = find_summary_section(text)
    parsed = parse_table(section)
    rows = build_csv_rows(parsed)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_csv(rows, args.output)

    failure_rows = build_failure_rows(rows)
    args.failure_output.parent.mkdir(parents=True, exist_ok=True)
    write_failure_csv(failure_rows, args.failure_output)

    total = len(rows)
    hair_fb = sum(int(r["hair_manual_fallback"]) for r in rows)
    sg_fb = sum(int(r["sg_manual_fallback"]) for r in rows)
    dual_fb = sum(int(r["dual_manual_fallback"]) for r in rows)
    timed = [r for r in rows if r["total_minutes"]]
    avg_min = (sum(float(r["total_minutes"]) for r in timed) / len(timed)) if timed else None

    print(f"Source: {args.source}")
    print(f"Output: {args.output}")
    print(f"Failure output: {args.failure_output}")
    print()
    print(f"Rows written: {total}")
    print(f"  Hair manual fallback: {hair_fb}")
    print(f"  SG manual fallback:   {sg_fb}")
    print(f"  Dual manual fallback: {dual_fb}")
    print(f"  failure-output rows:  {len(failure_rows)} (expected {hair_fb + sg_fb})")
    if avg_min is not None:
        print(f"  Timed samples: {len(timed)} (avg total: {avg_min:.1f} min)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
