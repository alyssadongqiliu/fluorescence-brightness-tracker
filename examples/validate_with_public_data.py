"""
Validation of FluoTrack using Cell Tracking Challenge datasets.

This script demonstrates FluoTrack's accuracy and performance using
publicly available benchmark datasets.

Dataset source: http://celltrackingchallenge.net/
"""

import cv2
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from fluotrack import BrightnessTracker, DataLogger, BrightnessAnalyzer
import time


class FluoTrackValidator:
    """Validate FluoTrack on public datasets"""
    
    def __init__(self, dataset_path, output_dir='validation_results'):
        """
        Initialize validator.
        
        Parameters
        ----------
        dataset_path : str
            Path to dataset directory containing .tif files
        output_dir : str
            Output directory for results
        """
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load frames
        self.frames = sorted(self.dataset_path.glob("*.tif"))
        print(f"Found {len(self.frames)} frames in {dataset_path}")
        
    def run_tracking(self):
        """Run FluoTrack on all frames"""
        print("\n" + "="*60)
        print("Running FluoTrack on dataset...")
        print("="*60)
        
        results = []
        processing_times = []
        
        for i, frame_path in enumerate(self.frames):
            start_time = time.time()
            
            # Load frame
            frame = cv2.imread(str(frame_path), cv2.IMREAD_GRAYSCALE)
            
            if frame is None:
                print(f"Warning: Could not read {frame_path}")
                continue
            
            # Apply Gaussian blur (matching FluoTrack preprocessing)
            denoised = cv2.GaussianBlur(frame, (5, 5), 0)
            
            # Find brightest point
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(denoised)
            
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            results.append({
                'frame': i,
                'filename': frame_path.name,
                'brightness': float(max_val),
                'x': int(max_loc[0]),
                'y': int(max_loc[1]),
                'processing_time': processing_time
            })
            
            if (i + 1) % 10 == 0:
                print(f"Processed {i+1}/{len(self.frames)} frames...")
        
        self.results_df = pd.DataFrame(results)
        
        # Calculate FPS
        avg_time = np.mean(processing_times)
        fps = 1.0 / avg_time if avg_time > 0 else 0
        
        print(f"\n✓ Tracking complete!")
        print(f"  Average processing time: {avg_time*1000:.2f} ms/frame")
        print(f"  Average FPS: {fps:.1f}")
        
        return self.results_df
    
    def analyze_photobleaching(self):
        """Analyze photobleaching characteristics"""
        print("\n" + "="*60)
        print("Photobleaching Analysis")
        print("="*60)
        
        brightness = self.results_df['brightness'].values
        frames = self.results_df['frame'].values
        
        # Test for photobleaching (decreasing trend)
        correlation = np.corrcoef(frames, brightness)[0, 1]
        
        if correlation < -0.3:  # Negative correlation suggests bleaching
            print("  Photobleaching detected!")
            
            # Fit exponential decay: I(t) = A * exp(-k*t) + C
            def exp_decay(t, A, k, C):
                return A * np.exp(-k * t) + C
            
            try:
                # Initial guess
                p0 = [brightness[0] - brightness[-1], 0.01, brightness[-1]]
                
                # Fit
                popt, pcov = curve_fit(exp_decay, frames, brightness, p0=p0)
                A, k, C = popt
                
                # Calculate half-life
                half_life = np.log(2) / k if k > 0 else np.inf
                
                # Calculate R²
                fitted = exp_decay(frames, *popt)
                ss_res = np.sum((brightness - fitted) ** 2)
                ss_tot = np.sum((brightness - np.mean(brightness)) ** 2)
                r_squared = 1 - (ss_res / ss_tot)
                
                print(f"  Exponential decay fit:")
                print(f"    Half-life: {half_life:.1f} frames")
                print(f"    Decay rate: {k:.4f} per frame")
                print(f"    R² = {r_squared:.3f}")
                
                return {
                    'detected': True,
                    'half_life': half_life,
                    'decay_rate': k,
                    'r_squared': r_squared,
                    'fitted_curve': fitted
                }
                
            except Exception as e:
                print(f"  Could not fit exponential decay: {e}")
                return {'detected': True, 'half_life': None}
        else:
            print("  No significant photobleaching detected")
            return {'detected': False}
    
    def analyze_trajectory(self):
        """Analyze spatial trajectory"""
        print("\n" + "="*60)
        print("Trajectory Analysis")
        print("="*60)
        
        x = self.results_df['x'].values
        y = self.results_df['y'].values
        
        # Calculate displacements
        dx = np.diff(x)
        dy = np.diff(y)
        distances = np.sqrt(dx**2 + dy**2)
        
        # Center of mass
        x_center = np.mean(x)
        y_center = np.mean(y)
        
        # Radial distances from center
        radial = np.sqrt((x - x_center)**2 + (y - y_center)**2)
        
        # Confinement radius (95th percentile)
        confinement_radius = np.percentile(radial, 95)
        
        stats = {
            'mean_displacement': float(np.mean(distances)),
            'std_displacement': float(np.std(distances)),
            'total_distance': float(np.sum(distances)),
            'max_displacement': float(np.max(distances)),
            'confinement_radius': float(confinement_radius),
            'center': (float(x_center), float(y_center))
        }
        
        print(f"  Mean displacement: {stats['mean_displacement']:.2f} pixels/frame")
        print(f"  Total distance traveled: {stats['total_distance']:.1f} pixels")
        print(f"  Confinement radius (95%): {stats['confinement_radius']:.1f} pixels")
        print(f"  Center of trajectory: ({stats['center'][0]:.1f}, {stats['center'][1]:.1f})")
        
        return stats
    
    def compute_statistics(self):
        """Compute summary statistics"""
        print("\n" + "="*60)
        print("Summary Statistics")
        print("="*60)
        
        brightness = self.results_df['brightness']
        
        stats = {
            'n_frames': len(self.results_df),
            'mean_brightness': float(brightness.mean()),
            'std_brightness': float(brightness.std()),
            'min_brightness': float(brightness.min()),
            'max_brightness': float(brightness.max()),
            'median_brightness': float(brightness.median()),
            'cv_brightness': float(brightness.std() / brightness.mean())  # Coefficient of variation
        }
        
        print(f"  Frames analyzed: {stats['n_frames']}")
        print(f"  Brightness (mean ± std): {stats['mean_brightness']:.1f} ± {stats['std_brightness']:.1f}")
        print(f"  Brightness range: {stats['min_brightness']:.1f} - {stats['max_brightness']:.1f}")
        print(f"  Coefficient of variation: {stats['cv_brightness']:.2%}")
        
        return stats
    
    def generate_plots(self, photobleaching_result=None):
        """Generate validation plots"""
        print("\n" + "="*60)
        print("Generating plots...")
        print("="*60)
        
        fig = plt.figure(figsize=(14, 10))
        
        # 1. Brightness over time
        ax1 = plt.subplot(2, 2, 1)
        ax1.plot(self.results_df['frame'], self.results_df['brightness'], 
                'o-', markersize=3, alpha=0.6, label='Measured')
        
        # Add fitted curve if photobleaching detected
        if photobleaching_result and 'fitted_curve' in photobleaching_result:
            ax1.plot(self.results_df['frame'], photobleaching_result['fitted_curve'],
                    'r--', linewidth=2, label='Exponential fit')
        
        ax1.set_xlabel('Frame Number', fontsize=11)
        ax1.set_ylabel('Brightness (a.u.)', fontsize=11)
        ax1.set_title('Brightness Over Time', fontsize=12, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Trajectory
        ax2 = plt.subplot(2, 2, 2)
        
        # Color by time
        scatter = ax2.scatter(
            self.results_df['x'], self.results_df['y'],
            c=self.results_df['frame'],
            cmap='viridis',
            s=20,
            alpha=0.6
        )
        
        # Mark start and end
        ax2.plot(self.results_df['x'].iloc[0], self.results_df['y'].iloc[0],
                'go', markersize=12, label='Start', zorder=5)
        ax2.plot(self.results_df['x'].iloc[-1], self.results_df['y'].iloc[-1],
                'ro', markersize=12, label='End', zorder=5)
        
        ax2.set_xlabel('X Position (pixels)', fontsize=11)
        ax2.set_ylabel('Y Position (pixels)', fontsize=11)
        ax2.set_title('Spatial Trajectory', fontsize=12, fontweight='bold')
        ax2.legend()
        ax2.set_aspect('equal')
        
        cbar = plt.colorbar(scatter, ax=ax2)
        cbar.set_label('Frame Number', fontsize=10)
        
        # 3. Displacement histogram
        ax3 = plt.subplot(2, 2, 3)
        
        x = self.results_df['x'].values
        y = self.results_df['y'].values
        dx = np.diff(x)
        dy = np.diff(y)
        distances = np.sqrt(dx**2 + dy**2)
        
        ax3.hist(distances, bins=30, alpha=0.7, edgecolor='black')
        ax3.axvline(np.mean(distances), color='r', linestyle='--', 
                   linewidth=2, label=f'Mean: {np.mean(distances):.2f}')
        ax3.set_xlabel('Displacement (pixels)', fontsize=11)
        ax3.set_ylabel('Frequency', fontsize=11)
        ax3.set_title('Frame-to-Frame Displacement Distribution', fontsize=12, fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Processing time
        ax4 = plt.subplot(2, 2, 4)
        
        times_ms = self.results_df['processing_time'] * 1000
        ax4.plot(self.results_df['frame'], times_ms, 'o-', markersize=3, alpha=0.6)
        ax4.axhline(times_ms.mean(), color='r', linestyle='--', 
                   linewidth=2, label=f'Mean: {times_ms.mean():.2f} ms')
        ax4.set_xlabel('Frame Number', fontsize=11)
        ax4.set_ylabel('Processing Time (ms)', fontsize=11)
        ax4.set_title('Processing Performance', fontsize=12, fontweight='bold')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save
        output_file = self.output_dir / 'validation_results.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved plot: {output_file}")
        
        plt.close()
    
    def save_results(self):
        """Save results to files"""
        print("\n" + "="*60)
        print("Saving results...")
        print("="*60)
        
        # CSV
        csv_file = self.output_dir / 'tracking_results.csv'
        self.results_df.to_csv(csv_file, index=False)
        print(f"  ✓ Saved CSV: {csv_file}")
        
        # Excel with summary
        excel_file = self.output_dir / 'validation_report.xlsx'
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            self.results_df.to_excel(writer, sheet_name='Raw Data', index=False)
        print(f"  ✓ Saved Excel: {excel_file}")
    
    def run_full_validation(self):
        """Run complete validation pipeline"""
        print("\n" + "="*70)
        print("  FLUOTRACK VALIDATION ON PUBLIC DATASET")
        print("="*70)
        print(f"\nDataset: {self.dataset_path.name}")
        print(f"Output directory: {self.output_dir}")
        
        # Track all frames
        self.run_tracking()
        
        # Analyze
        stats = self.compute_statistics()
        photobleaching = self.analyze_photobleaching()
        trajectory = self.analyze_trajectory()
        
        # Generate outputs
        self.generate_plots(photobleaching)
        self.save_results()
        
        print("\n" + "="*70)
        print("  VALIDATION COMPLETE!")
        print("="*70)
        print(f"\nResults saved to: {self.output_dir}/")
        print("  - validation_results.png (plots)")
        print("  - tracking_results.csv (raw data)")
        print("  - validation_report.xlsx (summary)")
        
        return {
            'statistics': stats,
            'photobleaching': photobleaching,
            'trajectory': trajectory
        }


def main():
    """Main validation script"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate FluoTrack on Cell Tracking Challenge dataset'
    )
    parser.add_argument(
        'dataset',
        help='Path to dataset directory (containing .tif files)'
    )
    parser.add_argument(
        '--output',
        default='validation_results',
        help='Output directory (default: validation_results)'
    )
    
    args = parser.parse_args()
    
    # Run validation
    validator = FluoTrackValidator(args.dataset, args.output)
    results = validator.run_full_validation()
    
    print("\n✓ Done!")


if __name__ == '__main__':
    # Example usage:
    # python validate_with_public_data.py path/to/Fluo-N2DH-SIM+/01
    
    main()
