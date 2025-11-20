"""
Unit tests for FluoTrack analysis module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from fluotrack.analysis import DataLogger, BrightnessAnalyzer


class TestDataLogger:
    """Tests for DataLogger class"""
    
    def test_initialization(self):
        """Test logger initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = DataLogger(output_dir=tmpdir, prefix='test')
            
            assert logger.filename.exists()
            assert logger.filename.suffix == '.csv'
            assert 'test' in logger.filename.name
            
    def test_csv_header(self):
        """Test that CSV has correct header"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = DataLogger(output_dir=tmpdir)
            
            df = pd.read_csv(logger.filename)
            
            expected_columns = ['timestamp', 'frame_number', 'x', 'y', 
                              'brightness', 'notes']
            assert list(df.columns) == expected_columns
            
    def test_log_point(self):
        """Test logging a single data point"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = DataLogger(output_dir=tmpdir)
            
            data = {
                'timestamp': '2025-01-17T12:00:00',
                'frame_number': 1,
                'location': (100, 200),
                'intensity': 250.5
            }
            
            logger.log_point(data, notes='test_note')
            
            # Read back
            df = pd.read_csv(logger.filename)
            
            assert len(df) == 1
            assert df.iloc[0]['x'] == 100
            assert df.iloc[0]['y'] == 200
            assert df.iloc[0]['brightness'] == 250.5
            assert df.iloc[0]['notes'] == 'test_note'
            
    def test_log_multiple_points(self):
        """Test logging multiple data points"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = DataLogger(output_dir=tmpdir)
            
            for i in range(10):
                data = {
                    'timestamp': f'2025-01-17T12:00:0{i}',
                    'frame_number': i+1,
                    'location': (i*10, i*20),
                    'intensity': 200.0 + i
                }
                logger.log_point(data)
                
            df = pd.read_csv(logger.filename)
            
            assert len(df) == 10
            assert df['frame_number'].tolist() == list(range(1, 11))
            
    def test_log_regions(self):
        """Test logging multiple regions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = DataLogger(output_dir=tmpdir)
            
            regions = [
                {'location': (10, 20), 'intensity': 250},
                {'location': (30, 40), 'intensity': 200},
                {'location': (50, 60), 'intensity': 180}
            ]
            
            logger.log_regions(regions, frame_number=1)
            
            df = pd.read_csv(logger.filename)
            
            assert len(df) == 3
            assert all(df['notes'].str.startswith('region_'))


class TestBrightnessAnalyzer:
    """Tests for BrightnessAnalyzer class"""
    
    @pytest.fixture
    def sample_data_file(self):
        """Create a sample data file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', 
                                        delete=False) as f:
            f.write('timestamp,frame_number,x,y,brightness,notes\n')
            
            # Generate synthetic photobleaching data
            for i in range(100):
                timestamp = f'2025-01-17T12:00:{i:02d}'
                brightness = 255 * np.exp(-i * 0.01)  # Exponential decay
                x = 100 + np.random.randint(-5, 6)
                y = 100 + np.random.randint(-5, 6)
                
                f.write(f'{timestamp},{i+1},{x},{y},{brightness:.2f},\n')
                
            filepath = f.name
            
        yield filepath
        
        # Cleanup
        Path(filepath).unlink()
        
    def test_load_data(self, sample_data_file):
        """Test data loading"""
        analyzer = BrightnessAnalyzer(sample_data_file)
        
        assert analyzer.data is not None
        assert len(analyzer.data) == 100
        assert 'brightness' in analyzer.data.columns
        
    def test_compute_statistics(self, sample_data_file):
        """Test statistics computation"""
        analyzer = BrightnessAnalyzer(sample_data_file)
        stats = analyzer.compute_statistics()
        
        assert 'mean_brightness' in stats
        assert 'std_brightness' in stats
        assert 'min_brightness' in stats
        assert 'max_brightness' in stats
        assert 'median_brightness' in stats
        assert 'total_frames' in stats
        assert 'duration_seconds' in stats
        
        # Check ranges
        assert 0 < stats['mean_brightness'] < 255
        assert 0 < stats['std_brightness']
        assert stats['min_brightness'] < stats['max_brightness']
        assert stats['total_frames'] == 100
        
    def test_detect_photobleaching(self, sample_data_file):
        """Test photobleaching detection"""
        analyzer = BrightnessAnalyzer(sample_data_file)
        bleaching = analyzer.detect_photobleaching(window_size=10)
        
        assert 'slope' in bleaching
        assert 'is_bleaching' in bleaching
        assert 'half_life_frames' in bleaching
        
        # Should detect bleaching (negative slope)
        assert bleaching['slope'] < 0
        assert bleaching['is_bleaching'] is True
        assert bleaching['half_life_frames'] is not None
        assert bleaching['half_life_frames'] > 0
        
    def test_analyze_trajectory(self, sample_data_file):
        """Test trajectory analysis"""
        analyzer = BrightnessAnalyzer(sample_data_file)
        trajectory = analyzer.analyze_trajectory()
        
        assert 'mean_displacement' in trajectory
        assert 'std_displacement' in trajectory
        assert 'total_distance' in trajectory
        assert 'confinement_radius' in trajectory
        assert 'center' in trajectory
        
        # Check reasonable values (small random walk)
        assert 0 < trajectory['mean_displacement'] < 10
        assert trajectory['confinement_radius'] < 20
        assert len(trajectory['center']) == 2
        
    def test_generate_report(self, sample_data_file):
        """Test report generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = BrightnessAnalyzer(sample_data_file)
            
            output_file = Path(tmpdir) / 'report.xlsx'
            analyzer.generate_report(str(output_file))
            
            assert output_file.exists()
            
            # Check sheets
            excel_file = pd.ExcelFile(output_file)
            sheets = excel_file.sheet_names
            
            assert 'Raw Data' in sheets
            assert 'Statistics' in sheets
            assert 'Photobleaching' in sheets
            assert 'Trajectory' in sheets


def test_end_to_end_workflow():
    """Integration test: log data then analyze"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Log some data
        logger = DataLogger(output_dir=tmpdir, prefix='integration')
        
        for i in range(50):
            data = {
                'timestamp': f'2025-01-17T12:00:{i:02d}',
                'frame_number': i+1,
                'location': (100, 100),
                'intensity': 250 - i * 2  # Linear decrease
            }
            logger.log_point(data)
            
        # Analyze
        analyzer = BrightnessAnalyzer(logger.filename)
        stats = analyzer.compute_statistics()
        
        assert stats['total_frames'] == 50
        assert stats['mean_brightness'] < 250
        
        # Should detect photobleaching
        bleaching = analyzer.detect_photobleaching(window_size=10)
        assert bleaching['is_bleaching'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
