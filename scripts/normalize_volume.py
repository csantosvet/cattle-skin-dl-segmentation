"""Normalize a micro-CT TIFF volume's intensity distribution to match a reference.

Applies a linear transform so the source volume's tissue intensities have the same
mean and standard deviation as the reference volume's tissue intensities:

    normalized = (src - src_mean) / src_std * ref_std + ref_mean

This addresses inter-session gray-value drift in micro-CT, where identical tissue
types end up at different absolute gray values depending on scan settings, tube
condition, and reconstruction parameters. Normalizing a new volume against a
reference volume that a trained DL model was calibrated on lets the model see
intensities in the distribution it was trained for.

The transform
-------------
- Is fully reversible (linear)
- Preserves relative contrast and spatial relationships
- Never modifies the input files (writes a new output file)
- Clips to the uint16 range for Dragonfly compatibility

Tissue detection
----------------
Voxels below the 5th percentile of nonzero values are treated as air/resin/outside-
cylinder and excluded from the mean/std calculation. This avoids needing the exact
cylinder mask and is robust to modest differences in the masked background value.

Usage
-----
    python normalize_volume.py \\
        --source  source.tif \\
        --reference reference.tif \\
        --output  normalized.tif \\
        [--voxel-size-mm 0.00784727] \\
        [--force]

`--voxel-size-mm` is written into the ImageJ-style TIFF metadata so Dragonfly picks
up the correct spacing automatically when the file is imported. Defaults to
0.00784727 mm (the voxel size used in the bundled protocols). Override if your
scans use a different voxel size.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from tifffile import imread, imwrite

DEFAULT_VOXEL_SIZE_MM = 0.00784727


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Match a micro-CT volume's tissue-intensity distribution to a reference.",
    )
    p.add_argument("--source", required=True, help="Volume to normalize (TIFF).")
    p.add_argument("--reference", required=True, help="Reference volume whose distribution we match (TIFF).")
    p.add_argument("--output", required=True, help="Where to write the normalized volume (TIFF).")
    p.add_argument(
        "--voxel-size-mm",
        type=float,
        default=DEFAULT_VOXEL_SIZE_MM,
        help=f"Isotropic voxel size in mm, written to TIFF metadata (default: {DEFAULT_VOXEL_SIZE_MM}).",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --output without asking.",
    )
    return p.parse_args()


def compute_tissue_stats(volume: np.ndarray, label: str = "volume") -> tuple[float, float]:
    """Compute mean and std of tissue voxels, excluding air/background."""
    nonzero = volume[volume > 0].astype(np.float64)
    if nonzero.size == 0:
        raise ValueError(f"{label}: no nonzero voxels found")

    threshold = np.percentile(nonzero, 5)
    tissue = nonzero[nonzero > threshold]

    mean = tissue.mean()
    std = tissue.std()
    p01 = np.percentile(tissue, 1)
    p99 = np.percentile(tissue, 99)

    print(f"  {label}:")
    print(f"    Nonzero voxels: {nonzero.size:,}")
    print(f"    Tissue voxels (above p5={threshold:.0f}): {tissue.size:,}")
    print(f"    Mean: {mean:.1f}")
    print(f"    Std:  {std:.1f}")
    print(f"    Range [p1, p99]: [{p01:.0f}, {p99:.0f}]")

    return mean, std


def normalize_volume(
    src_path: str,
    ref_path: str,
    out_path: str,
    voxel_size_mm: float,
) -> None:
    print(f"Loading source:    {src_path}")
    src_vol = imread(src_path)
    print(f"  Shape: {src_vol.shape}, dtype: {src_vol.dtype}")

    print(f"Loading reference: {ref_path}")
    ref_vol = imread(ref_path)
    print(f"  Shape: {ref_vol.shape}, dtype: {ref_vol.dtype}")

    print("\nComputing tissue statistics...")
    src_mean, src_std = compute_tissue_stats(src_vol, "source")
    ref_mean, ref_std = compute_tissue_stats(ref_vol, "reference")

    print(f"\nTransform: new = (old - {src_mean:.1f}) / {src_std:.1f} * {ref_std:.1f} + {ref_mean:.1f}")

    result = src_vol.astype(np.float64)
    tissue_mask = result > 0
    result[tissue_mask] = (result[tissue_mask] - src_mean) / src_std * ref_std + ref_mean
    result = np.clip(result, 0, 65535).astype(np.uint16)

    print(f"Output range: [{result.min()}, {result.max()}]")

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    print(f"\nWriting normalized volume to: {out_path}")
    imwrite(
        out_path,
        result,
        photometric="minisblack",
        metadata={
            "spacing": voxel_size_mm,
            "unit": "mm",
            "axes": "ZYX",
        },
        imagej=True,
    )

    file_size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Done. Output: {file_size_mb:.1f} MB")
    print(f"\nWhen importing to Dragonfly, verify Image spacing = {voxel_size_mm:.8f} mm in all axes.")


def main() -> int:
    args = parse_args()

    for label, path in (("Source", args.source), ("Reference", args.reference)):
        if not os.path.exists(path):
            print(f"ERROR: {label} file not found: {path}", file=sys.stderr)
            return 1

    if os.path.exists(args.output) and not args.force:
        resp = input(f"WARNING: {args.output} exists. Overwrite? [y/N] ").strip().lower()
        if resp != "y":
            print("Aborted.")
            return 0

    normalize_volume(args.source, args.reference, args.output, args.voxel_size_mm)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
