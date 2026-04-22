# Protocol 01: Conversion of Zeiss Xradia TXM Reconstructed Volumes to TIFF

## Purpose

Convert reconstructed micro-CT volumes from the proprietary Zeiss Xradia TXM format (`.txm`) into standard multi-page TIFF files compatible with open-source and commercial 3D analysis software (Dragonfly, 3D Slicer, ImageJ/Fiji, etc.).

## Background

Micro-CT scans acquired on the Zeiss Xradia Versa 542 produce reconstructed 3D volumes in the proprietary `.txm` format. This format stores volumetric data as an OLE2 (Object Linking and Embedding) structured storage file, with individual slices distributed across multiple internal directories (`ImageData1` through `ImageDataN`, each containing up to 100 slice entries). The `.txm` format is not natively supported by most open-source segmentation software.

The conversion extracts these slices, reassembles them into a contiguous 3D volume, and writes the result as a single ImageJ-compatible multi-page TIFF with embedded voxel spacing metadata.

## Input Data

### Scanner Parameters

| Parameter | Value |
| --- | --- |
| Scanner | Zeiss Xradia Versa 542 |
| Voltage | 100 kV |
| Power | 14.0 W |
| Objective | 0.4X |
| Filter | LE3 |
| Binning | 2 |
| Number of projections | 1301 |
| Rotation | 360 degrees |

### Input File

- **File**: `*_recon.txm` (reconstructed 3D volume)
- **Typical size**: ~2 GB per sample
- **Location example**: `<source_root>/<session_date>/<sample_id>/<session>_<sample_id>_recon.txm`

Other files in the sample folder (`.txrm` raw projections, `_Drift.txrm`, scout images) are **not** needed for the conversion and should be preserved as archival data only.

## Output Data

- **Format**: Multi-page TIFF (ImageJ-compatible, BigTIFF for files >4 GB)
- **Data type**: uint16 (16-bit unsigned integer), matching the original reconstruction
- **Embedded metadata**: Voxel spacing (Z-spacing and XY resolution in micrometers), axes order (ZYX)
- **Typical output size**: ~1.98 GB per sample (uncompressed, equivalent to source)

### Validated Output (Test Sample 23-89)

| Property | Value |
| --- | --- |
| Volume dimensions | 1004 x 1024 x 1010 (Width x Height x Slices) |
| Voxel size | 7.847 micrometers (isotropic) |
| Data type | uint16 |
| Output file size | 1,980.7 MB |
| Pixel value range | 0 -- 29,926 |

## Method

### Software Requirements

- Python 3.10 or later
- Python packages: `olefile`, `numpy`, `tifffile`

Installation:

```
pip install olefile numpy tifffile
```

### TXM File Structure

The Zeiss TXM format uses OLE2 structured storage. The reconstructed volume is stored as follows:

```
TXM File (OLE2)
├── ImageInfo/
│   ├── ImageWidth      (int32: 1004)
│   ├── ImageHeight     (int32: 1024)
│   ├── NoOfImages      (int32: 1010)
│   └── PixelSize       (float32: 7.847 micrometers)
├── ImageData1/
│   ├── Image1          (raw bytes: Width x Height x 2 bytes, uint16)
│   ├── Image2
│   └── ... Image100
├── ImageData2/
│   ├── Image1          (= global slice 101)
│   └── ... Image100
├── ...
├── ImageData10/
│   ├── Image1          (= global slice 901)
│   └── ... Image100
└── ImageData11/
    ├── Image1          (= global slice 1001)
    └── ... Image10     (= global slice 1010)
```

Each `ImageDataN/ImageM` entry contains a raw byte buffer of size `Width x Height x 2` (for uint16). The global slice index is computed as `(N - 1) * 100 + M`.

### Conversion Algorithm

1. Open the `.txm` file using the `olefile` library.
2. Read volume metadata from `ImageInfo/` streams: width, height, number of slices, and pixel size.
3. Enumerate all `ImageDataN/ImageM` streams and sort by global slice index.
4. Validate slice byte count against expected size (`Width x Height x sizeof(dtype)`).
5. Read each slice as a 1D byte buffer, interpret as uint16, and reshape to `(Height, Width)`.
6. Stack all slices into a 3D numpy array of shape `(Slices, Height, Width)`.
7. Write the volume as a multi-page TIFF using `tifffile.imwrite()` with ImageJ-compatible metadata including voxel spacing.

### Conversion Script

The conversion script is located at:

```
segmentation\convert_txm_to_tiff.py
```

**Single file conversion:**

```
python convert_txm_to_tiff.py --input <reconstruction.txm> --output <output.tif>
```

**Example:**

```
python convert_txm_to_tiff.py --input "<source_root>/<SampleID>/<SampleID>_recon.txm" --output "<project_root>/01_TIFF_STACKS/<SampleID>/<SampleID>_recon.tif"
```

### Performance

Conversion of a single 2 GB sample (1004 x 1024 x 1010, uint16) completed in approximately 8.5 seconds on a desktop PC (Intel Core i9-10850K, 32 GB RAM, NVMe SSD).

## Verification

After conversion, the output TIFF was validated by reading it back with `tifffile` and confirming:

1. **Slice count**: 1010 pages (matches `ImageInfo/NoOfImages`).
2. **Slice dimensions**: 1024 x 1004 pixels (matches `ImageInfo/ImageHeight` x `ImageInfo/ImageWidth`).
3. **Data type**: uint16 (matches source encoding).
4. **Voxel metadata**: Spacing = 7.847 um embedded in ImageJ metadata (matches `ImageInfo/PixelSize` and `config.txt`).
5. **Pixel value range**: Non-zero, physiologically plausible range (0 to 29,926 for sample 23-89).

## Notes

- The `.txrm` files in the same sample folder contain raw X-ray projection data (pre-reconstruction). These are **not** used for segmentation and should not be converted with this protocol.
- The `txrm2tiff` PyPI package (v2.2.0) handles `.txrm` and `.xrm` files only; it does **not** support the `.txm` reconstructed volume format. This custom conversion script was developed to address that gap.
- The voxel size (7.847 um) is automatically embedded in the TIFF metadata. When importing into Dragonfly, the software should auto-detect this value. Always verify the voxel size is set correctly before performing any measurements.
- Original `.txm` files must be preserved as archival source data. The conversion is read-only and does not modify the input file.
- For batch conversion of an entire cohort, see `conversion/batch_convert_all.py` (safe, resumable, read-only on originals).

## Importing into Dragonfly

When importing the converted TIFF into Dragonfly 3D World (2025.1), the software presents an "Import Image" dialog. The following settings must be verified:

| Field | Correct Value | Notes |
| --- | --- | --- |
| Image spacing X (mm) | **0.00784727** | Must be entered manually |
| Image spacing Y (mm) | **0.00784727** | Must be entered manually |
| Image spacing Z (mm) | **0.00784727** | Must be entered manually |
| Image sampling (X, Y, Z, T) | 1, 1, 1, 1 | Default, do not change |
| Physical conversion Offset | 0 | Default, do not change |
| Physical conversion Slope | 1 | Default, do not change |
| Axis transformation | XYZ | Default, do not change |

**Important**: Dragonfly does not correctly auto-detect the voxel spacing from the embedded ImageJ TIFF metadata. The three Image spacing fields default to incorrect values and must be manually set to `0.00784727` mm (= 7.847 micrometers) in all three axes before clicking Finish. All other fields auto-populate correctly (Width: 1004, Height: 1024, Depth: 1010, Bits: 16, Mode: Grayscale).

This was validated with Dragonfly 3D World version 2025.1 (Build 2063).
