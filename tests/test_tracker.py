"""
Unit tests for FluoTrack brightness tracking module.
"""

import pytest
import numpy as np
from fluotrack.tracker import BrightnessTracker, RegionSelector


class TestBrightnessTracker:
    """Tests for BrightnessTracker class"""
    
    def test_initialization(self):
        """Test tracker initialization with valid parameters"""
        bbox = (0, 0, 100, 100)
        tracker = BrightnessTracker(bbox)
        
        assert tracker.bbox == bbox
        assert tracker.denoising is True
        assert tracker.kernel_size == 5
        assert tracker.frame_count == 0
        
    def test_invalid_bbox(self):
        """Test that invalid bbox raises ValueError"""
        with pytest.raises(ValueError, match="bbox must contain 4 elements"):
            BrightnessTracker((0, 0, 100))
            
    def test_even_kernel_size(self):
        """Test that even kernel size raises ValueError"""
        with pytest.raises(ValueError, match="kernel_size must be odd"):
            BrightnessTracker((0, 0, 100, 100), kernel_size=4)
            
    def test_small_kernel_size(self):
        """Test that kernel size < 3 raises ValueError"""
        with pytest.raises(ValueError, match="kernel_size must be at least 3"):
            BrightnessTracker((0, 0, 100, 100), kernel_size=1)
            
    def test_preprocess_frame(self):
        """Test frame preprocessing"""
        bbox = (0, 0, 100, 100)
        tracker = BrightnessTracker(bbox, denoising=False)
        
        # Create test frame (BGR)
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame[50, 50] = [255, 255, 255]  # White pixel
        
        gray = tracker.preprocess_frame(frame)
        
        assert gray.shape == (100, 100)
        assert gray.dtype == np.uint8
        assert gray[50, 50] == 255
        
    def test_preprocess_with_denoising(self):
        """Test preprocessing with Gaussian blur"""
        bbox = (0, 0, 100, 100)
        tracker = BrightnessTracker(bbox, denoising=True, kernel_size=5)
        
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame[50, 50] = [255, 255, 255]
        
        gray = tracker.preprocess_frame(frame)
        
        # Blur should spread intensity to neighbors
        assert gray[50, 50] < 255
        assert gray[49, 50] > 0
        assert gray[51, 50] > 0
        
    def test_find_brightest_point(self):
        """Test brightest point detection"""
        bbox = (0, 0, 100, 100)
        tracker = BrightnessTracker(bbox)
        
        # Create frame with known brightest point
        frame = np.zeros((100, 100), dtype=np.uint8)
        frame[30, 40] = 255
        
        result = tracker.find_brightest_point(frame)
        
        assert result['location'] == (40, 30)  # Note: (x, y) format
        assert result['intensity'] == 255
        assert result['frame_number'] == 1
        assert 'timestamp' in result
        
    def test_frame_counter_increment(self):
        """Test that frame counter increments correctly"""
        bbox = (0, 0, 100, 100)
        tracker = BrightnessTracker(bbox)
        
        frame = np.zeros((100, 100), dtype=np.uint8)
        
        result1 = tracker.find_brightest_point(frame)
        result2 = tracker.find_brightest_point(frame)
        result3 = tracker.find_brightest_point(frame)
        
        assert result1['frame_number'] == 1
        assert result2['frame_number'] == 2
        assert result3['frame_number'] == 3
        
    def test_find_bright_regions(self):
        """Test multiple bright regions detection"""
        bbox = (0, 0, 200, 200)
        tracker = BrightnessTracker(bbox)
        
        # Create frame with multiple bright spots
        frame = np.zeros((200, 200), dtype=np.uint8)
        
        # Bright region 1 (brighter)
        frame[30:40, 30:40] = 200
        frame[35, 35] = 255
        
        # Bright region 2 (dimmer)
        frame[100:110, 100:110] = 150
        frame[105, 105] = 180
        
        regions = tracker.find_bright_regions(frame, min_area=50)
        
        # Should find both regions, sorted by intensity
        assert len(regions) >= 2
        
        # Check first region is brighter
        assert regions[0]['intensity'] > regions[1]['intensity']
        
        # Check structure
        for region in regions:
            assert 'location' in region
            assert 'intensity' in region
            assert 'bbox' in region
            assert 'area' in region
            
    def test_calculate_fps(self):
        """Test FPS calculation"""
        bbox = (0, 0, 100, 100)
        tracker = BrightnessTracker(bbox)
        
        # Simulate 30 frames in 1 second
        fps = tracker.calculate_fps(elapsed_time=1.0, num_frames=30)
        
        assert fps == 30.0
        assert tracker.fps == 30.0
        
    def test_fps_zero_time(self):
        """Test FPS calculation with zero elapsed time"""
        bbox = (0, 0, 100, 100)
        tracker = BrightnessTracker(bbox)
        
        fps = tracker.calculate_fps(elapsed_time=0.0, num_frames=30)
        
        assert tracker.fps == 0.0


class TestRegionSelector:
    """Tests for RegionSelector class"""
    
    def test_initialization(self):
        """Test RegionSelector initialization"""
        selector = RegionSelector()
        assert selector.bbox is None
        
    # Note: Interactive GUI testing requires additional setup
    # and is typically done manually or with specialized tools


def test_synthetic_data_workflow():
    """Integration test with synthetic data"""
    # Create synthetic time-series
    bbox = (0, 0, 100, 100)
    tracker = BrightnessTracker(bbox)
    
    results = []
    
    # Simulate photobleaching: exponential decay
    for i in range(100):
        frame = np.zeros((100, 100), dtype=np.uint8)
        
        # Decreasing brightness
        brightness = int(255 * np.exp(-i * 0.02))
        frame[50, 50] = brightness
        
        result = tracker.find_brightest_point(frame)
        results.append(result)
        
    # Check that brightness decreases
    brightnesses = [r['intensity'] for r in results]
    
    assert brightnesses[0] > brightnesses[-1]
    assert all(brightnesses[i] >= brightnesses[i+1] 
               for i in range(len(brightnesses)-1))
    
    # Check frame numbers
    assert results[0]['frame_number'] == 1
    assert results[-1]['frame_number'] == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
