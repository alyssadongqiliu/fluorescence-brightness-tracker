"""
FluoTrack: Fluorescence Brightness Tracking for Microscopy

A Python package for real-time tracking and analysis of fluorescent protein
brightness in microscopy images.
"""

__version__ = "0.1.0"
__author__ = "Dongqi Liu"
__email__ = "dongql@unc.edu"

from .tracker import BrightnessTracker, RegionSelector
from .analysis import DataLogger, BrightnessAnalyzer
from .app import FluoTrackApp

__all__ = [
    "BrightnessTracker",
    "RegionSelector",
    "DataLogger",
    "BrightnessAnalyzer",
    "FluoTrackApp",
]
