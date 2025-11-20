"""
Enhanced Multi-Target Fluorescence Tracker

Key innovations:
1. Automatic detection of multiple fluorescent spots
2. Frame-to-frame tracking with ID assignment
3. Individual spot analysis (photobleaching, movement)
4. Population statistics
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from scipy.optimize import linear_sum_assignment
from collections import defaultdict


@dataclass
class FluorescentSpot:
    """Represents a single fluorescent spot"""
    id: int
    location: Tuple[int, int]
    intensity: float
    area: int
    frame_number: int
    timestamp: str
    
    
class AdaptiveSpotDetector:
    """
    Intelligent spot detection using adaptive thresholding and morphological operations.
    
    Innovation: Automatically identifies all fluorescent spots above background,
    not just the brightest one. Uses local statistics to distinguish signal from noise.
    """
    
    def __init__(self, 
                 min_spot_area: int = 10,
                 max_spot_area: int = 1000,
                 sensitivity: float = 2.0,
                 denoising: bool = True):
        """
        Parameters
        ----------
        min_spot_area : int
            Minimum area (pixels) to consider as a spot
        max_spot_area : int
            Maximum area (pixels) to consider as a spot
        sensitivity : float
            Detection sensitivity (lower = more sensitive)
            Threshold = mean + sensitivity * std
        denoising : bool
            Whether to apply Gaussian denoising
        """
        self.min_spot_area = min_spot_area
        self.max_spot_area = max_spot_area
        self.sensitivity = sensitivity
        self.denoising = denoising
        
    def detect_spots(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect all fluorescent spots in frame.
        
        Parameters
        ----------
        frame : np.ndarray
            Grayscale image
            
        Returns
        -------
        List[Dict]
            List of detected spots with properties:
            - location: (x, y)
            - intensity: mean intensity
            - area: pixel count
            - bbox: (x, y, w, h)
        """
        # Preprocess
        if self.denoising:
            frame = cv2.GaussianBlur(frame, (5, 5), 0)
        
        # Adaptive thresholding using local statistics
        # Innovation: Use percentile-based threshold instead of fixed value
        threshold = self._calculate_adaptive_threshold(frame)
        
        # Create binary mask
        _, binary = cv2.threshold(frame, threshold, 255, cv2.THRESH_BINARY)
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Find contours (potential spots)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        spots = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter by area
            if area < self.min_spot_area or area > self.max_spot_area:
                continue
            
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Extract ROI and calculate statistics
            roi = frame[y:y+h, x:x+w]
            mask_roi = binary[y:y+h, x:x+w]
            
            # Calculate intensity (mean of pixels within contour)
            intensity = np.mean(roi[mask_roi > 0])
            
            # Find brightest point within this spot (for precise localization)
            _, max_val, _, max_loc = cv2.minMaxLoc(roi, mask=mask_roi)
            global_max_loc = (x + max_loc[0], y + max_loc[1])
            
            spots.append({
                'location': global_max_loc,
                'intensity': float(intensity),
                'max_intensity': float(max_val),
                'area': int(area),
                'bbox': (x, y, w, h)
            })
        
        # Sort by intensity (brightest first)
        spots.sort(key=lambda s: s['intensity'], reverse=True)
        
        return spots
    
    def _calculate_adaptive_threshold(self, frame: np.ndarray) -> float:
        """
        Calculate adaptive threshold based on image statistics.
        
        Innovation: Uses robust statistics (median, MAD) instead of mean/std
        to handle outliers better.
        """
        # Use median and MAD (Median Absolute Deviation) for robustness
        median = np.median(frame)
        mad = np.median(np.abs(frame - median))
        
        # Convert MAD to standard deviation equivalent
        std_estimate = 1.4826 * mad
        
        # Threshold: median + sensitivity * std
        threshold = median + self.sensitivity * std_estimate
        
        return threshold


class MultiTargetTracker:
    """
    Track multiple fluorescent spots across frames.
    
    Innovation: Uses Hungarian algorithm for optimal assignment,
    handles spot appearance/disappearance, maintains trajectory history.
    """
    
    def __init__(self, max_distance: float = 50.0):
        """
        Parameters
        ----------
        max_distance : float
            Maximum distance (pixels) to consider same spot between frames
        """
        self.max_distance = max_distance
        self.next_id = 0
        self.active_tracks = {}  # id -> track info
        self.track_history = defaultdict(list)  # id -> list of observations
        self.frame_number = 0
        
    def update(self, spots: List[Dict], timestamp: str) -> List[FluorescentSpot]:
        """
        Update tracks with new detections.
        
        Parameters
        ----------
        spots : List[Dict]
            Detected spots from current frame
        timestamp : str
            Current timestamp
            
        Returns
        -------
        List[FluorescentSpot]
            Updated spots with track IDs
        """
        self.frame_number += 1
        
        if not self.active_tracks:
            # First frame: create new tracks
            return self._initialize_tracks(spots, timestamp)
        
        # Match current spots to existing tracks
        tracked_spots = self._match_spots_to_tracks(spots, timestamp)
        
        return tracked_spots
    
    def _initialize_tracks(self, spots: List[Dict], timestamp: str) -> List[FluorescentSpot]:
        """Initialize tracks for first frame"""
        tracked_spots = []
        
        for spot in spots:
            track_id = self._get_next_id()
            
            tracked_spot = FluorescentSpot(
                id=track_id,
                location=spot['location'],
                intensity=spot['intensity'],
                area=spot['area'],
                frame_number=self.frame_number,
                timestamp=timestamp
            )
            
            self.active_tracks[track_id] = {
                'last_location': spot['location'],
                'last_seen': self.frame_number
            }
            self.track_history[track_id].append(tracked_spot)
            tracked_spots.append(tracked_spot)
        
        return tracked_spots
    
    def _match_spots_to_tracks(self, spots: List[Dict], timestamp: str) -> List[FluorescentSpot]:
        """
        Match detected spots to existing tracks using Hungarian algorithm.
        
        Innovation: Optimal assignment that minimizes total distance.
        """
        if not spots:
            return []
        
        # Build cost matrix (distances between spots and tracks)
        track_ids = list(self.active_tracks.keys())
        n_tracks = len(track_ids)
        n_spots = len(spots)
        
        cost_matrix = np.zeros((n_tracks, n_spots))
        
        for i, track_id in enumerate(track_ids):
            last_loc = self.active_tracks[track_id]['last_location']
            
            for j, spot in enumerate(spots):
                current_loc = spot['location']
                distance = np.sqrt(
                    (current_loc[0] - last_loc[0])**2 + 
                    (current_loc[1] - last_loc[1])**2
                )
                cost_matrix[i, j] = distance
        
        # Hungarian algorithm for optimal assignment
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        tracked_spots = []
        matched_spots = set()
        
        # Process matched pairs
        for i, j in zip(row_ind, col_ind):
            if cost_matrix[i, j] <= self.max_distance:
                track_id = track_ids[i]
                spot = spots[j]
                
                tracked_spot = FluorescentSpot(
                    id=track_id,
                    location=spot['location'],
                    intensity=spot['intensity'],
                    area=spot['area'],
                    frame_number=self.frame_number,
                    timestamp=timestamp
                )
                
                # Update track
                self.active_tracks[track_id]['last_location'] = spot['location']
                self.active_tracks[track_id]['last_seen'] = self.frame_number
                self.track_history[track_id].append(tracked_spot)
                
                tracked_spots.append(tracked_spot)
                matched_spots.add(j)
        
        # Create new tracks for unmatched spots
        for j, spot in enumerate(spots):
            if j not in matched_spots:
                track_id = self._get_next_id()
                
                tracked_spot = FluorescentSpot(
                    id=track_id,
                    location=spot['location'],
                    intensity=spot['intensity'],
                    area=spot['area'],
                    frame_number=self.frame_number,
                    timestamp=timestamp
                )
                
                self.active_tracks[track_id] = {
                    'last_location': spot['location'],
                    'last_seen': self.frame_number
                }
                self.track_history[track_id].append(tracked_spot)
                tracked_spots.append(tracked_spot)
        
        # Remove stale tracks (not seen for 5 frames)
        stale_ids = [
            tid for tid, info in self.active_tracks.items()
            if self.frame_number - info['last_seen'] > 5
        ]
        for tid in stale_ids:
            del self.active_tracks[tid]
        
        return tracked_spots
    
    def _get_next_id(self) -> int:
        """Get next unique ID"""
        track_id = self.next_id
        self.next_id += 1
        return track_id
    
    def get_track_statistics(self, track_id: int) -> Dict:
        """
        Get statistics for a specific track.
        
        Returns
        -------
        Dict
            Statistics including:
            - duration: number of frames
            - mean_intensity: average brightness
            - intensity_trend: slope of intensity over time
            - displacement: total distance traveled
            - velocity: average movement per frame
        """
        if track_id not in self.track_history:
            return {}
        
        track = self.track_history[track_id]
        
        if len(track) < 2:
            return {
                'duration': 1,
                'mean_intensity': track[0].intensity,
                'intensity_trend': 0.0,
                'total_displacement': 0.0,
                'mean_velocity': 0.0,
                'is_photobleaching': False
            }
        
        # Intensity statistics
        intensities = [spot.intensity for spot in track]
        mean_intensity = np.mean(intensities)
        
        # Fit linear trend
        frames = np.arange(len(track))
        intensity_trend = np.polyfit(frames, intensities, 1)[0]
        
        # Movement statistics
        positions = [spot.location for spot in track]
        distances = [
            np.sqrt((positions[i+1][0] - positions[i][0])**2 + 
                   (positions[i+1][1] - positions[i][1])**2)
            for i in range(len(positions) - 1)
        ]
        
        total_displacement = sum(distances)
        mean_velocity = np.mean(distances) if distances else 0
        
        return {
            'duration': len(track),
            'mean_intensity': float(mean_intensity),
            'intensity_trend': float(intensity_trend),
            'total_displacement': float(total_displacement),
            'mean_velocity': float(mean_velocity),
            'is_photobleaching': intensity_trend < -0.5
        }


class EnhancedFluoTracker:
    """
    Main interface for enhanced multi-target tracking.
    
    Combines adaptive detection with robust tracking.
    """
    
    def __init__(self, 
                 min_spot_area: int = 10,
                 max_spot_area: int = 1000,
                 sensitivity: float = 2.0,
                 max_tracking_distance: float = 50.0):
        """
        Parameters
        ----------
        min_spot_area : int
            Minimum spot area in pixels
        max_spot_area : int
            Maximum spot area in pixels
        sensitivity : float
            Detection sensitivity (2.0 = 2 std above background)
        max_tracking_distance : float
            Maximum distance for tracking between frames
        """
        self.detector = AdaptiveSpotDetector(
            min_spot_area=min_spot_area,
            max_spot_area=max_spot_area,
            sensitivity=sensitivity
        )
        self.tracker = MultiTargetTracker(
            max_distance=max_tracking_distance
        )
        
    def process_frame(self, frame: np.ndarray, timestamp: str) -> List[FluorescentSpot]:
        """
        Process a single frame.
        
        Parameters
        ----------
        frame : np.ndarray
            Grayscale image
        timestamp : str
            Timestamp for this frame
            
        Returns
        -------
        List[FluorescentSpot]
            Detected and tracked spots
        """
        # Detect spots
        spots = self.detector.detect_spots(frame)
        
        # Track spots
        tracked_spots = self.tracker.update(spots, timestamp)
        
        return tracked_spots
    
    def get_all_tracks(self) -> Dict[int, List[FluorescentSpot]]:
        """Get all track histories"""
        return dict(self.tracker.track_history)
    
    def get_track_stats(self, track_id: int) -> Dict:
        """Get statistics for specific track"""
        return self.tracker.get_track_statistics(track_id)
    
    def get_population_statistics(self) -> Dict:
        """
        Get population-level statistics.
        
        Innovation: Analyze collective behavior of all spots.
        """
        all_tracks = self.tracker.track_history
        
        if not all_tracks:
            return {}
        
        # Count active tracks
        n_tracks = len(all_tracks)
        
        # Average properties
        all_intensities = []
        all_velocities = []
        photobleaching_count = 0
        
        for track_id in all_tracks:
            stats = self.get_track_stats(track_id)
            if stats:
                all_intensities.append(stats['mean_intensity'])
                if 'mean_velocity' in stats:
                    all_velocities.append(stats['mean_velocity'])
                if stats.get('is_photobleaching', False):
                    photobleaching_count += 1
        
        return {
            'total_tracks': n_tracks,
            'mean_intensity': float(np.mean(all_intensities)) if all_intensities else 0,
            'std_intensity': float(np.std(all_intensities)) if all_intensities else 0,
            'mean_velocity': float(np.mean(all_velocities)) if all_velocities else 0,
            'photobleaching_fraction': photobleaching_count / n_tracks if n_tracks > 0 else 0
        }
