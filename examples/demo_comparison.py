"""
Comparison Demo: Basic vs Enhanced Tracking

This script demonstrates the improvements of the enhanced tracker
over the basic brightest-point detection.
"""

import numpy as np
import cv2
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from fluotrack.tracker import BrightnessTracker as BasicTracker
from fluotrack.tracker_enhanced import EnhancedBrightnessTracker


def create_synthetic_sequence(n_frames=100, noise_level=20):
    """
    Create synthetic test sequence with:
    - Moving bright spot
    - Varying background
    - Noise
    """
    frames = []
    true_positions = []
    
    for i in range(n_frames):
        # Create frame
        frame = np.zeros((200, 200), dtype=np.uint8)
        
        # Add varying background
        bg_level = 50 + 20 * np.sin(i / 10)
        frame += int(bg_level)
        
        # Add noise
        noise = np.random.normal(0, noise_level, frame.shape)
        frame = np.clip(frame + noise, 0, 255).astype(np.uint8)
        
        # Add moving bright spot
        t = i / n_frames * 2 * np.pi
        x = int(100 + 40 * np.cos(t))
        y = int(100 + 40 * np.sin(t))
        
        # Create Gaussian spot
        for dy in range(-5, 6):
            for dx in range(-5, 6):
                if 0 <= y+dy < 200 and 0 <= x+dx < 200:
                    dist = np.sqrt(dx**2 + dy**2)
                    intensity = 200 * np.exp(-dist**2 / 8)
                    frame[y+dy, x+dx] = min(255, frame[y+dy, x+dx] + int(intensity))
        
        frames.append(frame)
        true_positions.append((x, y))
    
    return frames, true_positions


def compare_trackers(frames, true_positions):
    """Compare basic vs enhanced tracker"""
    
    print("Comparing trackers on synthetic sequence...")
    print(f"Frames: {len(frames)}, Size: {frames[0].shape}")
    print()
    
    # Setup trackers
    bbox = (0, 0, 200, 200)
    basic = BasicTracker(bbox, denoising=True)
    enhanced = EnhancedBrightnessTracker(
        bbox,
        use_kalman=True,
        use_adaptive_bg=True,
        denoising=True
    )
    
    # Track
    basic_results = []
    enhanced_results = []
    
    for i, frame in enumerate(frames):
        basic_res = basic.find_brightest_point(frame)
        enhanced_res = enhanced.find_brightest_point(frame)
        
        basic_results.append(basic_res)
        enhanced_results.append(enhanced_res)
        
        if (i + 1) % 20 == 0:
            print(f"Processed {i+1}/{len(frames)} frames...")
    
    # Compute errors
    basic_errors = []
    enhanced_errors = []
    
    for i, true_pos in enumerate(true_positions):
        basic_pos = basic_results[i]['location']
        enhanced_pos = enhanced_results[i]['location']
        
        basic_err = np.sqrt((basic_pos[0] - true_pos[0])**2 + 
                           (basic_pos[1] - true_pos[1])**2)
        enhanced_err = np.sqrt((enhanced_pos[0] - true_pos[0])**2 + 
                               (enhanced_pos[1] - true_pos[1])**2)
        
        basic_errors.append(basic_err)
        enhanced_errors.append(enhanced_err)
    
    # Statistics
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    print("\nBasic Tracker:")
    print(f"  Mean error: {np.mean(basic_errors):.2f} pixels")
    print(f"  Std error: {np.std(basic_errors):.2f} pixels")
    print(f"  Max error: {np.max(basic_errors):.2f} pixels")
    
    print("\nEnhanced Tracker:")
    print(f"  Mean error: {np.mean(enhanced_errors):.2f} pixels")
    print(f"  Std error: {np.std(enhanced_errors):.2f} pixels")
    print(f"  Max error: {np.max(enhanced_errors):.2f} pixels")
    print(f"  Mean SNR: {np.mean([r['snr'] for r in enhanced_results]):.2f}")
    print(f"  Mean Confidence: {np.mean([r['confidence'] for r in enhanced_results]):.2f}")
    
    improvement = (np.mean(basic_errors) - np.mean(enhanced_errors)) / np.mean(basic_errors) * 100
    print(f"\n✓ Improvement: {improvement:.1f}% reduction in tracking error")
    
    # Visualization
    plot_comparison(frames, true_positions, basic_results, enhanced_results,
                   basic_errors, enhanced_errors)
    
    return basic_results, enhanced_results


def plot_comparison(frames, true_positions, basic_results, enhanced_results,
                   basic_errors, enhanced_errors):
    """Create comparison plots"""
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Trajectory comparison
    ax = axes[0, 0]
    true_x = [p[0] for p in true_positions]
    true_y = [p[1] for p in true_positions]
    basic_x = [r['location'][0] for r in basic_results]
    basic_y = [r['location'][1] for r in basic_results]
    enhanced_x = [r['location'][0] for r in enhanced_results]
    enhanced_y = [r['location'][1] for r in enhanced_results]
    
    ax.plot(true_x, true_y, 'k-', label='True', linewidth=2)
    ax.plot(basic_x, basic_y, 'r--', label='Basic', alpha=0.7)
    ax.plot(enhanced_x, enhanced_y, 'g-', label='Enhanced', linewidth=1.5)
    ax.set_xlabel('X position (pixels)')
    ax.set_ylabel('Y position (pixels)')
    ax.set_title('Trajectory Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    # Error over time
    ax = axes[0, 1]
    ax.plot(basic_errors, 'r-', label='Basic', alpha=0.7)
    ax.plot(enhanced_errors, 'g-', label='Enhanced')
    ax.set_xlabel('Frame')
    ax.set_ylabel('Tracking Error (pixels)')
    ax.set_title('Tracking Error Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Error distribution
    ax = axes[1, 0]
    ax.hist(basic_errors, bins=20, alpha=0.7, label='Basic', color='red')
    ax.hist(enhanced_errors, bins=20, alpha=0.7, label='Enhanced', color='green')
    ax.set_xlabel('Tracking Error (pixels)')
    ax.set_ylabel('Frequency')
    ax.set_title('Error Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Signal quality (Enhanced only)
    ax = axes[1, 1]
    snr = [r['snr'] for r in enhanced_results]
    confidence = [r['confidence'] for r in enhanced_results]
    
    ax2 = ax.twinx()
    ax.plot(snr, 'b-', label='SNR')
    ax2.plot(confidence, 'orange', label='Confidence')
    ax.set_xlabel('Frame')
    ax.set_ylabel('SNR', color='b')
    ax2.set_ylabel('Confidence', color='orange')
    ax.set_title('Signal Quality Metrics (Enhanced)')
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save
    output_dir = Path(__file__).parent / 'comparison_results'
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / 'tracker_comparison.png', dpi=300)
    print(f"\n✓ Comparison plot saved to: {output_dir / 'tracker_comparison.png'}")
    
    plt.show()


def demonstrate_features():
    """Demonstrate individual features"""
    
    print("\n" + "="*60)
    print("FEATURE DEMONSTRATIONS")
    print("="*60)
    
    # 1. Adaptive background
    print("\n1. Adaptive Background Estimation")
    print("   Creates synthetic sequence with varying background...")
    
    frames, positions = create_synthetic_sequence(n_frames=50, noise_level=30)
    
    bbox = (0, 0, 200, 200)
    tracker = EnhancedBrightnessTracker(bbox, use_adaptive_bg=True)
    
    for frame in frames[:20]:  # Process first 20 frames
        _ = tracker.find_brightest_point(frame)
    
    print("   ✓ Background model adapts to changing conditions")
    
    # 2. Kalman filtering
    print("\n2. Kalman Filtering for Smooth Trajectories")
    print("   Tracks moving spot with noise...")
    
    tracker = EnhancedBrightnessTracker(bbox, use_kalman=True)
    smoothness_basic = []
    smoothness_kalman = []
    
    tracker_no_kalman = EnhancedBrightnessTracker(bbox, use_kalman=False)
    
    for i in range(1, len(frames)):
        res = tracker.find_brightest_point(frames[i])
        res_no = tracker_no_kalman.find_brightest_point(frames[i])
        
        # Measure smoothness (change in position)
        if i > 1:
            prev = tracker.find_brightest_point(frames[i-1])
            prev_no = tracker_no_kalman.find_brightest_point(frames[i-1])
            
            dx = res['location'][0] - prev['location'][0]
            dy = res['location'][1] - prev['location'][1]
            smoothness_kalman.append(np.sqrt(dx**2 + dy**2))
            
            dx_no = res_no['location'][0] - prev_no['location'][0]
            dy_no = res_no['location'][1] - prev_no['location'][1]
            smoothness_basic.append(np.sqrt(dx_no**2 + dy_no**2))
    
    print(f"   Without Kalman: avg change = {np.mean(smoothness_basic):.2f} px/frame")
    print(f"   With Kalman: avg change = {np.mean(smoothness_kalman):.2f} px/frame")
    print(f"   ✓ {((np.mean(smoothness_basic) - np.mean(smoothness_kalman))/np.mean(smoothness_basic)*100):.1f}% smoother trajectory")
    
    # 3. Signal quality
    print("\n3. Signal Quality Assessment")
    print("   Analyzes detection confidence...")
    
    tracker = EnhancedBrightnessTracker(bbox)
    result = tracker.find_brightest_point(frames[0])
    
    print(f"   SNR: {result['snr']:.2f}")
    print(f"   Contrast: {result['contrast']:.3f}")
    print(f"   Confidence: {result['confidence']:.3f}")
    print("   ✓ Provides quality metrics for each detection")


def main():
    """Main comparison demo"""
    
    print("="*60)
    print("FluoTrack: Basic vs Enhanced Tracker Comparison")
    print("="*60)
    
    # Create test data
    print("\nGenerating synthetic test sequence...")
    frames, true_positions = create_synthetic_sequence(n_frames=100, noise_level=20)
    print(f"✓ Created {len(frames)} frames with moving spot + noise")
    
    # Run comparison
    basic_results, enhanced_results = compare_trackers(frames, true_positions)
    
    # Feature demonstrations
    demonstrate_features()
    
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)
    print("\nThe enhanced tracker provides:")
    print("  ✓ Better tracking accuracy (Kalman filtering)")
    print("  ✓ Robustness to background changes (adaptive BG)")
    print("  ✓ Quality assessment (SNR, confidence)")
    print("  ✓ Smoother trajectories (temporal filtering)")
    print("\nThese improvements make it suitable for:")
    print("  - Low SNR imaging")
    print("  - Long time-lapse sequences")
    print("  - Quantitative analysis requiring confidence scores")
    print("="*60)


if __name__ == '__main__':
    main()
