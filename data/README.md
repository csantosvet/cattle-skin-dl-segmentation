# Data

This repository distributes **code, protocols, and operator-training images
only**. No experimental dataset is shipped with the repository.

## Applying the pipeline to your own data

1. Convert raw TXM reconstructions to multi-page TIFF with the converter:

    ```bash
    python conversion/convert_txm_to_tiff.py \
        --input  <path-to-recon.txm> \
        --output <path-to-recon.tif>
    ```

    For a directory tree of reconstructions, use the resumable batch runner:

    ```bash
    python conversion/batch_convert_all.py \
        --source-root <raw-scan-root> \
        --output-root <tiff-stack-root>
    ```

2. Organize TIFFs under a project root as follows:

    ```text
    <project_root>/
    ├── 01_TIFF_STACKS/
    │   └── <SampleID>/<SampleID>_recon.tif
    ├── 02_DRAGONFLY_PROJECTS/
    │   └── <SampleID>_session/
    └── 03_RESULTS/
        ├── Hair/<SampleID>_hair.csv
        ├── SweatGlands/<SampleID>_sg.csv
        └── BloodVessels/<SampleID>_bv.csv
    ```

3. Segment each sample in Dragonfly following either
   [`protocols/02_Manual_Segmentation_Dragonfly.md`](../protocols/02_Manual_Segmentation_Dragonfly.md) (manual thresholding) or
   [`protocols/03_AI_Segmentation_Wizard_Automation.md`](../protocols/03_AI_Segmentation_Wizard_Automation.md) (DL-assisted).

4. Export the per-structure CSVs from Dragonfly into the `03_RESULTS/`
   subfolders and consolidate them into a master measurements file:

    ```bash
    python scripts/populate_master_csv.py \
        --results-dir <project_root>/03_RESULTS \
        --master-csv  <project_root>/master_measurements.csv
    ```

The master measurements schema and the expected per-sample CSV format are
documented in [`protocols/04_Data_Management_and_Scripts.md`](../protocols/04_Data_Management_and_Scripts.md).

## Preparing your own master CSV

The master CSV is a per-sample spreadsheet created by the user. Only one
column is required: `Sample_ID`, whose values must match the sample prefix of
the per-structure CSV file names (e.g. `S01` for `S01_hair.csv`). All other
columns (breed, herd, treatment group, animal ID, external phenotypes, etc.)
are optional user-defined metadata and are preserved unchanged by the scripts.

If your spreadsheet uses a different column name for the sample identifier,
pass `--sample-id-column <your-column-name>` to `populate_master_csv.py`.
