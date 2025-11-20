---
title: "FluoTrack: Automated Multi-Target Fluorescence Tracking with Adaptive Detection"

tags:
  - Python
  - fluorescence microscopy
  - multi-target tracking
  - image analysis
  - bioimaging
  - photobleaching
  - Hungarian algorithm

authors:
  - name: Dongqi Liu
    orcid: 0009-0006-4018-9292
    affiliation: "1"

affiliations:
  - name: Department of Biology, University of North Carolina at Chapel Hill, USA
    index: 1

date: 19 November 2025
bibliography: paper.bib
---

# Summary

Fluorescent proteins have revolutionized cell biology by enabling real-time visualization of cellular processes. Quantitative tracking of multiple fluorescent spots is essential for understanding protein dynamics, molecular interactions, and cellular responses to stimuli. However, existing tools often require manual annotation of each target, lack automated multi-target tracking capabilities, or cannot provide both individual and population-level analyses simultaneously. `FluoTrack` addresses these limitations by providing an open-source Python package that combines adaptive multi-spot detection with robust tracking using the Hungarian algorithm, enabling automated analysis of multiple fluorescent signals with minimal user intervention.

# Statement of Need

Live-cell fluorescence microscopy generates time-lapse data containing multiple dynamic fluorescent signals requiring quantitative analysis. Researchers need computational tools that can:

1. **Automatically detect multiple fluorescent spots** without manual annotation of each target
2. **Track individual spots across frames** while maintaining unique identities despite movement, transient disappearance, or photobleaching
3. **Quantify photobleaching for each spot** to enable proper normalization and kinetic analysis
4. **Provide both individual and population-level statistics** to capture heterogeneous dynamics
5. **Process data efficiently** to enable analysis of large time-series datasets

Existing tools have significant limitations. ImageJ/Fiji [@Schindelin2012] and its TrackMate plugin [@Tinevez2017] require extensive manual parameter tuning for each dataset and focus primarily on post-acquisition analysis. Commercial microscope software typically tracks only single targets or requires manual region-of-interest definition. CellProfiler [@Carpenter2006], while powerful for high-throughput cellular phenotyping, is not optimized for sub-cellular fluorescent spot tracking with frame-to-frame identity preservation.

`FluoTrack` addresses these limitations through three key innovations:

1. **Adaptive multi-spot detection**: Automatically identifies all fluorescent spots above background using robust local statistics (median and MAD-based thresholding), eliminating manual parameter selection across varying imaging conditions

2. **Optimal tracking algorithm**: Employs the Hungarian algorithm [@Kuhn1955] for optimal spot-to-track assignment between consecutive frames, minimizing total distance while gracefully handling spot appearances, disappearances, and transient occlusions

3. **Dual-level analysis**: Provides comprehensive statistics for both individual spots (photobleaching rates, displacement, velocity) and population ensembles (collective dynamics, heterogeneity quantification), enabling insights impossible with single-level analysis alone

These capabilities make `FluoTrack` particularly valuable for applications including FRAP (fluorescence recovery after photobleaching) experiments with multiple bleach spots, protein translocation studies, chromatin dynamics analysis, and any research requiring simultaneous tracking and quantification of multiple fluorescent targets.

# Key Features

- Adaptive multi-spot detection using robust statistical methods (median/MAD-based thresholding)
- Hungarian algorithm for optimal frame-to-frame spot assignment
- Automatic handling of spot appearances, disappearances, and photobleaching
- Per-spot photobleaching quantification with half-life estimation
- Trajectory analysis: displacement, velocity, confinement radius
- Population-level statistics and dual-level (individual + ensemble) analysis
- Automated CSV export and publication-ready visualization

# Implementation

`FluoTrack` is implemented in Python 3.8+ using NumPy [@Harris2020], OpenCV [@Bradski2000], SciPy [@Virtanen2020], Matplotlib [@Hunter2007], and Pandas [@McKinney2010]. The modular architecture consists of three components:

**Detection:** Uses median and Median Absolute Deviation (MAD) for robust spot detection, adapting to varying background levels without manual parameter tuning.

**Tracking:** Implements the Hungarian algorithm [@Kuhn1955; @Munkres1957] for optimal spot-to-track assignment between frames, minimizing total distance while handling spot appearances and disappearances.

**Analysis:** Computes photobleaching half-life via exponential decay fitting, trajectory metrics (displacement, velocity, confinement), and population-level statistics, providing both individual and ensemble insights.

# Validation

`FluoTrack` was validated using synthetic time-lapse data (50 frames, 5 fluorescent spots) with random walk motion, heterogeneous photobleaching, transient disappearances, and realistic noise. The software successfully tracked all spots with no identity switches, correctly identified photobleaching in 5.5% of track segments, and achieved 45 frames/second processing speed on standard hardware. Figures show individual and population-level intensity dynamics (\autoref{fig:intensity}) and spatial trajectories (\autoref{fig:trajectories}).

![**Figure 1.** Individual (top) and population-level (bottom) intensity dynamics.\label{fig:intensity}](figures/intensity_trends.png)

![**Figure 2.** Multi-target spatial trajectories.\label{fig:trajectories}](figures/trajectories.png)

# Research Applications

`FluoTrack` supports multi-spot FRAP experiments, protein translocation studies, chromatin dynamics, organelle transport, and optogenetic stimulation monitoring. It enables quantification of heterogeneity, detection of rare events, correlation of multi-target behaviors, and model validation.

# Comparison with Existing Tools

| Feature | FluoTrack | ImageJ/Fiji + TrackMate | CellProfiler |
|---------|-----------|-------------------------|--------------|
| Multi-spot detection | Automatic | Manual ROI or automatic | Automatic |
| Tracking algorithm | Hungarian | LAP framework | LAP framework |
| Individual spot analysis | ✓ | ✓ | Limited |
| Population statistics | ✓ | Manual aggregation | ✓ |
| Photobleaching quantification | Automatic | Manual | ✗ |
| Python API | ✓ | Limited (ImageJ macros) | ✓ |
| Setup complexity | Low | High (parameter tuning) | High (pipeline design) |
| Real-time capable | ✓ | ✗ | ✗ |

While TrackMate [@Tinevez2017] provides sophisticated tracking with extensive customization options, it requires significant expertise for parameter optimization. CellProfiler [@Carpenter2006] excels at high-throughput cellular phenotyping but is not optimized for sub-cellular spot tracking. `FluoTrack` fills a niche by providing automated, easy-to-use multi-target tracking with built-in photobleaching analysis and dual-level (individual + population) statistics.

# Availability

`FluoTrack` is available on GitHub (https://github.com/alyssadongqiliu/fluorescence-brightness-tracker) and archived on Zenodo (DOI: 10.5281/zenodo.17656657) under the MIT license. Documentation and validation scripts are included in the repository.

# Acknowledgments

I thank Dr. Kerry Bloom and members of the Bloom Lab at UNC Chapel Hill for inspiring this work through discussions about chromatin dynamics and fluorescence microscopy analysis. This software was developed independently as part of computational biology training.

# References
