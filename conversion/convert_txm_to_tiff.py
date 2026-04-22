"""Convert a Zeiss Xradia TXM reconstructed volume to a multi-page TIFF stack.

Reads the OLE2 structured TXM file, extracts every slice, stacks them into a 3D
uint16 (or float32) array, and writes an ImageJ-flavored TIFF whose metadata
records the voxel spacing. The output is loadable directly into Dragonfly.

Usage
-----
    python convert_txm_to_tiff.py --input reconstruction.txm --output volume.tif
"""
from __future__ import annotations

import argparse
import os
import struct
import sys

import numpy as np
import olefile
from tifffile import imwrite


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Convert a Zeiss Xradia TXM reconstructed volume to a multi-page TIFF.",
    )
    p.add_argument("--input", required=True, help="Path to the input .txm file.")
    p.add_argument("--output", required=True, help="Path to the output .tif file.")
    return p.parse_args()


def read_txm_metadata(ole: olefile.OleFileIO) -> dict[str, float | int]:
    def read_int(stream_name: str) -> int:
        data = ole.openstream(stream_name).read()
        return struct.unpack("<i", data)[0]

    def read_float(stream_name: str) -> float:
        data = ole.openstream(stream_name).read()
        return struct.unpack("<f", data)[0]

    return {
        "width": read_int("ImageInfo/ImageWidth"),
        "height": read_int("ImageInfo/ImageHeight"),
        "n_slices": read_int("ImageInfo/NoOfImages"),
        "pixel_size_um": read_float("ImageInfo/PixelSize"),
    }


def collect_slice_streams(ole: olefile.OleFileIO) -> list[tuple[int, str]]:
    slices: list[tuple[int, str]] = []
    for s in ole.listdir():
        if len(s) == 2 and s[0].startswith("ImageData") and s[1].startswith("Image"):
            try:
                dir_num = int(s[0].replace("ImageData", ""))
                img_num = int(s[1].replace("Image", ""))
                global_idx = (dir_num - 1) * 100 + img_num
                slices.append((global_idx, "/".join(s)))
            except ValueError:
                continue
    slices.sort(key=lambda x: x[0])
    return slices


def convert_txm_to_tiff(input_path: str, output_path: str) -> bool:
    print(f"Opening: {input_path}")
    ole = olefile.OleFileIO(input_path)

    meta = read_txm_metadata(ole)
    print(f"Volume dimensions: {meta['width']} x {meta['height']} x {meta['n_slices']}")
    print(f"Voxel size: {meta['pixel_size_um']:.3f} micrometers")

    slices = collect_slice_streams(ole)
    print(f"Found {len(slices)} slice streams")
    if len(slices) != meta["n_slices"]:
        print(f"WARNING: expected {meta['n_slices']} slices but found {len(slices)}")

    first_data = ole.openstream(slices[0][1]).read()
    expected_u16 = meta["width"] * meta["height"] * 2
    expected_f32 = meta["width"] * meta["height"] * 4
    if len(first_data) == expected_u16:
        dtype = np.uint16
        print(f"Data type: uint16 ({len(first_data)} bytes per slice)")
    elif len(first_data) == expected_f32:
        dtype = np.float32
        print(f"Data type: float32 ({len(first_data)} bytes per slice)")
    else:
        print(
            f"ERROR: unexpected slice size {len(first_data)} bytes "
            f"(expected uint16={expected_u16} or float32={expected_f32})",
            file=sys.stderr,
        )
        ole.close()
        return False

    n = len(slices)
    volume = np.zeros((n, meta["height"], meta["width"]), dtype=dtype)
    print(f"Reading {n} slices...")
    for i, (_, stream) in enumerate(slices):
        data = ole.openstream(stream).read()
        volume[i] = np.frombuffer(data, dtype=dtype).reshape(meta["height"], meta["width"])
        if (i + 1) % 100 == 0 or i == n - 1:
            print(f"  {i + 1}/{n} slices read")
    ole.close()

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    pixel_size_mm = meta["pixel_size_um"] / 1000.0
    resolution_ppmm = 1.0 / pixel_size_mm
    imwrite(
        output_path,
        volume,
        photometric="minisblack",
        resolution=(resolution_ppmm, resolution_ppmm),
        resolutionunit=3,  # centimeters per TIFF spec; ImageJ metadata overrides with mm
        metadata={"spacing": pixel_size_mm, "unit": "mm", "axes": "ZYX"},
        imagej=True,
    )

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Done. Output: {file_size_mb:.1f} MB")
    print(f"Voxel size: {meta['pixel_size_um']:.3f} um = {pixel_size_mm:.8f} mm")
    print(f"When importing to Dragonfly, verify Image spacing = {pixel_size_mm:.8f} mm in all axes.")
    return True


def main() -> int:
    args = parse_args()
    if not os.path.exists(args.input):
        print(f"ERROR: input file not found: {args.input}", file=sys.stderr)
        return 1
    return 0 if convert_txm_to_tiff(args.input, args.output) else 1


if __name__ == "__main__":
    raise SystemExit(main())
