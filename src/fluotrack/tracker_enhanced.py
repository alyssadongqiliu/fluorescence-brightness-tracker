"""
Enhanced Brightness Tracker with Adaptive Algorithms

This module implements advanced tracking with:
1. Adaptive background estimation
2. Temporal filtering with Kalman filter
3. Signal quality scoring
4. Multi-spot tracking with confidence
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class KalmanTracker:
    """
    Kalman filter for smooth trajectory tracking.
    
    Predicts future position based on motion model and handles
    occlusions/missed detections gracefully.
    """
    
    def __init__(self):
        # State: [x, y, vx, vy]
        self.kf = cv2.KalmanFilter(4, 2)
        self.kf.measurementMatrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=np.float32)
        
        self.kf.transitionMatrix = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        # Process noise
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03
        
        # Measurement noise
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 1.0
        
        self.initialized = False
        
    def init(self, x: float, y: float):
        """Initialize with first measurement"""
        self.kf.statePre = np.array([x, y, 0, 0], dtype=np.float32).reshape(-1, 1)
        self.kf.statePost = self.kf.statePre.copy()
        self.initialized = True
        
    def predict(self) -> Tuple[float, float]:
        """Predict next position"""
        pred = self.kf.predict()
        return float(pred[0]), float(pred[1])
        
    def update(self, x: float, y: float) -> Tuple[float, float]:
        """Update with new measurement"""
        measurement = np.array([x, y], dtype=np.float32).reshape(-1, 1)
        corrected = self.kf.correct(measurement)
        return float(corrected[0]), float(corrected[1])


class AdaptiveBackgroundModel:
    """
    Adaptive background estimation using running statistics.
    
    Maintains a statistical model of background intensity to
    distinguish true signals from background fluctuations.
    """
    
    def __init__(self, learning_rate: float = 0.01):
        self.learning_rate = learning_rate
        self.mean = None
        self.std = None
        
    def update(self, frame: np.ndarray):
        """Update background model"""
        if self.mean is None:
            self.mean = frame.astype(np.float32)
            self.std = np.ones_like(frame, dtype=np.float32) * 10.0
        else:
            # Running average
            self.mean = (1 - self.learning_rate) * self.mean + \
                       self.learning_rate * frame
            
            # Running std
            diff = np.abs(frame - self.mean)
            self.std = (1 - self.learning_rate) * self.std + \
                      self.learning_rate * diff
                      
    def subtract(self, frame: np.ndarray, threshold: float = 3.0) -> np.ndarray:
        """
        Subtract background and threshold.
        
        Parameters
        ----------
        frame : np.ndarray
            Input frame
        threshold : float
            Number of std deviations above mean for detection
            
        Returns
        -------
        np.ndarray
            Foreground mask (binary)
        """
        if self.mean is None:
            return np.ones_like(frame, dtype=np.uint8) * 255
            
        # Normalize by background
        diff = (frame.astype(np.float32) - self.mean) / (self.std + 1e-6)
        
        # Threshold at N standard deviations
        mask = (diff > threshold).astype(np.uint8) * 255
        
        return mask


class EnhancedBrightnessTracker:
    """
    Enhanced brightness tracker with adaptive algorithms.
    
    Key improvements over basic tracker:
    1. Adaptive background subtraction
    2. Kalman filtering for smooth trajectories
    3. Signal quality scoring
    4. Robust to noise and occlusions
    
    Parameters
    ----------
    bbox : tuple of int
        Region of interest (x1, y1, x2, y2)
    use_kalman : bool, default=True
        Enable Kalman filtering for trajectory smoothing
    use_adaptive_bg : bool, default=True
        Enable adaptive background estimation
    denoising : bool, default=True
        Enable Gaussian denoising
    kernel_size : int, default=5
        Kernel size for Gaussian blur
    """
    
    def __init__(self, 
                 bbox: Tuple[int, int, int, int],
                 use_kalman: bool = True,
                 use_adaptive_bg: bool = True,
                 denoising: bool = True,
                 kernel_size: int = 5):
        
        self.bbox = bbox
        self.use_kalman = use_kalman
        self.use_adaptive_bg = use_adaptive_bg
        self.denoising = denoising
        self.kernel_size = kernel_size
        
        # Initialize Kalman filter
        if self.use_kalman:
            self.kalman = KalmanTracker()
        
        # Initialize background model
        if self.use_adaptive_bg:
            self.bg_model = AdaptiveBackgroundModel(learning_rate=0.01)
        
        self.frame_count = 0
        self.fps = 0.0
        
        logger.info(f"Enhanced tracker initialized: "
                   f"Kalman={use_kalman}, AdaptiveBG={use_adaptive_bg}")
        
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame with optional denoising and background subtraction.
        
        Parameters
        ----------
        frame : np.ndarray
            Input frame (grayscale)
            
        Returns
        -------
        np.ndarray
            Preprocessed frame
        """
        # Denoising
        if self.denoising:
            frame = cv2.GaussianBlur(frame, (self.kernel_size, self.kernel_size), 0)
        
        # Adaptive background subtraction
        if self.use_adaptive_bg:
            # Update background model
            self.bg_model.update(frame)
            
            # Subtract background
            fg_mask = self.bg_model.subtract(frame, threshold=2.5)
            
            # Apply mask to original frame
            frame = cv2.bitwise_and(frame, frame, mask=fg_mask)
        
        return frame
        
    def compute_signal_quality(self, 
                               frame: np.ndarray, 
                               location: Tuple[int, int],
                               intensity: float,
                               window_size: int = 11) -> Dict[str, float]:
        """
        Compute signal quality metrics for detected spot.
        
        Parameters
        ----------
        frame : np.ndarray
            Grayscale frame
        location : tuple of int
            (x, y) position of detected spot
        intensity : float
            Peak intensity value
        window_size : int
            Size of local window for SNR calculation
            
        Returns
        -------
        dict
            Quality metrics: snr, contrast, confidence
        """
        x, y = location
        h, w = frame.shape
        
        # Extract local window
        half = window_size // 2
        x1 = max(0, x - half)
        y1 = max(0, y - half)
        x2 = min(w, x + half + 1)
        y2 = min(h, y + half + 1)
        
        window = frame[y1:y2, x1:x2]
        
        if window.size == 0:
            return {'snr': 0.0, 'contrast': 0.0, 'confidence': 0.0}
        
        # Compute SNR
        mean_bg = np.mean(window)
        std_bg = np.std(window) + 1e-6
        snr = (intensity - mean_bg) / std_bg
        
        # Compute contrast
        contrast = (intensity - mean_bg) / (intensity + mean_bg + 1e-6)
        
        # Overall confidence score (0-1)
        confidence = min(1.0, snr / 10.0)  # Normalize assuming SNR~10 is excellent
        
        return {
            'snr': float(snr),
            'contrast': float(contrast),
            'confidence': float(confidence)
        }
        
    def find_brightest_point(self, frame: np.ndarray) -> Dict[str, any]:
        """
        Find brightest point with quality assessment.
        
        Parameters
        ----------
        frame : np.ndarray
            Grayscale frame
            
        Returns
        -------
        dict
            Detection result with location, intensity, quality metrics
        """
        self.frame_count += 1
        
        # Preprocess
        processed = self.preprocess_frame(frame)
        
        # Find brightest point
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(processed)
        
        # Kalman filtering for smooth trajectory
        if self.use_kalman:
            if not self.kalman.initialized:
                self.kalman.init(max_loc[0], max_loc[1])
                smoothed_loc = max_loc
            else:
                # Predict
                pred_x, pred_y = self.kalman.predict()
                
                # Update with measurement
                smoothed_x, smoothed_y = self.kalman.update(max_loc[0], max_loc[1])
                smoothed_loc = (int(smoothed_x), int(smoothed_y))
        else:
            smoothed_loc = max_loc
        
        # Compute signal quality
        quality = self.compute_signal_quality(frame, max_loc, max_val)
        
        return {
            'location': smoothed_loc,
            'raw_location': max_loc,
            'intensity': float(max_val),
            'frame_number': self.frame_count,
            'timestamp': datetime.now().isoformat(),
            'snr': quality['snr'],
            'contrast': quality['contrast'],
            'confidence': quality['confidence']
        }
        
    def find_multiple_spots(self,
                           frame: np.ndarray,
                           num_spots: int = 5,
                           min_distance: int = 10) -> List[Dict[str, any]]:
        """
        Find multiple bright spots with non-maximum suppression.
        
        Parameters
        ----------
        frame : np.ndarray
            Grayscale frame
        num_spots : int
            Maximum number of spots to detect
        min_distance : int
            Minimum distance between spots (pixels)
            
        Returns
        -------
        list of dict
            Detected spots with locations and quality metrics
        """
        # Preprocess
        processed = self.preprocess_frame(frame)
        
        spots = []
        mask = processed.copy()
        
        for i in range(num_spots):
            # Find brightest remaining point
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(mask)
            
            if max_val < 50:  # Minimum intensity threshold
                break
            
            # Compute quality
            quality = self.compute_signal_quality(frame, max_loc, max_val)
            
            # Store spot
            spots.append({
                'location': max_loc,
                'intensity': float(max_val),
                'rank': i + 1,
                'snr': quality['snr'],
                'contrast': quality['contrast'],
                'confidence': quality['confidence']
            })
            
            # Suppress nearby pixels
            x, y = max_loc
            cv2.circle(mask, (x, y), min_distance, 0, -1)
        
        return spots
        
    def calculate_fps(self, elapsed_time: float, num_frames: int = 30) -> float:
        """Calculate frames per second"""
        if elapsed_time > 0:
            self.fps = num_frames / elapsed_time
        return self.fps


# Backward compatibility: keep original class name
class BrightnessTracker(EnhancedBrightnessTracker):
    """Alias for backward compatibility"""
    pass
