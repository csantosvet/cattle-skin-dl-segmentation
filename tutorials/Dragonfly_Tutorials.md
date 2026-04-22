# Dragonfly Video Tutorials & Learning Resources

Curated list of Dragonfly video tutorials and written resources for operators running the bovine skin micro-CT segmentation pipeline.
Watch in the order listed -- each video builds on skills from the previous ones.

---

## Phase 1: Core Skills (Watch Before Starting Manual Segmentation)

### 1. Porosity Analysis Webinar (March 2025)

- **URL**: [https://www.youtube.com/watch?v=aQqSDJLiIqE](https://www.youtube.com/watch?v=aQqSDJLiIqE)
- **Duration**: ~1 hour
- **Presenter**: Prof. Anton du Plessis (Comet Technologies)
- **Audio**: Yes (fully narrated)
- **Topics covered**:
  - Manual and automated (Otsu) thresholding
  - Pore size distributions and statistical data extraction
  - AI-driven segmentation methods
  - 3D vs 2D analysis
  - Visualization and export of results
- **Why watch this**: The porosity workflow (threshold → clean → connected components → count → measure diameter) is essentially identical to our hair segmentation pipeline. This is the single best end-to-end walkthrough of the analysis type we need.
- **Maps to plan steps**: 5.3 (Threshold), 5.4 (Clean), 5.5 (Count & Measure)

---

### 2. Dragonfly Daily 21 -- Objects Analysis

- **URL**: [https://www.youtube.com/watch?v=AjmhMqn7V58](https://www.youtube.com/watch?v=AjmhMqn7V58)
- **Duration**: ~30 minutes
- **Presenter**: Mike Marsh (Dragonfly Product Manager)
- **Audio**: Yes (narrated)
- **Topics covered**:
  - Connected Components Analysis (counting individual objects)
  - Shape-based measurements (Feret diameter, equivalent diameter, volume, surface area)
  - Intensity-based measurements
  - Coloring objects by measurement values
  - Interactive selection from 2D views, 3D views, histograms, and tables
  - Hierarchical subgroup analyses
  - Exporting selections, groups, or full tables to CSV/Excel
- **Why watch this**: This is the most critical video for our workflow. It teaches exactly how to count hair/glands/vessels and measure their diameters after segmentation.
- **Maps to plan steps**: 5.5 (Count & Measure Hair), 6.4 (Count & Measure Sweat Glands), 7.4 (Count & Measure Blood Vessels)

---

### 3. Crack Identification and Segmentation (How-To)

- **URL**: [https://www.youtube.com/watch?v=648R-rjHr2Q](https://www.youtube.com/watch?v=648R-rjHr2Q)
- **Duration**: ~10-15 minutes
- **Presenter**: ORS / Dragonfly team
- **Audio**: Yes (narrated)
- **Topics covered**:
  - Defining a Region of Interest (ROI)
  - Applying threshold segmentation
  - Cleaning the segmentation result
  - Practical end-to-end segmentation workflow
- **Why watch this**: Quick, practical walkthrough of the ROI → threshold → clean pipeline. The subject is cracks (not biological tissue), but the tools and steps are identical to what we use for hair.
- **Maps to plan steps**: 5.2 (Define ROI), 5.3 (Threshold), 5.4 (Clean)

---

## Phase 2: AI & Automation (Watch After Completing ~5 Manual Samples)

### 4. Dragonfly Daily 17 -- Image Segmentation with Deep Learning

- **URL**: [https://www.youtube.com/watch?v=8g7uT7ZiOjk](https://www.youtube.com/watch?v=8g7uT7ZiOjk)
- **Duration**: ~30 minutes
- **Presenter**: Mike Marsh (Dragonfly Product Manager)
- **Audio**: Yes (narrated)
- **Topics covered**:
  - AI Segmentation Wizard
  - Training a deep learning model from manually labeled slices
  - Applying trained models to new data
  - Semi-automated segmentation workflow
- **Why watch this**: This is the technique that will eventually let you process samples in minutes instead of hours. Your manual segmentations from Phase 1 become the training data.
- **Maps to plan step**: 10 (AI Automation)

---

### 5. Turbine Blade Segmentation with Deep Learning (How-To)

- **URL**: [https://www.youtube.com/watch?v=81bDOI8Np_8](https://www.youtube.com/watch?v=81bDOI8Np_8)
- **Duration**: ~10-15 minutes
- **Presenter**: ORS / Dragonfly team
- **Audio**: Yes (narrated)
- **Topics covered**:
  - Smartgrid / super-pixel tool for efficient labeling
  - Training a U-net deep learning model
  - Applying the model to segment remaining data
  - Comparison of manual vs automated results
- **Why watch this**: Shows the practical deep learning workflow end-to-end. Demonstrates how a model trained on a few slices can segment an entire volume automatically.
- **Maps to plan step**: 10 (AI Automation)

---

### 6. ML Segmentation of a 3-Horned Chameleon (Workshop 2022)

- **URL**: [https://www.youtube.com/watch?v=XWafhfUhK5g](https://www.youtube.com/watch?v=XWafhfUhK5g)
- **Duration**: Workshop length (~30-60 min)
- **Presenter**: Dragonfly workshop team
- **Audio**: Yes (workshop recording)
- **Topics covered**:
  - Machine learning segmentation on biological micro-CT data
  - Distinguishing different tissue types in a 3D scan
  - Training and applying ML models to animal tissue
- **Why watch this**: The closest example to bovine skin biopsies -- biological tissue scanned with micro-CT and segmented with ML. Shows that the approach works on biological samples.
- **Maps to plan step**: 10 (AI Automation)

---

## Phase 3: Workflow Optimization (Watch When Ready to Scale)

### 7. Dragonfly Daily 35 -- Workflows, Wizards, and Reports

- **URL**: [https://www.youtube.com/watch?v=LXzewzFHq4A](https://www.youtube.com/watch?v=LXzewzFHq4A)
- **Duration**: ~30 minutes
- **Presenter**: Mike Marsh (Dragonfly Product Manager)
- **Audio**: Yes (narrated)
- **Topics covered**:
  - Creating automated workflows
  - Using built-in wizards
  - Generating analysis reports
  - Batch processing strategies
- **Why watch this**: Once you have a working manual protocol and a trained AI model, this video teaches you how to create repeatable automated workflows for processing all remaining samples.
- **Maps to plan step**: 10 (AI Automation / Batch Processing)

---

## Supplementary Videos

### Image Import in Dragonfly

- **URL**: [https://www.youtube.com/watch?v=S1aqM-aRZQA](https://www.youtube.com/watch?v=S1aqM-aRZQA)
- **Audio**: Yes (narrated)
- **Topics**: Loading data, navigating the 3D viewer, interface basics
- **Note**: You have already completed the import step, but useful for reference.

### Interpolating Features on ROIs

- **URL**: [https://www.youtube.com/watch?v=CeWqaz3LqQw](https://www.youtube.com/watch?v=CeWqaz3LqQw)
- **Audio**: Yes (narrated)
- **Topics**: Labeling a few slices and letting Dragonfly interpolate the segmentation across gaps
- **Note**: Time-saving technique for manual cleanup.

### View a 3D micro-CT image of a mouse (hide/remove the bed)

- **URL**: [https://www.youtube.com/watch?v=AvZiU6Iwuqo](https://www.youtube.com/watch?v=AvZiU6Iwuqo)
- **Audio**: NO SOUND (intentionally silent)
- **Topics**: ROI creation, manual brushes, thresholding, boolean operators, morphological operators, Point & Click tool
- **Note**: Covers many relevant basics but has no narration. Use the Porosity Webinar (#1) and Crack Segmentation (#3) as narrated replacements. Can still be useful to watch on mute alongside the written docs below.

### Dragonfly Software Showcase (3 minutes)

- **URL**: [https://www.youtube.com/watch?v=jAlXONZ92Hg](https://www.youtube.com/watch?v=jAlXONZ92Hg)
- **Audio**: Yes
- **Topics**: Quick overview of all Dragonfly capabilities
- **Note**: Good for a high-level orientation of what the software can do.

---

## Full Playlist

All 40+ Dragonfly Daily episodes:
[https://www.youtube.com/playlist?list=PLbYyniU4wPOtHGT0m68liH5SntwfETKsP](https://www.youtube.com/playlist?list=PLbYyniU4wPOtHGT0m68liH5SntwfETKsP)

---

## Official Written Documentation

For step-by-step instructions with screenshots (useful alongside the videos):


| Topic                       | URL                                                                                                                                                                                                                                                                        |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Threshold Segmentation      | [http://www.theobjects.com/dragonfly/dfhelp/2024-1/Content/Segmentation%20Tools/Creating%20Threshold%20Segmentations.htm](http://www.theobjects.com/dragonfly/dfhelp/2024-1/Content/Segmentation%20Tools/Creating%20Threshold%20Segmentations.htm)                         |
| ROI Tools                   | [https://www.theobjects.com/dragonfly/dfhelp/2020-1/Content/Segmentation/ROI%20Tools.htm](https://www.theobjects.com/dragonfly/dfhelp/2020-1/Content/Segmentation/ROI%20Tools.htm)                                                                                         |
| Intensity Ranges            | [https://www.theobjects.com/dragonfly/dfhelp/3-5/Content/07_Segmentation/Working%20with%20Intensity%20Ranges.htm](https://www.theobjects.com/dragonfly/dfhelp/3-5/Content/07_Segmentation/Working%20with%20Intensity%20Ranges.htm)                                         |
| Connected Components        | [https://www.theobjects.com/dragonfly/dfhelp/2024-1/Content/ROIs%20and%20Multi-ROIs/Multi-ROIs/Connected%20Components%20Analysis.htm](https://www.theobjects.com/dragonfly/dfhelp/2024-1/Content/ROIs%20and%20Multi-ROIs/Multi-ROIs/Connected%20Components%20Analysis.htm) |
| Segmentation Tools Overview | [https://www.theobjects.com/dragonfly/dfhelp/2022-2/Content/Segmentation%20Tools/About%20Dragonfly%27s%20Segmentation%20Tools.htm](https://www.theobjects.com/dragonfly/dfhelp/2022-2/Content/Segmentation%20Tools/About%20Dragonfly%27s%20Segmentation%20Tools.htm)       |


