# Protocol 02: Manual Segmentation in Dragonfly

## Purpose

Step-by-step instructions for manually segmenting hair, sweat glands, blood vessels, and measuring dermis-to-sweat-gland distance in Dragonfly 3D World. This protocol is used for the first 5-10 samples to establish ground truth and generate training data for later AI-assisted automation.

## Prerequisites

- Dragonfly 3D World 2025.1 or later installed with a valid license (FreeD academic or trial).
- Sample already converted from TXM to TIFF (see Protocol 01).
- Converted TIFF file located in the project folder (e.g., `<project_root>/01_TIFF_STACKS/<SampleID>/<SampleID>_recon.tif`).

## Reference Values


| Parameter                                  | Value                                                  |
| ------------------------------------------ | ------------------------------------------------------ |
| Voxel size (isotropic)                     | 7.847 um = 0.00784727 mm                               |
| Cylinder mask diameter                     | 2.00 mm (radius = 1 mm), applied to all samples        |
| Process Islands threshold (all structures) | up to 50 voxels, 26-connected (production value; intentionally conservative to preserve very small hair and sweat-gland components) |


---

## Part A: Import, Align, and Setup

These steps are performed once per sample and shared across all three structure types.

### A.1 Open Dragonfly and Import the TIFF Stack

1. Launch **Dragonfly 3D World**.
2. If you have a saved session from a previous sample: **File > Load Session** and use it as a starting point.
3. For a new sample: **File > Import Image Stacks and Raw Data**.
4. Navigate to the TIFF file (e.g., `01_TIFF_STACKS\23-89\23-89_recon.tif`) and select it.
5. In the **Import Image** dialog, manually set these three fields:
  - Image spacing X (mm): **0.00784727**
  - Image spacing Y (mm): **0.00784727**
  - Image spacing Z (mm): **0.00784727**
6. Leave all other fields at their defaults (Sampling: 1,1,1,1 | Offset: 0 | Slope: 1 | Axis: XYZ).
7. Click **Finish**. The volume will load into the workspace.

### A.2 Adjust Window/Level (Visibility)

After import, the volume may appear completely black because the default display range doesn't match the data's gray-value distribution.

1. In the **left panel**, under **MAIN**, find the **Window Level** tool.
2. Adjust the **Gamma** slider to bring structures into visibility — move it until you can see the internal anatomy (hair, dermis, glands) through the volume.
3. This does not alter the data — it only changes how it is displayed.

Step 1: Raw import — volume appears dark/unreadable

Step 2: After Window Level adjustment — internal structures become visible

### A.3 Orient and Align the Sample

The sample needs to be oriented so the epidermis (skin surface) is on top and roughly horizontal. Some samples arrive with debris from adjacent samples (they were physically stacked during scanning), so correct orientation is essential.

**Goal**: Hair pointing upward, epidermis flat and level, aligned with the viewing axes.

**Rotation procedure**:

1. Enter **Track mode** (in the toolbar or via shortcut).
2. In each **2D view** individually, adjust the **Roll** value to rotate the slice planes until the sample is upright — hair on top, base on bottom.
3. In the **3D view**, use the Track tool to manually flip/rotate the volume to match.
4. Aim for: the epidermis should appear as a flat horizontal band at the top, with hair follicles descending below it.

Step 3: Sample rotated but axes not yet aligned

**Axis alignment** (critical step):

1. After rotating, the **viewing axes** will have rotated with the sample and are no longer perpendicular.
2. You must **manually realign the axes** so they form a 90-degree cross.
3. Hover over an axis line in any 2D view — small **arrow handles** will appear.
4. **Click the arrows** to rotate the axis back into alignment. Important: clicking the line itself moves the axis position (translation), while clicking the arrows rotates it.
5. Repeat for all three orthogonal views until the axes are perpendicular.

Step 4: Fully rotated with axes realigned to 90 degrees

**Anatomical landmarks to identify during orientation**:

- **Top of volume**: Epidermis (skin surface) — bright, dense horizontal band.
- **Upper-mid region**: Hair follicles — bright, elongated cylindrical structures descending from the surface.
- **Mid region**: Sweat glands — rounded/tubular structures, typically brighter than surrounding dermis tissue.
- **Lower-mid region**: Blood vessels — fainter tubular structures, lower contrast than hair.
- **Bottom**: Base of the biopsy.

### A.4 Create Named Segmentation Layers

Before beginning segmentation, create empty ROI layers for each structure. This keeps everything organized.

1. In the **Data Properties** or **Scene** panel, right-click and select **New ROI** (or use the ROI Toolbar).
2. Create the following named ROIs (one at a time):
  - `Hair`
  - `SweatGlands`
  - `BloodVessels`
  - `Dermis`
3. Assign each ROI a distinct color for easy visual differentiation (e.g., Hair = yellow, SweatGlands = green, BloodVessels = red, Dermis = blue).

### A.5 Save Session

Before starting the cylinder standardization, save the oriented volume as a Dragonfly session.

1. Go to **File > Save Session**.
2. Save to the `02_DRAGONFLY_PROJECTS` folder using the standard naming convention (e.g., `<sample_id>_recon`).
3. This saved session preserves the orientation and is the starting point for AI model training.

### A.6 Standardize Sample Size (Cylinder Mask)

Biopsy samples vary in physical diameter. To ensure comparable measurements across all samples, apply a fixed-diameter cylinder mask before any segmentation.

**Step 1: Create the cylinder**

1. In the **Shapes** toolbar at the top of the screen, click the **Create a cylinder** button.

Shapes toolbar — cylinder button

**Step 2: Position the cylinder**

1. The cylinder will not appear in the correct position initially. You must adjust it using all four views in the Quad View.
2. The cylinder displays **three small square handles**: one in the middle and one at each end (top/bottom).
  - **Middle handle**: click and drag to **move** (translate) the cylinder.
  - **End handles**: click and drag to **rotate** the direction of the cylinder.
3. Use the **lateral 2D views** (side views) to ensure the cylinder appears as a vertical rectangle — it should be aligned with the sample's vertical axis (hair pointing up).
4. Use the **3D view** to verify the cylinder is positioned as a clean vertical cut through the sample.
5. Use the **top/bottom 2D view** (axial cross-section) to center the cylinder over a region with good coverage of hair, sweat glands, and blood vessels if visible.

Cylinder positioned — visible in all four quad views

**Step 3: Set cylinder radius**

1. With the cylinder selected, open the **Properties** panel on the right side.
2. Under **Size**, set **Radius** to **1 mm** (which gives a 2 mm diameter — our standard).
3. Set the **Height** to cover the full length of the sample. The exact height does not matter because each segmentation trims its own analysis area later.

Cylinder properties — Radius set to 1 mm

**Step 4: Verify cylinder placement**

1. Confirm in the axial view that the cylinder selects a good portion of the hair and sweat glands in the cross-section.
2. If a blood vessel is visible, try to include it within the cylinder when possible.

Cylinder in final position

**Step 5: Duplicate the volume**

1. In the **Data Properties** panel, right-click the original volume (e.g., `<sample_id>_recon`) and **Duplicate** it. This creates `<sample_id>_recon (Copied)`.
2. This backup preserves the original volume, since the masking step modifies the data.

Volume duplicated in Data Properties panel

**Step 6: Mask with the cylinder**

1. Right-click the **Cylinder** object in the Data Properties panel.
2. Select **Mask Structured Grid...** from the context menu.

Right-click menu — Mask Structured Grid option

1. In the dialog that appears, select the **original volume** (e.g., `<sample_id>_recon`) as the Structured Grid to mask. Click OK.

Choose Structured Grid dialog

1. The volume is now masked — everything outside the cylinder is set to zero/background, leaving only the tissue within the 2 mm cylinder.

Masked result — cylindrical volume ready for segmentation

**Step 7: Clean up the workspace**

1. **Hide the Cylinder** object in the Data Properties panel (click its visibility eye icon) so it does not interfere with visualization.
2. **Use the masked volume for all subsequent segmentation** (Parts B through E).

> **Note:** This cylinder mask defines the analysis region for all structures (Parts B, C, and D). No additional ROI region definition is needed.

---

## Part B: Hair Segmentation

The standardized cylinder mask (A.6) defines the analysis region for all structures. No additional ROI is needed — segmentation is performed directly on the masked volume.

### B.1 Threshold Segmentation

1. Adjust the **Gamma** (Window Level) so internal structures are visible in the 3D view.
2. Select the masked volume (e.g., `<sample_id>_recon`) in the Data Properties panel.
3. Switch to the **Segment** tab in the left sidebar.
4. Check **Define range** to enable thresholding. Check **Show Histogram** and optionally **Log Y** to better visualize the histogram distribution.

Segment panel with Define Range, Show Histogram, and Log Y enabled

1. Set the threshold range for hair:
  - Consult previous sample ranges for reference values, but the **ground truth is visual**: move through all views and verify the selection captures the hair (bright circles in the cross-section) with minimal noise.
  - The hair cores are among the brightest structures. Drag the lower and upper limit sliders until hair-like structures are highlighted in the red overlay across all views.

Define Range applied — hair structures highlighted in red across all views

Define Range panel showing selected range values

1. Click **Add to New** to create a new ROI from the threshold selection.
2. Make the new ROI visible (click its eye icon) and enable **3D** view for it.
3. **Rename** the ROI to a short label: `H` (for Hair), `SG` (for SweatGlands), or `BV` (for BloodVessels). Use short names because this is the working ROI — the final Multi-ROI created later will get the full name.

### B.2 Clean the Hair Segmentation

The raw threshold will capture hair strands but also the epidermis (skin surface), sweat glands, blood vessels, and noise. These must be removed in stages.

**Stage 1: Cut Epidermis and Bottom Debris (Critical Step)**

The epidermis connects all hair strands at their roots. If left intact, Connected Components will count all hairs + epidermis as one single object. You also need to remove any structures below the hair zone (sweat glands, blood vessels, debris at the base).

ROI after thresholding — epidermis at top and bottom debris need removal

1. Go to the **Segment** tab, then select **ROI Painter**.
2. Configure the painter for bulk removal:
  - Select **Multi-slice** mode (applies edits across all slices at once).
  - Select the **square brush**.
  - Set brush **Size** to **350 pixels** (large enough for sweeping cuts).

ROI Painter settings — Multi-slice, square brush, size 350

1. Choose the **clearest lateral 2D view** (where epidermis and hair strands are most visible).
2. **Delete the bottom first**: position the brush below the hair zone, then **Shift + click** to erase everything beneath the hairs across all slices.
3. **Delete from the epidermis up**: identify the lowest point of the epidermis across all slices, then **Shift + click** above that line to remove the epidermis sheet and anything above it. Scroll through slices to find the lowest epidermis point before cutting — cut conservatively to avoid removing hair roots.

Lateral view showing where to cut — hair zone separated from epidermis and bottom

**Stage 2: 3D Cleanup of Remaining Particles**

1. Switch to the **3D view** and visually inspect the remaining ROI.
2. Small debris particles or edge artifacts may still be present. Use the **3D paint brush** tool to erase these directly in the 3D view.
3. Rotate the view to check all angles.

3D view after cleanup — only hair structures remain

**Stage 3: Remove Small Noise (Process Islands 3D)**

After the manual cuts, many small disconnected noise particles remain. Process Islands removes them automatically by voxel count.

ROI after manual cuts — top view showing remaining hair circles and scattered noise

> **IMPORTANT — Duplicate before running.** Process Islands modifies the ROI in place and **cannot be undone**. Right-click the ROI and duplicate it first as a backup.

1. Right-click the `H` ROI in the **Data Properties** panel.
2. Navigate to **Refine Region of Interest > Process Islands 3D**.

Right-click menu — Refine Region of Interest > Process Islands 3D

1. Select **Remove by Voxel Count (26-connected)**.

Process Islands 3D submenu — select Remove by Voxel Count (26-connected)

> **WARNING — Select REMOVE, not KEEP.** The submenu shows both "Remove by Voxel Count" and "Keep by Voxel Count" options side by side. Selecting "Keep" will have the **opposite** effect and delete your actual structures. Always confirm you selected **Remove**.

1. Enter a minimum voxel count of **150** (validated across multiple samples; real hair strands contain 3,000–15,000+ voxels, so 150 safely removes only small debris).
2. Click OK. The small noise particles disappear from the ROI.

**Stage 4: Optional Morphological Cleanup**

1. If small protrusions or bridges remain between hair strands, right-click the `Hair` ROI.
2. Select **Morphological Operations**.
3. Apply **Opening** (erosion followed by dilation) with kernel size 1-2 voxels.

### B.3 Connected Components Analysis (Count and Measure)

1. Right-click the cleaned `H` ROI in the **Data Properties** panel.
2. In the context menu, hover over **Connected Components 3D**.
3. Select **Create New Multi-ROI (26-connected)** to start.

Right-click menu — Connected Components 3D with 6-connected and 26-connected options

- **26-connected** (try first): considers face, edge, and corner neighbors. Works well when hairs are cleanly separated.
- **6-connected** (fallback): stricter connectivity — use if 26-connected merges distinct hairs that are touching.

1. Dragonfly creates a new Multi-ROI in the Data Properties panel. Each separate hair strand is labeled as an individual component with a unique color.
2. **Rename** this Multi-ROI to its final name: `Hair` (or `SweatGlands` or `BloodVessels`). This is the final result volume from which measurements will be computed.

**Evaluating the Multi-ROI — check for merged hairs**

Inspect the Multi-ROI in 3D. If multiple hairs share the same color, they are merged into one component. This is wrong and must be fixed.

Multi-ROI with merged hairs — several strands share the same color, and a blood vessel is visible

Two common causes and their fixes:

**Fix A — Epidermis remnants connecting hairs:**
Residual epidermis tissue at the top bridges adjacent hairs. Go back to the `H` ROI, use the ROI Painter to cut a little more off the top, then re-run Connected Components on the trimmed ROI.

**Fix B — Threshold range too wide:**
The range captured tissue between hair strands, fusing them. Go back to the **original standardized volume** and re-run Define Range with a **narrower range** (typically raise the lower bound) to isolate only the hair cores. Repeat the full cleanup and Connected Components on the new ROI.

> **Tip — Blood vessels may appear in the hair Multi-ROI.** In the image above, a blood vessel is visible among the hairs. This is a useful detection opportunity — note the BV for later segmentation, then remove it from the Hair Multi-ROI during cleanup.

This is an **iterative process**. Repeat the range adjustment until individual hairs are cleanly separated in the Multi-ROI.

**Example — iterative refinement on a sample:**

The initial range (10,308 – 19,474) produced excessive merging. Raising the lower bound to **11,075** resolved most fusions:

Refined range 11,075.44 – 19,474.38

Multi-ROI after refined range — much cleaner separation, a few remaining merged pairs and a visible BV

> **Accepting residual merged hairs.** After iterative refinement, a small number of merged pairs (2–3 groups out of 100+ hairs) is normal and acceptable. With sample sizes of 50–150+ hairs per sample, a handful of merged pairs has negligible impact on population-level statistics (mean diameter, count per area). You can either delete these merged groups during the Analyze step or keep them — the choice does not meaningfully affect the final results. Aim for the best practical separation, not perfection.

**Stage 5: Remove Non-Hair Components from the Multi-ROI**

> **Duplicate the Multi-ROI first.** Before any cleanup, create a copy of the Multi-ROI as a backup in case you accidentally remove something you wanted to keep.

After Connected Components, debris and non-hair structures (e.g., blood vessels) may appear as individual components. Clean them using the **Classes and scalar information** panel:

Classes and scalar information panel — each row is one component

1. In the **Data Properties** panel, scroll down to the **Classes and scalar information** section for the Multi-ROI.
2. Click the **teardrop icon** (selection tool) to enable interactive picking.
3. Click structures in the 3D view to identify them. Use **Ctrl + click** to select multiple components. Toggle **Hide** on selected classes to verify whether a structure is hair or debris before removing it.
4. **Extracting blood vessels**: If you identify a blood vessel among the hair components, select it, then right-click in the class list and choose **Extract Each Class as an ROI**. This creates a separate ROI for the BV that you can use later during blood vessel segmentation (Union multiple extracted BV ROIs together).

Right-click class menu — Extract Each Class as an ROI to save BV structures

1. After extracting the BV as a separate ROI, select those classes in the Multi-ROI and click **Remove** to delete them from the Hair Multi-ROI.
2. Continue reviewing and removing any remaining debris or non-hair components.

### B.4 Compute and Extract Measurements

**Step 1: Compute Measurements**

1. Right-click the Multi-ROI (e.g., `Hair`) in the Data Properties panel.
2. Go to **Measurements and Scalar Values > Compute Measurements**.

Right-click menu — Measurements and Scalar Values > Compute Measurements
3. A dialog will appear letting you select which metrics to calculate. Select **only** these specific items (do NOT check the entire "Basic Measurements" category -- that triggers dozens of expensive computations):
  **From 2D Measurements:**

- **2D Maximum Feret Diameter** -- the widest cross-sectional diameter. This is the primary "hair diameter" metric.
- **2D Area Equivalent Circle Diameter** -- diameter of a circle with the same cross-sectional area. Alternative diameter metric.
- **2D Minimum Feret Diameter** -- narrowest width; useful for checking if cross-sections are circular vs. elliptical.
  **From Basic Measurements (expand the category and check ONLY these):**
- **Volume** -- check this explicitly; useful for sorting and identifying noise during cleanup.
- **Equivalent Spherical Diameter** -- 3D volume-based diameter, useful as a reference.
- **Surface Area (voxel-wise)** -- the fastest of the three Surface Area options.
- **Sphericity** -- measures how round each component is (quality check: real hair should have moderate sphericity).
   **Do NOT check:** Feret 3D measurements (they give hair *length*, not diameter), Center of Mass, Bounding Box, or any other items in Basic Measurements.

1. Click **Compute**. On a clean Multi-ROI with ~350 components, this completes in seconds.

**Step 2: Analyze and Classify**

1. Right-click the same Multi-ROI again.
2. Go to **Measurements and Scalar Values > Analyze and Classify Measurements**.
3. This opens an interactive analysis window with tables showing all components and their computed measurements.

Analyze and Classify Measurements — table sorted by label, showing 144 hair components

1. Use the **visual batch deletion technique** (see below) to remove remaining debris:
  - **Sort the table by Volume** (ascending) so the smallest debris appears at the top.
  - In the **Opacity controls** at the bottom: reduce the **Complement** slider close to zero (structures you haven't selected become nearly invisible). Keep **Selected** at full opacity.
  - Enable **"Fit to view selection"** in Selection Tools — the 3D view zooms to each selected component.
  - Starting from the smallest-volume rows, **Ctrl + click** to select batches of debris. The 3D view highlights them at full opacity so you can confirm they are noise.
  - Click **Delete** to remove the selected batch. Repeat until only real hair structures remain.
2. After cleanup, note the **component count** shown at the top-right (e.g., "0 / 144") — this is the final hair count.

**Step 3: Export**

1. Right-click the Multi-ROI again.
2. Go to **Measurements and Scalar Values > Export Scalar Values...** to save all computed measurements as a CSV file.
3. **Important:** Make sure no individual row is selected before exporting -- if a single row is selected, only that row may be exported. Click an empty area in the table or press Ctrl+A to select all before exporting.
4. The exported CSV is semicolon-delimited (`;`) with the following columns:

  | Column                                  | Description                                         |
  | --------------------------------------- | --------------------------------------------------- |
  | Time Step                               | Always 0 (single time point)                        |
  | Label Index                             | Component number (1, 2, 3, ...)                     |
  | Name (NA)                               | Empty for auto-detected components                  |
  | 2D Area Equivalent Circle Diameter (mm) | Alternative diameter metric                         |
  | 2D Maximum Feret Diameter (mm)          | **Primary hair diameter**                           |
  | 2D Minimum Feret Diameter (mm)          | Narrowest cross-sectional width                     |
  | Volume (mm³)                            | 3D volume of the component                          |
  | Equivalent Spherical Diameter (mm)      | Diameter of a sphere with the same volume           |
  | Surface Area (voxel-wise) (mm²)         | Surface area of the component                       |
  | Sphericity                              | Roundness metric (0 to 1, where 1 = perfect sphere) |


### B.5 Export Hair Results

1. If you haven't already exported in B.5 Step 3: right-click the Multi-ROI, go to **Measurements and Scalar Values > Export Scalar Values...**
2. Save to: `<project_root>/03_RESULTS/Hair/<SampleID>_hair.csv`
3. This CSV contains one row per hair strand. The total number of data rows = **hair count**.
4. Take a **screenshot** of the final segmentation:
  - Show the 3D view with Hair ROI visible, plus one representative 2D slice.
  - Save to: `<project_root>/04_SCREENSHOTS/<SampleID>_hair.png`
5. Record the ROI area (mm^2) -- you will need this to calculate hair density (count / area).

### B.6 Update the Master CSV

After exporting the CSV, refresh the master measurements table:

```bash
python scripts/populate_master_csv.py \
  --results-dir <project_root>/03_RESULTS \
  --master-csv <project_root>/master_measurements.csv
```

After ~5–10 well-segmented samples, compile per-group reference ranges (hair count, mean 2D Max Feret Diameter, mean volume) for each experimental group in your own cohort. When a new sample's values fall outside those ranges, review the segmentation for potential issues (e.g., uncleaned debris inflating count, merged hairs reducing count, threshold too narrow reducing diameters). Minor deviations are expected due to biological variability between animals.


### B.7 Establishing Reference Ranges

Once ~10 samples have been segmented to acceptance, compute per-group ranges for hair count, mean 2D Max Feret Diameter, mean Equivalent Spherical Diameter, and mean volume. These ranges then serve as sanity checks for subsequent manual and DL-assisted segmentations. Expect some spread because of biological variability between animals and, if relevant, between breed or breed-composition groups.

**Physiological sanity check:** cattle body hair is typically reported in the 30–120 μm diameter range in the literature. Compare your per-sample means against this envelope when validating a new sample.

**Key workflow lesson:** Always clean the ROI (Stages 1–3) **before** running Connected Components. Running Connected Components on an uncleaned ROI produces hundreds of junk components and makes measurement computation extremely slow (20+ minutes instead of seconds).

---

## Part C: Sweat Gland Segmentation

Performed on the same sample, reusing the already-imported and aligned volume.

### C.1 Sweat Gland Segmentation Overview

The sweat gland workflow follows the same core steps as hair segmentation (Part B), with key differences noted below. Refer to Part B for detailed screenshots of shared steps (Define Range, ROI Painter, Process Islands, Connected Components, Compute Measurements, Analyze and Classify).

**Key differences from hair:**

- The threshold range uses **Invert** — sweat glands sit in a lower gray-value band than hair.
- Sweat glands are harder to separate; iterative range adjustment is more common.
- Both **6-connected and 26-connected** should be tested (see C.3).
- Blood vessels are often intertwined with sweat glands at similar gray levels — they may need to be extracted and segmented separately (see troubleshooting).
- The primary diameter metric is **Equivalent Spherical Diameter**, not 2D Maximum Feret Diameter.

### C.2 Threshold and ROI Creation

1. Select the standardized (masked) volume.
2. Go to **Segment > Define Range**. Enable **Show Histogram** and **Log Y**.
3. Set the threshold range to capture sweat gland structures. Sweat glands sit in a **lower gray-value band** than hair (typically 4,000–8,000 range vs 10,000+ for hair). Adjust the range visually until glands are highlighted without excessive dermal tissue.
4. Visually validate the range across all views, the same way as for hair: move through slices to confirm the selection captures gland structures without excessive noise.
5. Click **Add to New** to create the ROI. Rename it to `SG`.

### C.3 Cleanup

Follow the same cleanup stages as hair (Part B, B.2 Stages 1–4):

1. **ROI Painter cuts**: Use Multi-slice mode with a large square brush (350 px) to remove the epidermis, bottom debris, and anything clearly not sweat glands.
2. **3D brush cleanup**: Remove remaining edge artifacts in the 3D view.
3. **Process Islands 3D**: Duplicate the ROI first, then run **Remove by Voxel Count (26-connected)** with a threshold of **up to 50 voxels** (production value; conservative to preserve small glands).

**Connected Components — try both connectivity modes:**

Sweat glands benefit from testing both 6-connected and 26-connected before committing:

- **26-connected** (try first): Groups large debris clusters into single components, making bulk deletion easier. However, it may fuse adjacent glands.
- **6-connected** (use for final): Provides finer separation of individual glands, but fragments debris into many small components.

A practical workflow:

1. Run 26-connected first to identify and delete large debris clusters.
2. Then run 6-connected on the cleaned ROI for the final gland separation.

The visual difference between 6-connected and 26-connected results is usually dramatic for small, closely-spaced glands — inspect both on a representative slice before committing.

After Connected Components, rename the Multi-ROI to `SweatGlands`.

**Extracting blood vessels found in SG**: If blood vessels are visible among the sweat gland components (common — they share similar gray levels), select them in the Classes panel, right-click > **Extract Each Class as an ROI**, then **Remove** them from the SG Multi-ROI. Save these extracted BV ROIs for Part D.

### C.4 Compute, Analyze, and Clean

1. **Compute Measurements**: Same metrics as hair, with one addition:
  - **Equivalent Spherical Diameter** — this is the **primary sweat gland diameter metric** (not 2D Maximum Feret Diameter).
  - Also compute: Volume, Surface Area (voxel-wise), Sphericity, 2D Maximum Feret Diameter, 2D Area Equivalent Circle Diameter, 2D Minimum Feret Diameter.

> **Important: Why use Equivalent Spherical Diameter for sweat glands.** Sweat glands are 3D structures, not simple cross-sectional circles like hair. The Equivalent Spherical Diameter represents the diameter of a sphere with the same total volume, correctly capturing the full 3D extent of each gland.

1. **Analyze and Classify**: Use the same visual batch deletion technique as hair:
  - Sort by Volume ascending.
  - Reduce Complement opacity, keep Selected at 100%.
  - Enable "Fit to view selection."
  - Ctrl+click small debris, delete in batches.
  - Also check for non-gland structures (fat, tissue fragments) that survived thresholding.

### C.5 Export and Validate

1. Export CSV: **Measurements and Scalar Values > Export Scalar Values...**
2. Save to: `<project_root>/03_RESULTS/SweatGlands/<SampleID>_sg.csv`
3. Take a screenshot and save to: `<project_root>/04_SCREENSHOTS/<SampleID>_sweatglands.png`
4. Update the Master CSV:

```bash
python scripts/populate_master_csv.py \
  --results-dir <project_root>/03_RESULTS \
  --master-csv <project_root>/master_measurements.csv
```

### C.6 Establishing Reference Ranges

Once ~10 samples have been segmented to acceptance, compile per-group reference ranges for sweat-gland count, mean Equivalent Spherical Diameter, and mean/total volume. These serve as sanity checks for subsequent samples. Expect substantial biological variability — in our own cohort, groups that differed in *Bos indicus* composition also differed in sweat-gland morphology (fewer, larger glands vs. more numerous, smaller glands). Use per-group ranges rather than a single cohort-wide range once group differences are apparent.

**Key workflow lesson:** Sweat glands are the most labor-intensive structure to segment manually. With DL models, SG segmentation is usually fast but requires a **quality gate**: inspect results in 2D before accepting. If glands appear unusually small, sparse, or intricate, verify in 2D and consider manual re-segmentation — DL models can fail on atypical morphology (typically under-segmentation, not false positives).

---

## Part D: Blood Vessel Segmentation

Blood vessels are found through two methods: (1) dedicated thresholding on the masked volume, and (2) extraction from the SG Multi-ROI when BVs appear intertwined with sweat glands.

### D.1 Blood Vessel Segmentation Overview

The blood vessel workflow follows the same core steps as hair (Part B): Define Range, cleanup, Process Islands, Connected Components, Compute Measurements. Refer to Part B for detailed screenshots of shared steps.

**Key differences from hair and sweat glands:**

- BV gray-value ranges often overlap with both hair and SG. The range typically sits **between** the SG and hair bands (e.g., 5,000–12,000).
- BVs are frequently found **intertwined with sweat glands** at similar gray levels. When this happens, they are extracted from the SG Multi-ROI rather than segmented independently.
- Blood vessel counts are typically low (1–2 per sample) — each vessel is a large, branching structure.
- **Equivalent Spherical Diameter** is the primary size metric. Sphericity is characteristically very low (0.15–0.30) due to the elongated, branching morphology.
- Some BVs may be unsegmentable via thresholding (appearing hollow or open internally). Document these as skipped.

### D.2 Method A: Dedicated Thresholding

1. Select the standardized (masked) volume.
2. Go to **Segment > Define Range**. Enable **Show Histogram** and **Log Y**.
3. Set a threshold range for BV structures. Validate visually across all views.
4. Click **Add to New**, rename the ROI to `BV`.
5. Follow the same cleanup stages as hair (B.2): ROI Painter cuts, 3D brush cleanup, Process Islands (up to 50 voxels, 26-connected).
6. Run **Connected Components 3D** (26-connected or 6-connected). Rename the Multi-ROI to `BloodVessels`.

### D.3 Method B: Extract from SG Multi-ROI

Blood vessels frequently appear among sweat gland components because they share similar gray levels. When identified during SG cleanup:

1. In the SG Multi-ROI **Classes and scalar information** panel, select the BV component(s).
2. Right-click > **Extract Each Class as an ROI** to create a separate BV ROI.
3. **Remove** the extracted classes from the SG Multi-ROI.
4. If multiple BV ROIs were extracted (from different segmentation runs), **Union** them: convert all to binary ROIs first, then Union, then re-run Connected Components to generate clean labels.

### D.4 Compute, Analyze, and Export

1. **Compute Measurements**: Same metrics as hair and SG (Volume, Equivalent Spherical Diameter, Surface Area, Sphericity, 2D Feret diameters).
2. **Analyze and Classify**: Use the visual batch deletion technique to remove debris. BV components are large — debris is easily identified by volume.
3. **Export CSV**: save to `<project_root>/03_RESULTS/BloodVessels/<SampleID>_bv.csv`.
4. **Validate**: compare counts, volumes, and Equivalent Spherical Diameters against previously segmented samples from the same group.

### D.5 Sanity Checks for Blood Vessel Results

- Typical BV counts per sample are low (often 1–2, occasionally 0 or 3).
- Sphericity is characteristically very low (roughly 0.1–0.4) because BVs are elongated and heavily branched.
- Equivalent Spherical Diameter is the more stable size metric than 2D Feret for BVs.
- Samples where no BV can be reliably thresholded should be recorded as BV-absent rather than zero-valued gaps in the master CSV; document the reason (scan quality, morphology) in a per-sample note column.

---

## Part E: Sweat Gland Depth Measurement (Distance Map Method)

> **Status: Requires pilot test.** This workflow uses Dragonfly's Distance Map and "Basic Measurements with Dataset" features to compute the distance from each sweat gland to the epidermis surface. The workflow is based on confirmed Dragonfly 2024.1 documentation but requires validation on one sample before production use.

This measures the shortest surface-to-surface distance from the epidermis (skin surface) to each sweat gland. The per-gland depth values are exported alongside the regular SG measurements and aggregated into the Master CSV as `SG_Depth`.

### E.1 Segment the Epidermis Surface

The epidermis is the outermost skin layer — the bright, continuous horizontal band at the top of the biopsy.

1. Use the **cylinder-masked volume** (the same one used for SG segmentation in Part C).
2. Go to **Segment > Define Range**. Enable **Show Histogram** and **Log Y**.
3. Set a threshold range to isolate the epidermis layer:
  - The epidermis appears as the **brightest, most continuous horizontal band** near the top of the sample.
  - It has higher density than the underlying dermis tissue.
  - Typical threshold: the high end of the gray-value range (similar to or higher than hair tissue).
4. Click **Add to New** to create a new ROI. Rename it to `Epidermis`.
5. **Clean the segmentation:**
  - Run **Process Islands 3D** (up to 50 voxels, 26-connected) to remove small fragments.
  - Use **ROI Painter** in Multi-slice mode to erase any hair follicles or non-epidermis structures that were captured.
  - The goal is a **clean, continuous surface layer** representing the outer skin boundary.
6. **Verify in the 2D views:** The epidermis ROI should appear as a thin cap at the top of the cylinder, following the skin contour.

> **Tip:** If the epidermis is not clearly visible (e.g., the biopsy surface was damaged during collection), document the sample as "epidermis not segmentable" and skip Part E for that sample. Leave `SG_Depth` empty in the Master CSV.

### E.2 Create the Distance Map

1. In the **Data Properties and Settings** panel, right-click the `Epidermis` ROI.
2. Choose **Create Mapping Of > Distance Map**.
3. Dragonfly creates a new 3D floating-point volume where each voxel's value equals its distance (in mm, based on the voxel spacing) to the nearest epidermis voxel.
4. The Distance Map volume appears automatically in the Data Properties panel. Rename it to `Epidermis_DistanceMap` for clarity.
5. **Visual verification:** Apply a color map overlay to the Distance Map:
  - Regions near the epidermis should be **dark** (low distance values, near 0).
  - Deeper regions should be **bright** (higher distance values).
  - The sweat glands should appear at an intermediate depth (typically 0.2–1.5 mm from the surface).

> **Reference:** [Dragonfly Help — Creating Distance Maps](http://www.theobjects.com/dragonfly/dfhelp/2024-1/Content/ROIs%20and%20Multi-ROIs/Regions%20of%20Interest/Creating%20Distance%20Maps.htm)

### E.3 Compute Per-Gland Depth (Batch Method)

The key optimization: Dragonfly's **"Basic Measurements with Dataset"** feature computes per-component intensity statistics (Min, Mean, Max) for all components in a Multi-ROI simultaneously, using any volume as the intensity source. When the "dataset" is the Distance Map, "Min Intensity" = minimum distance from that gland to the epidermis = **SG_Depth**.

1. Right-click the `SweatGlands` Multi-ROI (the same one from Part C, after Connected Components and cleanup).
2. Go to **Measurements and Scalar Values > Compute Measurements**.
3. In the Compute Measurements dialog, expand **Basic Measurements with Dataset**.
4. In the **Dataset** dropdown, select `Epidermis_DistanceMap`. (Only volumes with the same shape as the Multi-ROI appear in this list.)
5. Check **Min Intensity** — this is the primary SG_Depth metric (closest point of each gland to the epidermis surface).
6. Optionally check:
  - **Mean Intensity** — average depth across all voxels in the gland.
  - **Max Intensity** — deepest point of the gland.
7. Click **Compute**. This runs for all gland components simultaneously — no need to process each gland individually.

> **Reference:** [Dragonfly Help — Basic Measurements with Dataset](https://www.theobjects.com/dragonfly/dfhelp/2024-1/Content/ROIs%20and%20Multi-ROIs/Multi-ROIs/Measurements%20and%20Scalar%20Data%20for%20Multi-ROIs/Basic%20Measurements%20with%20Dataset.htm)

### E.4 Export and Verify

1. The **Min Intensity** column now appears alongside the existing SG measurements in the **Analyze and Classify** table (right-click Multi-ROI > Measurements and Scalar Values > Analyze and Classify Measurements).
2. Export via **Measurements and Scalar Values > Export Scalar Values** to the standard SG CSV location:
  - `03_RESULTS/SweatGlands/<SampleID>_sg.csv`
3. The CSV now contains an additional column `Min Intensity` whose values are the per-gland depth in mm.
4. **Sanity check:** Values should be in the range **0.2–1.5 mm** (typical cattle SG depth from the literature):
  - If values are **0 or near 0**: Check that the Epidermis ROI does not overlap with the SweatGlands ROI.
  - If values are **very large (>2 mm)**: Check that the Epidermis ROI correctly captures the skin surface, not some deeper structure.
5. **Document** in the sample's logbook entry:
  - Whether epidermis segmentation was easy or difficult.
  - The mean SG_Depth for the sample.
  - Any anomalies observed.

### E.5 Consistency Rules for SG_Depth

Follow these rules to ensure comparable depth measurements across all samples:

1. **Reference surface:** Always use the **epidermis** (outermost bright band) as the reference surface, not the dermis/subdermis boundary.
2. **Primary metric:** Always use **Min Intensity** from the Distance Map as the SG_Depth metric. This measures the closest point of each gland to the epidermis surface.
3. **Same voxel grid:** The Distance Map must be created from the same cylinder-masked volume used for SG segmentation. The Multi-ROI and Distance Map must have the same shape (same voxel dimensions).
4. **Export alongside other SG metrics:** Run "Compute Measurements" with both the standard SG metrics (Volume, EqSphD, etc.) AND the Distance Map measurements (Min Intensity) in the same session, then export once. This ensures all metrics are in the same CSV row for each gland.
5. **Unsegmentable epidermis:** If the epidermis is not clearly visible in a sample (damaged biopsy surface, unusual scan angle), document the sample as "epidermis not segmentable" and leave `SG_Depth` empty in the Master CSV. Do not substitute an arbitrary reference surface.

### E.6 Script Integration

The `populate_master_csv.py` script is configured to read the `Min Intensity` column from the SG CSV and compute the mean depth across all glands:

```
SG_Depth = mean(Min Intensity for all glands)
```

If the `Min Intensity` column is not present in the CSV (i.e., Part E was not performed for that sample), `SG_Depth` is left empty.

### E.7 Pilot Test Checklist

Before using this workflow in production, validate it on one manually segmented sample:

- Epidermis ROI segments cleanly (continuous layer, no hair inclusions).
- Distance Map visual verification: dark near surface, bright deeper.
- Min Intensity values are physiologically plausible (0.2–1.5 mm range).
- Exported CSV column name matches what `populate_master_csv.py` expects (`Min Intensity`).
- If the column name differs, update the script's `sg_depth_col` variable.
- Update this protocol with any corrections after the pilot.

Once the pilot is successful, remove this checklist and update the status note at the top of Part E to "Validated."

---

## Part F: Save and Finalize

### F.1 Save the Dragonfly Session

1. **File > Save Session**.
2. Save to: `<project_root>/02_DRAGONFLY_PROJECTS/<SampleID>_session`
3. Dragonfly saves the entire project state: all imported volumes, all ROIs, all segmentations, and all analysis results. You can reload this session at any time to review or modify the work.

### F.2 Summary Checklist per Sample

Before moving to the next sample, verify you have:


| Item                                                 | Location                                     |
| ---------------------------------------------------- | -------------------------------------------- |
| Hair CSV (count, per-strand diameter, mean diameter) | `<project_root>/03_RESULTS/Hair/<SampleID>_hair.csv`        |
| Sweat gland CSV (count, per-gland diameter)          | `<project_root>/03_RESULTS/SweatGlands/<SampleID>_sg.csv`   |
| Blood vessel CSV (count, per-vessel diameter)        | `<project_root>/03_RESULTS/BloodVessels/<SampleID>_bv.csv`  |
| Hair screenshot                                      | `<project_root>/04_SCREENSHOTS/<SampleID>_hair.png`         |
| Sweat gland screenshot                               | `<project_root>/04_SCREENSHOTS/<SampleID>_sweatglands.png`  |
| Blood vessel screenshot                              | `<project_root>/04_SCREENSHOTS/<SampleID>_bloodvessels.png` |
| Dragonfly session file                               | `<project_root>/02_DRAGONFLY_PROJECTS/<SampleID>_session`   |


### F.3 Update the Master CSV

The Master CSV (`<project_root>/master_measurements.csv`) aggregates summary statistics from all per-sample CSVs. Update it with:

```bash
python scripts/populate_master_csv.py \
  --results-dir <project_root>/03_RESULTS \
  --master-csv <project_root>/master_measurements.csv
```

This script reads all Hair, SG, and BV CSVs and populates the corresponding columns in the Master CSV. See Protocol 04 (`04_Data_Management_and_Scripts.md`) for details on the script and column mapping.

**Group / breed codes**: Record whichever metadata your study stratifies on (breed, herd, treatment group) in a dedicated column of the master CSV. The script does not interpret these codes; consistency is the only requirement.

Recording a group label enables group-stratified analysis and group-aware AI model training, since hair density, diameter, and sweat-gland morphology can differ systematically between groups.

---

## Timing Estimates

### Manual segmentation (Protocol 02 only)


| Step                         | Estimated Time (first few samples) | After practice |
| ---------------------------- | ---------------------------------- | -------------- |
| A. Import, align, setup      | 5-10 min                           | 3-5 min        |
| B. Hair segmentation         | 15-25 min                          | 10-15 min      |
| C. Sweat gland segmentation  | 20-30 min                          | 15-20 min      |
| D. Blood vessel segmentation | 25-40 min                          | 20-30 min      |
| E. Dermis-to-SG distance     | 10-15 min                          | 5-10 min       |
| F. Save and export           | 5-10 min                           | 3-5 min        |
| **Total per sample**         | **80-130 min**                     | **55-85 min**  |


### DL-assisted production workflow (Protocol 03)

Once trained DL models are available, production segmentation typically combines DL-based Hair and SG with manual BV. Expected per-sample timing:


| Sample profile              | Typical time | Speedup vs manual | Notes                                             |
| --------------------------- | ------------ | ----------------- | ------------------------------------------------- |
| Clean (no fusions)          | ~12–16 min   | 4–6×              | Best case: zero hair fusions, fast SG cleanup     |
| Moderate (minor fusions)    | ~15–25 min   | 2.5–4×            | Some 6-connected cleanup or moderate hair fusions |
| Heavy fusions               | ~24–32 min   | 2–3×              | May require full manual hair re-segmentation      |
| **Typical average**         | **~15–20 min** | **~3×**         |                                                   |


Track per-sample timing and failure modes in your own progress log; the format described in Protocol 04 Part E is compatible with `scripts/rebuild_production_csv.py`.

---

## Consistency Rules

Follow these rules across ALL samples to ensure reproducible, publication-quality data:

1. **Diameter metric is structure-specific** (validated across 10 samples):
  - **Hair**: Use **2D Maximum Feret Diameter** (hair cross-sections are well-defined circles; 2D Feret is accurate and meaningful).
  - **Sweat Glands**: Use **Equivalent Spherical Diameter** (the 3D volume-based diameter correctly captures the full gland size).
  - **Blood Vessels**: Use **Equivalent Spherical Diameter** (BVs are large, branching 3D structures).
  - Once chosen per structure, use the same metric consistently across ALL samples.
  - **Known issue — hairs with 2D Feret = 0**: Some hair components return a 2D Maximum Feret Diameter of 0.0 mm. This is a **2D measurement limitation, not a segmentation quality issue**. These components are still real hairs and should be **kept for hair count** (do not delete them). When reporting:
    - **Hair count** = total number of components (including Feret = 0).
    - **Mean hair diameter** = average of **only the nonzero** 2D Max Feret values.
    - **Record how many components had Feret = 0** (e.g., "Mean diameter from 94/127 measurable components").
    **Why Feret = 0 occurs**: The 2D Feret Diameter is measured from a single cross-sectional slice. When a hair's footprint in that slice is too small, the software cannot compute a reliable measurement and returns 0. This can happen for multiple reasons:
    - **Threshold-related thinning**: raising the lower threshold to separate fused hairs can make some components too thin in 2D (the original documented cause).
    - **Hair orientation**: hairs tilted away from perpendicular relative to the scan plane have smaller 2D cross-sections even though their 3D volume is normal.
    - **Hair tapering**: the 2D measurement may be taken at a point where the hair tapers, rather than at its widest cross-section.
    - **Individual morphology**: some samples with large, well-segmented hairs still show high Feret=0 rates even when fusions are minimal, because the 2D slice where the measurement is taken may not coincide with the hair's widest section.
    **Typical production behavior**: Feret=0 rates can range from single-digit percentages to over 20% depending on sample morphology. High rates do NOT indicate bad segmentation — the 3D metrics (EqSphD, Volume) are unaffected because they use the full voxel volume of each hair. The Feret=0 rate is a secondary descriptor of 2D measurement reliability, not a quality gate.
2. **Connected Components connectivity**: Start with **26-connected** for hair. For sweat glands, test **both** 6-connected and 26-connected — use 26-connected for bulk debris removal, then 6-connected for final gland separation. Document which was used.
3. **Standardize the analysis region**: Apply the same fixed-diameter cylinder mask (A.6, radius = 1 mm) to every sample before segmentation.
4. **Process Islands threshold**: Use **up to 50 voxels** (26-connected) for all structures. This is the production value, intentionally conservative to avoid deleting very small hair or sweat-gland components. (The 150-voxel value listed in older logbook entries applies only to the first two training samples.)
5. **Voxel spacing**: Verify 0.00784727 mm in X, Y, Z for every import. If a sample has a different voxel size, record the difference.
6. **Duplicate before destructive operations**: Always duplicate an ROI before running Process Islands or other irreversible operations.
7. **Save frequently**: Save the Dragonfly session after each major cleanup step. ROI Painter operations cannot be undone with Ctrl+Z.
8. **Screenshots**: Always include the sample ID and structure name visible in the Dragonfly window title or as an overlay annotation.
9. **Record metadata when known**: Populate group / breed / treatment columns in the master CSV from your own study's animal list. Keep the mapping between the short `Sample_ID` used here and any external animal identifier in your own records.

---

## Troubleshooting


| Problem                                                             | Solution                                                                                                                                                                                                                                                                                                                  |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Threshold captures too much non-hair tissue                         | Narrow the threshold range (increase lower limit). Try Upper Otsu as a starting point.                                                                                                                                                                                                                                    |
| Hair strands appear merged into one component                       | Raise the lower threshold bound (e.g., from ~10,000 to ~11,000–12,000) to select only the bright core of each hair. This is the most effective fix. Also check for residual epidermis connecting hairs at the top — cut more with ROI Painter if needed.                                                                  |
| Many hair components have 2D Max Feret = 0                          | Normal — occurs due to threshold thinning, hair orientation, or tapering (not just after raising threshold). Can reach 18–23% even on well-segmented samples. Keep these components for count; report mean Feret from nonzero values only; record the fraction with Feret = 0. See "Known issue" in Best Practices above. |
| Sweat glands appear as one fused mass                               | The threshold range is too broad. Narrow it iteratively until individual glands separate. Try both 6-connected and 26-connected Components to find better separation.                                                                                                                                                     |
| Blood vessel unsegmentable (appears hollow/open)                    | Some BVs cannot be captured via thresholding due to internal morphology. Document as skipped in your per-sample notes.                                                                                                                                                                                                    |
| Blood vessel intertwined with sweat glands at same gray level       | Extract the BV+gland cluster from the SG Multi-ROI, run 6-connected Components to separate them, create a binary ROI of the rescued glands, Union it back into the SG binary ROI, then re-run 26-connected Components.                                                                                                    |
| Boolean Union of two Multi-ROIs merges/corrupts labels              | **Never Union Multi-ROIs directly.** Convert both to binary ROIs first, Union the binary ROIs, then re-run Connected Components to generate fresh labels.                                                                                                                                                                 |
| Connected Components finds thousands of tiny objects                | Run Process Islands (up to 50 voxels, 26-connected) before Connected Components. Also use the visual batch deletion technique in Analyze and Classify to remove remaining debris.                                                                                                                                         |
| Measurements take 20+ minutes to compute                            | Clean the ROI first (Process Islands, erase debris) BEFORE running Connected Components. Uncleaned ROIs produce hundreds of junk components.                                                                                                                                                                              |
| ROI Painter edit cannot be undone (Ctrl+Z)                          | Dragonfly does not reliably undo brush operations. **Duplicate the ROI before destructive operations.** Save the session frequently.                                                                                                                                                                                      |
| CSV export contains only 1 row                                      | Deselect all rows before exporting (click empty area or Ctrl+A). A single selected row may limit the export to that row.                                                                                                                                                                                                  |
| Accidentally selected KEEP instead of REMOVE in Process Islands     | The ROI is now destroyed (only noise remains). Restore from the duplicate you created before running Process Islands.                                                                                                                                                                                                     |
| Dragonfly crashes or runs slowly                                    | Reduce the working volume by cropping to just the ROI region before running analysis. Close other applications to free RAM.                                                                                                                                                                                               |
| Samples have different physical diameters                           | Apply the standardized cylinder mask (A.6) before segmentation to ensure all samples are analyzed over the same area.                                                                                                                                                                                                     |
| AI segmentation produces fused/merged objects (cannot re-threshold) | Use the **Extract → Separate → Re-import** workflow described in Appendix A below. This avoids the need to revert to the original recon volume.                                                                                                                                                                           |


---

## Appendix A: Separating Fused Objects from AI Segmentation Results

When the AI model produces a Multi-ROI where two or more structures (sweat glands or hair follicles) are fused into a single labeled class, they cannot be separated by re-running Define Range on the original reconstruction volume. The following workflow separates them entirely within the Multi-ROI domain.

**Applies to**: Sweat glands, hair follicles, or any structure fused after AI prediction and Connected Components analysis.

### Step 1 — Extract the fused class as an ROI

1. In the **Classes and scalar information** panel of the original Multi-ROI, select the fused class (the label containing 2+ merged structures).
2. Right-click → **Extract Class as an ROI**.
3. A new standalone ROI appears in the Data Properties panel containing only the voxels from that fused class.

### Step 2 — Separate via Connected Components

1. Right-click the extracted ROI.
2. Select **Separate Connected Components (6-connected)** (or 26-connected — try 6-connected first for finer separation).
3. Dragonfly creates a **new Multi-ROI** where each disconnected region is labeled as a distinct class.
4. Verify in 3D that the structures are now properly split (each one has a different color).

> **Note**: This works because the fused structures typically share only a thin bridge of voxels. The 6-connected criterion (face-adjacent only) breaks connections that 26-connected (face + edge + corner) would preserve.

### Step 3 — Convert the split Multi-ROI into individual ROIs

1. Right-click the **new Multi-ROI** (the split result from Step 2) in the Data Properties panel.
2. Select **Extract ROIs** from the pop-up menu.
3. This creates one separate ROI object per separated structure (e.g., 3 fused glands → 3 individual ROIs).

### Step 4 — Remove the fused class from the original Multi-ROI

1. Go back to the **original Multi-ROI**.
2. In the Classes and scalar information panel, right-click the fused class → **Delete Class** (or **Clear Class**).
3. This removes the fused label, freeing those voxels.

### Step 5 — Import each separated ROI as a new class

For each individual ROI created in Step 3:

1. In the original Multi-ROI's Classes and scalar information panel, **Add** a new class (click Add → Add Class).
2. Right-click the new class → **Import ROI...**.
3. Select the corresponding separated ROI from Step 3.
4. The voxels from that ROI are labeled as the new class.

Repeat for all separated ROIs.

### Step 6 — Clean up temporary objects

Once all separated structures are confirmed in the original Multi-ROI:

1. Delete the standalone ROI from Step 1.
2. Delete the split Multi-ROI from Step 2.
3. Delete the individual ROIs from Step 3.
4. Re-run **Compute Measurements** on the original Multi-ROI to update all scalar values.

### Quick reference


| Step | Action                   | Dragonfly menu path                                           |
| ---- | ------------------------ | ------------------------------------------------------------- |
| 1    | Extract fused label      | Classes panel → right-click class → Extract Class as an ROI   |
| 2    | Separate                 | Right-click ROI → Separate Connected Components (6-connected) |
| 3    | Split to individual ROIs | Right-click new Multi-ROI → Extract ROIs                      |
| 4    | Remove fused label       | Classes panel → right-click class → Delete Class              |
| 5    | Import each part back    | Classes panel → Add Class → right-click → Import ROI...       |
| 6    | Clean up                 | Delete temporary ROIs and Multi-ROI                           |


> **When this may not work**: If the fused structures are truly contiguous (no thin bridge — they overlap volumetrically), Connected Components will still see them as one object. In that case, use **ROI Painter** to manually draw an erase line through the fusion point before running Connected Components, or apply a light **Erosion** (1–2 voxels) to break the bridge, then separate, then **Dilate** back to restore size.

### Batch variant: A - B → Union (multiple fused objects at once)

When a Multi-ROI contains **many** fused classes, the per-class Steps 1–5 above become tedious. Use this streamlined batch approach instead:

1. In the **Analyze and Classify Measurements** panel, select all fused classes and extract them together as a **single new Multi-ROI**. Do **not** remove them from the original Multi-ROI.
2. On the new Multi-ROI, run **Separate Connected Components (6-connected)**. For any classes where 6-connected doesn't split them, extract those individually as ROIs and separate manually (ROI Painter erase or further 6-connected).
3. **Union** all separated ROIs and Multi-ROIs into one clean Multi-ROI where every structure is its own class.
4. Merge with the original using **two Boolean operations** (select both Multi-ROIs in the Data Properties panel):
  - **A - B** where A = original Multi-ROI, B = new separated Multi-ROI. This removes the old fused labels from exactly the voxels now covered by the separated labels.
  - **Union** the A - B result with the separated Multi-ROI. This combines the cleaned original (non-fused glands) with the properly separated glands.
5. The result is a single Multi-ROI with no double-counting: every gland is its own class.
6. Delete all intermediate objects. Re-run **Compute Measurements** on the final Multi-ROI.

> **Why A - B then Union?** A straight Union would keep the old fused label on overlapping voxels, losing the separation work. A - B first punches out the fused areas; Union then fills them back with the separated classes.

---

## Notes

- This protocol produces the same measurements as the original VGStudio MAX protocol (hair count/diameter, sweat gland count/diameter, blood vessel count/diameter) but uses Dragonfly's thresholding, morphological operations, and connected components tools to significantly reduce manual effort.
- Hair segmentation (Part B) is typically completed first, as blood vessels are sometimes discovered and extracted during hair or SG cleanup.
- After completing ~10 well-segmented samples with this manual protocol, proceed to **Protocol 03** (`03_AI_Segmentation_Wizard_Automation.md`) to train Dragonfly's Segmentation Wizard for semi-automated processing of the remaining samples.
- If two operators segment on separate machines, cross-validate a shared sample before merging training sets and agree on conventions (threshold-selection criterion, how to handle edge cases, naming) up front.
- Threshold ranges are sample-dependent and must be visually validated for each sample. Process Islands threshold (up to 50 voxels) can be kept fixed across all samples.