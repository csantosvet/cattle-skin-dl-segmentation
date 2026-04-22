"""Batch converter: Zeiss Xradia TXM reconstructed volumes -> multi-page TIFF stacks.

Safety guarantees
-----------------
- NEVER modifies, deletes, or overwrites files under --source-root.
- Opens TXM files in read-only mode (olefile).
- Writes only to --output-root.
- Uses a temp filename during each conversion; renames only on success.
- Skips samples that already have a valid output TIFF.
- Fully resumable via a manifest CSV (written to <output-root>/_manifest.csv).

Usage
-----
    # Scan sources and build the manifest (no conversion):
    python batch_convert_all.py --source-root SRC --output-root OUT --dry-run

    # Convert the next 10 pending samples:
    python batch_convert_all.py --source-root SRC --output-root OUT --batch 10

    # Convert all remaining pending samples:
    python batch_convert_all.py --source-root SRC --output-root OUT --batch 0

    # Show progress summary from the existing manifest:
    python batch_convert_all.py --output-root OUT --status

Source-folder conventions
-------------------------
The script recursively searches --source-root for any file whose name ends in
`_recon.txm`. It groups files under an identifier derived from the file name
(everything before `_recon.txm`). If a file name has the form `DATE_ID_recon.txm`
(for example `04-21-25_23-89_recon.txm`), `DATE` is recorded as the scan date
and `ID` as the sample id. Subfolders whose names match --skip-folder are
ignored (pass --skip-folder once per folder to skip).
"""
from __future__ import annotations

import argparse
import csv
import datetime
import os
import sys
import time


MANIFEST_FIELDS = [
    "sample_id", "scan_date", "txm_path", "txm_size_bytes",
    "tiff_path", "status", "tiff_size_bytes", "error_message",
    "conversion_timestamp",
]

DEFAULT_SKIP_FOLDERS = (
    "Trials", "CT Reconstruction Training", "Pictures",
    "Test Image Stack", "Versa_Files", "Screenshots",
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Safe, resumable batch converter from TXM reconstructions to TIFF stacks.",
    )
    p.add_argument("--source-root",
                   help="Directory to recursively scan for *_recon.txm files. Required for "
                        "--dry-run, --rebuild-manifest, and --batch.")
    p.add_argument("--output-root", required=True,
                   help="Directory where TIFF stacks, the manifest, and the log are written.")
    p.add_argument("--dry-run", action="store_true",
                   help="Scan and build the manifest; do not convert anything.")
    p.add_argument("--rebuild-manifest", action="store_true",
                   help="Rescan --source-root and rewrite the manifest (preserves 'done' status).")
    p.add_argument("--batch", type=int,
                   help="Convert N pending samples (0 = all remaining).")
    p.add_argument("--status", action="store_true",
                   help="Print progress summary from the existing manifest.")
    p.add_argument("--skip-folder", action="append", default=list(DEFAULT_SKIP_FOLDERS),
                   help="Folder name to skip when scanning --source-root (repeatable).")
    return p.parse_args()


def manifest_path(output_root: str) -> str:
    return os.path.join(output_root, "_manifest.csv")


def log_path(output_root: str) -> str:
    return os.path.join(output_root, "_conversion_log.txt")


def log(output_root: str, msg: str, also_print: bool = True) -> None:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    if also_print:
        print(line)
    os.makedirs(output_root, exist_ok=True)
    with open(log_path(output_root), "a", encoding="utf-8") as f:
        f.write(line + "\n")


def scan_sources(source_root: str, skip_folders: set[str]) -> dict[str, dict[str, str]]:
    """Recursively find every _recon.txm file under source_root.

    Returns a dict mapping sample_id -> {scan_date, txm_path}. If a file is
    named like `DATE_ID_recon.txm` the DATE is captured as scan_date; otherwise
    the file's mtime (formatted MM-DD-YY) is used.
    """
    results: dict[str, dict[str, str]] = {}
    for dirpath, dirnames, filenames in os.walk(source_root):
        dirnames[:] = [d for d in dirnames if d not in skip_folders]
        for fname in filenames:
            if not fname.endswith("_recon.txm"):
                continue
            txm_path = os.path.join(dirpath, fname)
            base = fname.replace("_recon.txm", "")
            parts = base.split("_", 1)
            if len(parts) == 2:
                scan_date, sample_id = parts
            else:
                mtime = os.path.getmtime(txm_path)
                scan_date = datetime.datetime.fromtimestamp(mtime).strftime("%m-%d-%y")
                sample_id = base
            if sample_id not in results:
                results[sample_id] = {"scan_date": scan_date, "txm_path": txm_path}
    return results


def build_manifest(source_root: str, output_root: str, skip_folders: set[str]) -> list[dict[str, str]]:
    log(output_root, "=== BUILDING MANIFEST ===")
    log(output_root, f"Scanning: {source_root}")

    samples = scan_sources(source_root, skip_folders)
    log(output_root, f"Found {len(samples)} unique samples")

    rows: list[dict[str, str]] = []
    for sample_id in sorted(samples.keys()):
        info = samples[sample_id]
        txm_path = info["txm_path"]
        txm_size = os.path.getsize(txm_path)
        tiff_dir = os.path.join(output_root, sample_id)
        tiff_path = os.path.join(tiff_dir, f"{sample_id}_recon.tif")

        if os.path.exists(tiff_path):
            status = "done"
            tiff_size = os.path.getsize(tiff_path)
        else:
            status = "pending"
            tiff_size = 0

        rows.append({
            "sample_id": sample_id,
            "scan_date": info["scan_date"],
            "txm_path": txm_path,
            "txm_size_bytes": str(txm_size),
            "tiff_path": tiff_path,
            "status": status,
            "tiff_size_bytes": str(tiff_size),
            "error_message": "",
            "conversion_timestamp": "",
        })

    os.makedirs(output_root, exist_ok=True)
    with open(manifest_path(output_root), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    log(output_root, f"Manifest written: {manifest_path(output_root)}")
    pending = sum(1 for r in rows if r["status"] == "pending")
    done = sum(1 for r in rows if r["status"] == "done")
    log(output_root, f"Total: {len(rows)} | Pending: {pending} | Already done: {done}")
    return rows


def load_manifest(output_root: str) -> list[dict[str, str]] | None:
    path = manifest_path(output_root)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_manifest(rows: list[dict[str, str]], output_root: str) -> None:
    with open(manifest_path(output_root), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_metadata_txt(sample_id: str, scan_date: str, txm_path: str,
                        meta: dict, tiff_path: str) -> None:
    meta_path = os.path.join(os.path.dirname(tiff_path), "metadata.txt")
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"Sample ID: {sample_id}\n")
        f.write(f"Scan Date: {scan_date}\n")
        f.write(f"Original TXM Path: {txm_path}\n")
        f.write(f"Volume Width: {meta['width']}\n")
        f.write(f"Volume Height: {meta['height']}\n")
        f.write(f"Number of Slices: {meta['n_slices']}\n")
        f.write(f"Voxel Size (um): {meta['pixel_size_um']:.4f}\n")
        f.write(f"Voxel Size (mm): {meta['pixel_size_um'] / 1000:.8f}\n")
        f.write(f"TIFF Path: {tiff_path}\n")
        f.write(f"Conversion Date: {datetime.datetime.now().isoformat()}\n")


def convert_single(
    txm_path: str,
    tiff_path: str,
    sample_id: str,
    scan_date: str,
    output_root: str,
) -> tuple[bool, dict | None, str]:
    import olefile
    import numpy as np
    import struct
    from tifffile import imwrite

    tiff_dir = os.path.dirname(tiff_path)
    temp_path = os.path.join(tiff_dir, f"{sample_id}_converting.tif")
    if os.path.exists(temp_path):
        os.remove(temp_path)

    try:
        ole = olefile.OleFileIO(txm_path)

        def read_int(name: str) -> int:
            return struct.unpack("<i", ole.openstream(name).read())[0]

        def read_float(name: str) -> float:
            return struct.unpack("<f", ole.openstream(name).read())[0]

        meta = {
            "width": read_int("ImageInfo/ImageWidth"),
            "height": read_int("ImageInfo/ImageHeight"),
            "n_slices": read_int("ImageInfo/NoOfImages"),
            "pixel_size_um": read_float("ImageInfo/PixelSize"),
        }

        slices: list[tuple[int, str]] = []
        for s in ole.listdir():
            if len(s) == 2 and s[0].startswith("ImageData") and s[1].startswith("Image"):
                try:
                    dir_num = int(s[0].replace("ImageData", ""))
                    img_num = int(s[1].replace("Image", ""))
                    slices.append(((dir_num - 1) * 100 + img_num, "/".join(s)))
                except ValueError:
                    continue
        slices.sort(key=lambda x: x[0])

        if len(slices) != meta["n_slices"]:
            log(output_root, f"  WARNING: expected {meta['n_slices']} slices, found {len(slices)}")

        first_data = ole.openstream(slices[0][1]).read()
        expected_u16 = meta["width"] * meta["height"] * 2
        expected_f32 = meta["width"] * meta["height"] * 4
        if len(first_data) == expected_u16:
            dtype = np.uint16
        elif len(first_data) == expected_f32:
            dtype = np.float32
        else:
            ole.close()
            return False, meta, f"Unexpected slice size: {len(first_data)} bytes"

        n = len(slices)
        volume = np.zeros((n, meta["height"], meta["width"]), dtype=dtype)
        for i, (_, stream) in enumerate(slices):
            data = ole.openstream(stream).read()
            volume[i] = np.frombuffer(data, dtype=dtype).reshape(meta["height"], meta["width"])
            if (i + 1) % 200 == 0 or i == n - 1:
                log(output_root, f"  Reading slices: {i + 1}/{n}")
        ole.close()

        os.makedirs(tiff_dir, exist_ok=True)
        pixel_size_mm = meta["pixel_size_um"] / 1000.0
        resolution_ppmm = 1.0 / pixel_size_mm
        imwrite(
            temp_path,
            volume,
            photometric="minisblack",
            resolution=(resolution_ppmm, resolution_ppmm),
            resolutionunit=3,
            metadata={"spacing": pixel_size_mm, "unit": "mm", "axes": "ZYX"},
            imagej=True,
        )

        del volume

        if not os.path.exists(temp_path):
            return False, meta, "Temp TIFF file not found after write"

        temp_size = os.path.getsize(temp_path)
        min_expected = meta["width"] * meta["height"] * n * 2 * 0.8
        if temp_size < min_expected:
            os.remove(temp_path)
            return False, meta, f"TIFF too small: {temp_size} bytes (expected >{min_expected:.0f})"

        os.rename(temp_path, tiff_path)
        write_metadata_txt(sample_id, scan_date, txm_path, meta, tiff_path)
        return True, meta, ""

    except Exception as exc:  # noqa: BLE001 - we propagate the message in the row
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        return False, None, str(exc)


def run_batch(output_root: str, batch_size: int) -> None:
    rows = load_manifest(output_root)
    if rows is None:
        log(output_root, "No manifest found. Run --dry-run first to build it.")
        return

    stale = [r for r in rows if r["status"] == "converting"]
    for r in stale:
        log(output_root, f"  Resetting interrupted sample: {r['sample_id']} (was 'converting')")
        r["status"] = "pending"
    if stale:
        save_manifest(rows, output_root)

    pending = [r for r in rows if r["status"] == "pending"]
    if not pending:
        log(output_root, "All samples are already converted.")
        return

    to_convert = pending if batch_size == 0 else pending[:batch_size]
    log(output_root, f"=== BATCH CONVERSION: {len(to_convert)} of {len(pending)} pending samples ===")

    converted = 0
    errors = 0
    batch_start = time.time()

    for i, row in enumerate(to_convert):
        sample_id = row["sample_id"]
        txm_path = row["txm_path"]
        tiff_path = row["tiff_path"]
        scan_date = row["scan_date"]

        log(output_root, f"[{i + 1}/{len(to_convert)}] Converting: {sample_id}")

        if not os.path.exists(txm_path):
            row["status"] = "error"
            row["error_message"] = "TXM file not found"
            log(output_root, f"  ERROR: TXM not found: {txm_path}")
            errors += 1
            save_manifest(rows, output_root)
            continue

        if os.path.exists(tiff_path):
            row["status"] = "done"
            row["tiff_size_bytes"] = str(os.path.getsize(tiff_path))
            log(output_root, "  SKIP: TIFF already exists")
            save_manifest(rows, output_root)
            continue

        row["status"] = "converting"
        save_manifest(rows, output_root)

        sample_start = time.time()
        success, _meta, err_msg = convert_single(txm_path, tiff_path, sample_id, scan_date, output_root)
        elapsed = time.time() - sample_start

        if success:
            tiff_size = os.path.getsize(tiff_path)
            row["status"] = "done"
            row["tiff_size_bytes"] = str(tiff_size)
            row["error_message"] = ""
            row["conversion_timestamp"] = datetime.datetime.now().isoformat()
            converted += 1
            log(output_root, f"  OK: {tiff_size / (1024**2):.0f} MB in {elapsed:.1f}s")
        else:
            row["status"] = "error"
            row["error_message"] = err_msg
            errors += 1
            log(output_root, f"  ERROR: {err_msg}")

        save_manifest(rows, output_root)

    batch_elapsed = time.time() - batch_start
    log(output_root, "=== BATCH COMPLETE ===")
    log(output_root, f"  Converted: {converted}/{len(to_convert)}")
    log(output_root, f"  Errors: {errors}")
    log(output_root, f"  Batch time: {batch_elapsed:.0f}s ({batch_elapsed / 60:.1f} min)")
    if converted > 0:
        avg = batch_elapsed / converted
        remaining = len(pending) - converted
        log(output_root, f"  Average per sample: {avg:.1f}s ({avg / 60:.1f} min)")
        log(output_root, f"  Estimated time for remaining {remaining}: {remaining * avg / 60:.0f} min")


def show_status(output_root: str) -> None:
    rows = load_manifest(output_root)
    if rows is None:
        print("No manifest found. Run --dry-run first.")
        return

    total = len(rows)
    by_status: dict[str, int] = {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1

    print("=" * 50)
    print("CONVERSION PROGRESS")
    print("=" * 50)
    print(f"Total samples: {total}")
    for status in ("done", "pending", "converting", "error"):
        count = by_status.get(status, 0)
        pct = count / total * 100 if total > 0 else 0
        bar = "#" * int(pct / 2)
        print(f"  {status:>12}: {count:>4} ({pct:5.1f}%) {bar}")

    done_sizes = [int(r["tiff_size_bytes"]) for r in rows
                  if r["status"] == "done" and r["tiff_size_bytes"] != "0"]
    if done_sizes:
        total_gb = sum(done_sizes) / (1024 ** 3)
        print(f"\nTIFF output so far: {total_gb:.1f} GB")

    err_rows = [r for r in rows if r["status"] == "error"]
    if err_rows:
        print("\nErrors:")
        for r in err_rows:
            print(f"  {r['sample_id']}: {r['error_message']}")


def main() -> int:
    args = parse_args()
    output_root = args.output_root
    os.makedirs(output_root, exist_ok=True)

    if args.status:
        show_status(output_root)
        return 0

    if args.dry_run or args.rebuild_manifest:
        if not args.source_root:
            print("ERROR: --source-root is required for --dry-run / --rebuild-manifest",
                  file=sys.stderr)
            return 1
        rows = build_manifest(args.source_root, output_root, set(args.skip_folder))
        print(f"\nManifest saved to: {manifest_path(output_root)}")
        pending = sum(1 for r in rows if r["status"] == "pending")
        done = sum(1 for r in rows if r["status"] == "done")
        print(f"Total: {len(rows)} | Pending: {pending} | Already done: {done}")
        if pending:
            print("\nTo start converting, run:")
            print(f'  python batch_convert_all.py --source-root "{args.source_root}" '
                  f'--output-root "{output_root}" --batch 10')
        return 0

    if args.batch is not None:
        if not args.source_root and load_manifest(output_root) is None:
            print("ERROR: no manifest found and --source-root not provided. "
                  "Run --dry-run first (with --source-root) to build the manifest.",
                  file=sys.stderr)
            return 1
        if load_manifest(output_root) is None:
            build_manifest(args.source_root, output_root, set(args.skip_folder))
        run_batch(output_root, args.batch)
        return 0

    print("No action specified. Try --help.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
