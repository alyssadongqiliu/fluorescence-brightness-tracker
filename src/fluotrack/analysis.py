"""
Data logging and analysis module for fluorescence brightness tracking.
"""

import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DataLogger:
    """
    Log brightness tracking data to CSV files.

    Parameters
    ----------
    output_dir : str or Path, default='.'
        Directory for output files
    prefix : str, default='brightness_log'
        Prefix for output filename

    Attributes
    ----------
    filename : Path
        Path to the current CSV log file
    """

    def __init__(self, output_dir: str = ".", prefix: str = "brightness_log"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = self.output_dir / f"{prefix}_{timestamp}.csv"

        self._initialize_csv()
        logger.info(f"Data logging initialized: {self.filename}")

    def _initialize_csv(self):
        """Initialize CSV file with header"""
        with open(self.filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["timestamp", "frame_number", "x", "y", "brightness", "notes"]
            )

    def log_point(self, data: Dict, notes: str = ""):
        """
        Log a single brightness measurement.

        Parameters
        ----------
        data : dict
            Data dictionary from tracker containing:
            - timestamp, frame_number, location, intensity
        notes : str, optional
            Additional notes or annotations
        """
        try:
            with open(self.filename, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        data["timestamp"],
                        data["frame_number"],
                        data["location"][0],
                        data["location"][1],
                        data["intensity"],
                        notes,
                    ]
                )
        except Exception as e:
            logger.error(f"Error logging data: {e}")

    def log_regions(self, regions: List[Dict], frame_number: int):
        """
        Log multiple bright regions.

        Parameters
        ----------
        regions : list of dict
            List of region data from tracker
        frame_number : int
            Current frame number
        """
        timestamp = datetime.now().isoformat()
        for i, region in enumerate(regions):
            data = {
                "timestamp": timestamp,
                "frame_number": frame_number,
                "location": region["location"],
                "intensity": region["intensity"],
            }
            self.log_point(data, notes=f"region_{i}")


class BrightnessAnalyzer:
    """
    Analyze fluorescence brightness tracking data.

    Parameters
    ----------
    data_file : str or Path
        Path to CSV data file
    """

    def __init__(self, data_file: str):
        self.data_file = Path(data_file)
        self.data = None
        self._load_data()

    def _load_data(self):
        """Load data from CSV file"""
        try:
            self.data = pd.read_csv(self.data_file)
            logger.info(f"Loaded {len(self.data)} data points")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise

    def compute_statistics(self) -> Dict:
        """
        Compute basic statistics on brightness data.

        Returns
        -------
        dict
            Dictionary of statistics including:
            - mean, std, min, max, median brightness
            - total_frames, duration
        """
        if self.data is None or len(self.data) == 0:
            return {}

        brightness = self.data["brightness"]

        # Parse timestamps
        timestamps = pd.to_datetime(self.data["timestamp"])
        duration = (timestamps.max() - timestamps.min()).total_seconds()

        stats = {
            "mean_brightness": float(brightness.mean()),
            "std_brightness": float(brightness.std()),
            "min_brightness": float(brightness.min()),
            "max_brightness": float(brightness.max()),
            "median_brightness": float(brightness.median()),
            "total_frames": int(self.data["frame_number"].max()),
            "duration_seconds": float(duration),
            "average_fps": float(len(self.data) / duration) if duration > 0 else 0,
        }

        return stats

    def detect_photobleaching(self, window_size: int = 100) -> Dict:
        """
        Detect photobleaching using linear regression.

        Parameters
        ----------
        window_size : int, default=100
            Window size for moving average

        Returns
        -------
        dict
            Dictionary containing:
            - slope: rate of brightness change
            - is_bleaching: boolean indicator
            - half_life_frames: estimated photobleaching half-life
        """
        if self.data is None or len(self.data) < window_size:
            return {}

        # Calculate moving average
        brightness = self.data["brightness"].values
        smoothed = np.convolve(
            brightness, np.ones(window_size) / window_size, mode="valid"
        )

        # Linear regression on smoothed data with error handling
        x = np.arange(len(smoothed))
        try:
            coeffs = np.polyfit(x, smoothed, 1)
            slope = coeffs[0]
        except (np.linalg.LinAlgError, ValueError):
            # If fitting fails, return no bleaching
            return {
                "slope": 0.0,
                "is_bleaching": False,
                "half_life_frames": None,
                "smoothed_brightness": smoothed,
            }

        # Estimate half-life if bleaching
        is_bleaching = slope < 0
        half_life = None
        if is_bleaching and smoothed[0] > 0:
            # Frames until 50% of initial brightness
            half_life = int(smoothed[0] * 0.5 / abs(slope))

        return {
            "slope": float(slope),
            "is_bleaching": bool(is_bleaching),
            "half_life_frames": half_life,
            "smoothed_brightness": smoothed,
        }

    def analyze_trajectory(self) -> Dict:
        """
        Analyze spatial trajectory of brightest point.

        Returns
        -------
        dict
            Dictionary containing:
            - mean_displacement: average movement per frame
            - total_distance: total path length
            - confinement_radius: radius containing 95% of points
        """
        if self.data is None or len(self.data) < 2:
            return {}

        x = self.data["x"].values
        y = self.data["y"].values

        # Calculate displacements
        dx = np.diff(x)
        dy = np.diff(y)
        distances = np.sqrt(dx**2 + dy**2)

        # Center of mass
        x_center = np.mean(x)
        y_center = np.mean(y)

        # Distances from center
        radial_distances = np.sqrt((x - x_center) ** 2 + (y - y_center) ** 2)

        # 95th percentile for confinement
        confinement_radius = float(np.percentile(radial_distances, 95))

        return {
            "mean_displacement": float(np.mean(distances)),
            "std_displacement": float(np.std(distances)),
            "total_distance": float(np.sum(distances)),
            "confinement_radius": confinement_radius,
            "center": (float(x_center), float(y_center)),
        }

    def plot_brightness_trend(self, output_file: Optional[str] = None):
        """
        Plot brightness over time.

        Parameters
        ----------
        output_file : str, optional
            If provided, save plot to this file
        """
        if self.data is None:
            logger.warning("No data to plot")
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(
            self.data["frame_number"], self.data["brightness"], alpha=0.5, label="Raw"
        )

        # Add moving average
        window = min(50, len(self.data) // 10)
        if window > 0:
            smoothed = self.data["brightness"].rolling(window=window).mean()
            ax.plot(
                self.data["frame_number"], smoothed, linewidth=2, label=f"MA({window})"
            )

        ax.set_xlabel("Frame Number", fontsize=12)
        ax.set_ylabel("Brightness (a.u.)", fontsize=12)
        ax.set_title("Fluorescence Brightness Over Time", fontsize=14)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, dpi=300)
            logger.info(f"Plot saved to {output_file}")
        else:
            plt.show()

        plt.close()

    def plot_trajectory(self, output_file: Optional[str] = None):
        """
        Plot spatial trajectory of brightest point.

        Parameters
        ----------
        output_file : str, optional
            If provided, save plot to this file
        """
        if self.data is None:
            logger.warning("No data to plot")
            return

        fig, ax = plt.subplots(figsize=(8, 8))

        # Color by time
        scatter = ax.scatter(
            self.data["x"],
            self.data["y"],
            c=self.data["frame_number"],
            cmap="viridis",
            s=10,
            alpha=0.6,
        )

        # Add start and end markers
        ax.plot(
            self.data["x"].iloc[0],
            self.data["y"].iloc[0],
            "go",
            markersize=10,
            label="Start",
        )
        ax.plot(
            self.data["x"].iloc[-1],
            self.data["y"].iloc[-1],
            "ro",
            markersize=10,
            label="End",
        )

        ax.set_xlabel("X Position (pixels)", fontsize=12)
        ax.set_ylabel("Y Position (pixels)", fontsize=12)
        ax.set_title("Spatial Trajectory of Brightest Point", fontsize=14)
        ax.legend()
        ax.set_aspect("equal")

        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label("Frame Number", fontsize=10)

        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, dpi=300)
            logger.info(f"Plot saved to {output_file}")
        else:
            plt.show()

        plt.close()

    def generate_report(self, output_file: str):
        """
        Generate comprehensive analysis report.

        Parameters
        ----------
        output_file : str
            Path for Excel report file
        """
        if self.data is None:
            logger.warning("No data for report")
            return

        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            # Raw data
            self.data.to_excel(writer, sheet_name="Raw Data", index=False)

            # Statistics
            stats = self.compute_statistics()
            stats_df = pd.DataFrame([stats])
            stats_df.to_excel(writer, sheet_name="Statistics", index=False)

            # Photobleaching analysis
            bleaching = self.detect_photobleaching()
            if bleaching:
                bleach_df = pd.DataFrame(
                    [{k: v for k, v in bleaching.items() if k != "smoothed_brightness"}]
                )
                bleach_df.to_excel(writer, sheet_name="Photobleaching", index=False)

            # Trajectory analysis
            trajectory = self.analyze_trajectory()
            if trajectory:
                traj_df = pd.DataFrame([trajectory])
                traj_df.to_excel(writer, sheet_name="Trajectory", index=False)

        logger.info(f"Report saved to {output_file}")
