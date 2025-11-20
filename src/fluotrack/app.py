"""
Main application interface for Fluorescence Brightness Tracker.
"""

import cv2
import time
import logging
import tkinter as tk
from typing import Optional
from .tracker import BrightnessTracker, RegionSelector
from .analysis import DataLogger

logger = logging.getLogger(__name__)


class FluoTrackApp:
    """
    Main application for fluorescence brightness tracking.

    This class provides a GUI interface for selecting tracking mode
    and running real-time brightness analysis.
    """

    def __init__(self):
        """Initialize the application"""
        self.root = tk.Tk()
        self.root.title("Fluorescence Brightness Tracker")

        # Center window
        window_width = 350
        window_height = 250
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

        # Tracking mode
        self.mode = tk.StringVar(value="brightest_point")

        # Output directory
        self.output_dir = tk.StringVar(value=".")

        self._setup_gui()

        # Initialize components
        self.tracker = None
        self.logger = None
        self.bbox = None

    def _setup_gui(self):
        """Set up GUI elements"""
        # Title
        title_label = tk.Label(
            self.root,
            text="Fluorescence Brightness Tracker",
            font=("Arial", 14, "bold"),
        )
        title_label.pack(pady=10)

        # Mode selection
        mode_frame = tk.LabelFrame(self.root, text="Tracking Mode", padx=10, pady=10)
        mode_frame.pack(pady=10, padx=20, fill="x")

        tk.Radiobutton(
            mode_frame,
            text="Track Single Brightest Point",
            variable=self.mode,
            value="brightest_point",
        ).pack(anchor="w")

        tk.Radiobutton(
            mode_frame,
            text="Analyze Multiple Bright Regions",
            variable=self.mode,
            value="bright_regions",
        ).pack(anchor="w")

        # Output directory
        output_frame = tk.Frame(self.root)
        output_frame.pack(pady=5, padx=20, fill="x")

        tk.Label(output_frame, text="Output Directory:").pack(side="left")
        tk.Entry(output_frame, textvariable=self.output_dir, width=20).pack(
            side="left", padx=5
        )
        tk.Button(output_frame, text="Browse", command=self._browse_output).pack(
            side="left"
        )

        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=15)

        tk.Button(
            button_frame,
            text="Start Tracking",
            command=self._start_tracking,
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=5,
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame, text="Exit", command=self.root.quit, padx=20, pady=5
        ).pack(side="left", padx=5)

    def _browse_output(self):
        """Browse for output directory"""
        from tkinter import filedialog

        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)

    def _start_tracking(self):
        """Start the tracking process"""
        # Select region
        selector = RegionSelector()
        self.bbox = selector.select()

        if self.bbox is None:
            logger.info("Region selection cancelled")
            return

        # Initialize tracker and logger
        self.tracker = BrightnessTracker(self.bbox)
        self.logger = DataLogger(output_dir=self.output_dir.get())

        # Hide main window
        self.root.withdraw()

        # Run tracking based on mode
        try:
            if self.mode.get() == "brightest_point":
                self._track_brightest_point()
            else:
                self._analyze_bright_regions()
        finally:
            # Show main window again
            self.root.deiconify()

    def _track_brightest_point(self):
        """Track single brightest point in real-time"""
        logger.info("Starting brightest point tracking")

        fps_update_interval = 30
        frame_count = 0
        start_time = time.time()

        try:
            while True:
                # Capture and process
                frame = self.tracker.capture_frame()
                gray = self.tracker.preprocess_frame(frame)

                # Find brightest point
                result = self.tracker.find_brightest_point(gray)

                # Log data
                self.logger.log_point(result)

                # Update FPS
                frame_count += 1
                if frame_count % fps_update_interval == 0:
                    elapsed = time.time() - start_time
                    fps = self.tracker.calculate_fps(elapsed, fps_update_interval)
                    frame_count = 0
                    start_time = time.time()

                # Visualization
                loc = result["location"]
                cv2.circle(frame, loc, 10, (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"FPS: {self.tracker.fps:.1f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )
                cv2.putText(
                    frame,
                    f"Brightness: {result['intensity']:.0f}",
                    (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )

                # Display
                cv2.imshow("Fluorescence Brightness Tracking", frame)

                # Check for exit
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        except Exception as e:
            logger.error(f"Error during tracking: {e}")
        finally:
            cv2.destroyAllWindows()
            logger.info("Tracking stopped")
            self._show_results()

    def _analyze_bright_regions(self):
        """Analyze multiple bright regions"""
        logger.info("Starting bright regions analysis")

        try:
            while True:
                # Capture and process
                frame = self.tracker.capture_frame()
                gray = self.tracker.preprocess_frame(frame)

                # Find bright regions
                regions = self.tracker.find_bright_regions(gray)

                # Log data
                self.logger.log_regions(regions, self.tracker.frame_count)

                # Visualization
                for i, region in enumerate(regions[:5]):  # Show top 5
                    # Draw bounding box
                    x, y, w, h = region["bbox"]
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # Mark brightest point
                    loc = region["location"]
                    cv2.circle(frame, loc, 5, (0, 255, 255), -1)

                    # Label
                    cv2.putText(
                        frame,
                        f"#{i+1}: {region['intensity']:.0f}",
                        (x, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        1,
                    )

                # Display
                cv2.imshow("Bright Regions Analysis", frame)

                # Check for exit
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        except Exception as e:
            logger.error(f"Error during analysis: {e}")
        finally:
            cv2.destroyAllWindows()
            logger.info("Analysis stopped")
            self._show_results()

    def _show_results(self):
        """Show results summary"""
        from tkinter import messagebox

        message = f"Tracking complete!\n\nData saved to:\n{self.logger.filename}"
        messagebox.showinfo("Results", message)

    def run(self):
        """Run the application"""
        logger.info("Application started")
        self.root.mainloop()


def main():
    """Main entry point"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("fluotrack.log"), logging.StreamHandler()],
    )

    # Run app
    app = FluoTrackApp()
    app.run()


if __name__ == "__main__":
    main()
