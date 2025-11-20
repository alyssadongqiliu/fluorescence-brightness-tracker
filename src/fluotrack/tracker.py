"""
Fluorescence Brightness Tracker - Core tracking module

This module provides real-time tracking and analysis of fluorescent protein
brightness in microscopy images or screen captures.
"""

import cv2
import numpy as np
from PIL import ImageGrab
import logging
from typing import Tuple, Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class BrightnessTracker:
    """
    Real-time brightness tracking for fluorescent proteins.
    
    This class implements algorithms to detect and track the brightest points
    or regions in fluorescence microscopy images, with specialized handling
    for fluorescent protein characteristics.
    
    Parameters
    ----------
    bbox : tuple of int
        Bounding box coordinates (x1, y1, x2, y2) for the region of interest
    denoising : bool, default=True
        Whether to apply Gaussian denoising
    kernel_size : int, default=5
        Kernel size for Gaussian blur (must be odd)
        
    Attributes
    ----------
    frame_count : int
        Number of frames processed
    fps : float
        Current frames per second
    """
    
    def __init__(self, bbox: Tuple[int, int, int, int], 
                 denoising: bool = True,
                 kernel_size: int = 5):
        self.bbox = bbox
        self.denoising = denoising
        self.kernel_size = kernel_size
        self.frame_count = 0
        self.fps = 0.0
        self._validate_params()
        
    def _validate_params(self):
        """Validate initialization parameters"""
        if len(self.bbox) != 4:
            raise ValueError("bbox must contain 4 elements (x1, y1, x2, y2)")
        if self.kernel_size % 2 == 0:
            raise ValueError("kernel_size must be odd")
        if self.kernel_size < 3:
            raise ValueError("kernel_size must be at least 3")
            
    def capture_frame(self) -> np.ndarray:
        """
        Capture a frame from the screen region.
        
        Returns
        -------
        np.ndarray
            Captured frame as numpy array in BGR format
        """
        screen = ImageGrab.grab(bbox=self.bbox)
        frame = np.array(screen)
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for brightness detection.
        
        Parameters
        ----------
        frame : np.ndarray
            Input frame in BGR format
            
        Returns
        -------
        np.ndarray
            Preprocessed grayscale frame
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self.denoising:
            gray = cv2.GaussianBlur(gray, (self.kernel_size, self.kernel_size), 0)
            
        return gray
        
    def find_brightest_point(self, frame: np.ndarray) -> Dict[str, any]:
        """
        Find the brightest point in the frame.
        
        Parameters
        ----------
        frame : np.ndarray
            Grayscale frame
            
        Returns
        -------
        dict
            Dictionary containing:
            - 'location': (x, y) coordinates of brightest point
            - 'intensity': brightness value (0-255)
            - 'frame_number': current frame count
            - 'timestamp': ISO format timestamp
        """
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(frame)
        
        self.frame_count += 1
        
        return {
            'location': max_loc,
            'intensity': float(max_val),
            'frame_number': self.frame_count,
            'timestamp': datetime.now().isoformat()
        }
        
    def find_bright_regions(self, frame: np.ndarray, 
                           threshold_percentile: float = 90.0,
                           min_area: int = 50) -> list:
        """
        Find multiple bright regions using adaptive thresholding.
        
        Parameters
        ----------
        frame : np.ndarray
            Grayscale frame
        threshold_percentile : float, default=90.0
            Percentile threshold for brightness (0-100)
        min_area : int, default=50
            Minimum contour area to consider
            
        Returns
        -------
        list of dict
            List of detected regions, each containing:
            - 'location': (x, y) of brightest point in region
            - 'intensity': brightness value
            - 'bbox': (x, y, w, h) bounding box
            - 'area': contour area
        """
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            frame, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Find contours
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
                
            x, y, w, h = cv2.boundingRect(contour)
            roi = frame[y:y+h, x:x+w]
            
            # Find brightest point in ROI
            _, max_val, _, max_loc = cv2.minMaxLoc(roi)
            
            # Convert to global coordinates
            global_loc = (x + max_loc[0], y + max_loc[1])
            
            regions.append({
                'location': global_loc,
                'intensity': float(max_val),
                'bbox': (x, y, w, h),
                'area': int(area)
            })
            
        # Sort by intensity
        regions.sort(key=lambda r: r['intensity'], reverse=True)
        
        return regions
        
    def calculate_fps(self, elapsed_time: float, num_frames: int = 30) -> float:
        """
        Calculate frames per second.
        
        Parameters
        ----------
        elapsed_time : float
            Time elapsed in seconds
        num_frames : int
            Number of frames in the period
            
        Returns
        -------
        float
            Calculated FPS
        """
        if elapsed_time > 0:
            self.fps = num_frames / elapsed_time
        return self.fps


class RegionSelector:
    """
    Interactive region selection tool for defining ROI.
    
    This class provides a GUI for users to select a rectangular region
    on the screen for brightness tracking.
    """
    
    def __init__(self):
        self.bbox = None
        
    def select(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Launch interactive region selection.
        
        Returns
        -------
        tuple of int or None
            Selected bounding box (x1, y1, x2, y2) or None if cancelled
        """
        import tkinter as tk
        
        selection_window = tk.Tk()
        selection_window.attributes("-alpha", 0.3)
        selection_window.attributes("-topmost", True)
        selection_window.geometry("+0+0")
        selection_window.attributes("-fullscreen", True)
        selection_window.config(cursor="cross")
        
        canvas = tk.Canvas(selection_window, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        
        coords = {"x1": None, "y1": None, "x2": None, "y2": None}
        rect_id = None
        
        def on_click(event):
            coords["x1"] = event.x
            coords["y1"] = event.y
            
        def on_drag(event):
            nonlocal rect_id
            if rect_id:
                canvas.delete(rect_id)
            coords["x2"] = event.x
            coords["y2"] = event.y
            rect_id = canvas.create_rectangle(
                coords["x1"], coords["y1"],
                coords["x2"], coords["y2"],
                outline="green", width=2
            )
            
        def on_release(event):
            coords["x2"] = event.x
            coords["y2"] = event.y
            
            x1 = min(coords["x1"], coords["x2"])
            y1 = min(coords["y1"], coords["y2"])
            x2 = max(coords["x1"], coords["x2"])
            y2 = max(coords["y1"], coords["y2"])
            
            if (x2 - x1) < 10 or (y2 - y1) < 10:
                logger.warning("Selection too small")
                return
                
            self.bbox = (x1, y1, x2, y2)
            selection_window.quit()
            selection_window.destroy()
            
        def on_escape(event):
            selection_window.quit()
            selection_window.destroy()
            
        canvas.bind("<Button-1>", on_click)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        selection_window.bind("<Escape>", on_escape)
        
        # Instructions
        label = tk.Label(
            selection_window,
            text="Click and drag to select region. Press ESC to cancel.",
            bg='white', font=('Arial', 12)
        )
        label.place(relx=0.5, rely=0.1, anchor='center')
        
        selection_window.mainloop()
        
        return self.bbox
