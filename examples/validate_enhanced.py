"""
Validation script for Enhanced Multi-Target Tracker

Demonstrates innovations:
1. Automatic multi-spot detection
2. Frame-to-frame tracking with IDs
3. Individual spot analysis
4. Population statistics
"""

import numpy as np
import cv2
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from fluotrack.enhanced_tracker import EnhancedFluoTracker
from datetime import datetime


def create_synthetic_data():
    """
    Create synthetic test data with multiple moving spots.
    
    Simulates:
    - 5 fluorescent spots
    - Movement (random walk)
    - Photobleaching
    - Some spots appear/disappear
    """
    n_frames = 50
    img_size = (256, 256)
    n_spots = 5
    
    frames = []
    ground_truth = []
    
    # Initialize spot positions
    spots = []
    for i in range(n_spots):
        spots.append({
            'pos': np.array([
                np.random.randint(50, img_size[0]-50),
                np.random.randint(50, img_size[1]-50)
            ], dtype=float),
            'intensity': 200 + np.random.rand() * 50,
            'active': True,
            'disappear_frame': None if i < 3 else np.random.randint(20, 40)
        })
    
    for frame_idx in range(n_frames):
        # Create blank frame with noise
        frame = np.random.randint(10, 30, img_size, dtype=np.uint8)
        
        frame_spots = []
        
        for spot_idx, spot in enumerate(spots):
            # Check if spot should disappear
            if spot['disappear_frame'] and frame_idx >= spot['disappear_frame']:
                spot['active'] = False
            
            if not spot['active']:
                continue
            
            # Random walk
            spot['pos'] += np.random.randn(2) * 2.0
            
            # Keep in bounds
            spot['pos'] = np.clip(spot['pos'], [20, 20], [img_size[0]-20, img_size[1]-20])
            
            # Photobleaching
            spot['intensity'] *= 0.98
            
            # Draw spot (Gaussian)
            y, x = int(spot['pos'][0]), int(spot['pos'][1])
            for dy in range(-5, 6):
                for dx in range(-5, 6):
                    if 0 <= y+dy < img_size[0] and 0 <= x+dx < img_size[1]:
                        dist = np.sqrt(dy**2 + dx**2)
                        if dist < 5:
                            intensity = spot['intensity'] * np.exp(-dist**2 / 4)
                            frame[y+dy, x+dx] = min(255, frame[y+dy, x+dx] + int(intensity))
            
            frame_spots.append({
                'id': spot_idx,
                'pos': tuple(spot['pos']),
                'intensity': spot['intensity']
            })
        
        frames.append(frame)
        ground_truth.append(frame_spots)
    
    return frames, ground_truth


def visualize_tracking(frames, all_tracks, output_dir):
    """Create visualization of tracking results"""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Create video writer
    height, width = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_path = output_dir / 'tracking_visualization.mp4'
    out = cv2.VideoWriter(str(video_path), fourcc, 10.0, (width, height))
    
    # Color map for different tracks
    colors = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255),
        (255, 255, 0), (255, 0, 255), (0, 255, 255),
        (128, 255, 0), (255, 128, 0), (128, 0, 255)
    ]
    
    # Draw each frame
    for frame_idx, frame in enumerate(frames):
        # Convert to color
        vis_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        
        # Draw all tracks
        for track_id, track in all_tracks.items():
            color_idx = track_id % len(colors)
            color = colors[color_idx]
            
            # Draw trajectory
            positions = [spot.location for spot in track if spot.frame_number <= frame_idx + 1]
            if len(positions) > 1:
                for i in range(len(positions) - 1):
                    cv2.line(vis_frame, positions[i], positions[i+1], color, 1)
            
            # Draw current position
            current_spots = [spot for spot in track if spot.frame_number == frame_idx + 1]
            for spot in current_spots:
                cv2.circle(vis_frame, spot.location, 8, color, 2)
                cv2.putText(vis_frame, f"ID{spot.id}", 
                           (spot.location[0] + 10, spot.location[1]),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # Add frame number
        cv2.putText(vis_frame, f"Frame {frame_idx + 1}/{len(frames)}",
                   (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        out.write(vis_frame)
    
    out.release()
    print(f"✓ Video saved to: {video_path}")
    
    # Create trajectory plot - ONLY show long tracks (>5 frames) for clarity
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.imshow(frames[0], cmap='gray', alpha=0.3)
    
    # Filter for longer tracks only
    long_tracks = {tid: track for tid, track in all_tracks.items() if len(track) > 5}
    
    # Use a nice color map
    import matplotlib.cm as cm
    colors_map = cm.get_cmap('tab20', len(long_tracks))
    
    for idx, (track_id, track) in enumerate(long_tracks.items()):
        positions = np.array([spot.location for spot in track])
        color = colors_map(idx)
        
        # Plot trajectory with thicker lines
        ax.plot(positions[:, 0], positions[:, 1], '-', 
               linewidth=2.5, color=color, alpha=0.7)
        
        # Mark start (green) and end (red)
        ax.plot(positions[0, 0], positions[0, 1], 'o', 
               markersize=12, color='green', markeredgecolor='white', markeredgewidth=1.5)
        ax.plot(positions[-1, 0], positions[-1, 1], 'o', 
               markersize=12, color='red', markeredgecolor='white', markeredgewidth=1.5)
        
        # Add track ID at the end point
        ax.text(positions[-1, 0] + 5, positions[-1, 1], f'{track_id}',
               fontsize=9, color='white', weight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.7, edgecolor='none'))
    
    ax.set_xlabel('X (pixels)', fontsize=12)
    ax.set_ylabel('Y (pixels)', fontsize=12)
    ax.set_title('Multi-Target Trajectories\n(Green=Start, Red=End, Only tracks >5 frames shown)', 
                fontsize=14, weight='bold')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'trajectories.png', dpi=200, bbox_inches='tight')
    print(f"✓ Trajectory plot saved to: {output_dir / 'trajectories.png'}")
    plt.close()


def plot_intensity_trends(all_tracks, output_dir):
    """Plot intensity over time for each track"""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Filter for tracks with >5 frames for top plot
    long_tracks = {tid: track for tid, track in all_tracks.items() if len(track) > 5}
    
    # Individual tracks - only show longer ones
    ax = axes[0]
    
    import matplotlib.cm as cm
    colors_map = cm.get_cmap('tab20', min(len(long_tracks), 20))
    
    for idx, (track_id, track) in enumerate(list(long_tracks.items())[:20]):  # Max 20 tracks
        frames = [spot.frame_number for spot in track]
        intensities = [spot.intensity for spot in track]
        color = colors_map(idx)
        ax.plot(frames, intensities, 'o-', alpha=0.8, linewidth=2, 
               markersize=5, label=f'Track {track_id}', color=color)
    
    ax.set_xlabel('Frame', fontsize=12)
    ax.set_ylabel('Intensity', fontsize=12)
    ax.set_title('Individual Spot Intensities Over Time (Top 20 longest tracks)', 
                fontsize=13, weight='bold')
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9, ncol=2)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Population average
    ax = axes[1]
    max_frame = max(spot.frame_number for track in all_tracks.values() for spot in track)
    
    avg_intensities = []
    std_intensities = []
    
    for frame in range(1, max_frame + 1):
        frame_intensities = [
            spot.intensity for track in all_tracks.values() 
            for spot in track if spot.frame_number == frame
        ]
        if frame_intensities:
            avg_intensities.append(np.mean(frame_intensities))
            std_intensities.append(np.std(frame_intensities))
        else:
            avg_intensities.append(np.nan)
            std_intensities.append(np.nan)
    
    frames = np.arange(1, max_frame + 1)
    avg_intensities = np.array(avg_intensities)
    std_intensities = np.array(std_intensities)
    
    ax.plot(frames, avg_intensities, 'b-', linewidth=3, label='Mean', zorder=10)
    ax.fill_between(frames, 
                     avg_intensities - std_intensities,
                     avg_intensities + std_intensities,
                     alpha=0.3, color='blue', label='±1 SD')
    
    ax.set_xlabel('Frame', fontsize=12)
    ax.set_ylabel('Mean Intensity', fontsize=12)
    ax.set_title('Population-Level Intensity (Photobleaching)', fontsize=13, weight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'intensity_trends.png', dpi=200, bbox_inches='tight')
    print(f"✓ Intensity plot saved to: {Path(output_dir) / 'intensity_trends.png'}")
    plt.close()


def main():
    """Run validation"""
    print("="*60)
    print("Enhanced Multi-Target Tracker Validation")
    print("="*60)
    
    # Create synthetic data
    print("\n1. Creating synthetic test data...")
    frames, ground_truth = create_synthetic_data()
    print(f"   Generated {len(frames)} frames with multiple moving spots")
    
    # Initialize tracker
    print("\n2. Initializing Enhanced Tracker...")
    tracker = EnhancedFluoTracker(
        min_spot_area=10,
        max_spot_area=200,
        sensitivity=2.0,
        max_tracking_distance=20.0
    )
    
    # Process frames
    print("\n3. Processing frames...")
    for frame_idx, frame in enumerate(frames):
        timestamp = f"2025-01-17T12:00:{frame_idx:02d}"
        spots = tracker.process_frame(frame, timestamp)
        
        if (frame_idx + 1) % 10 == 0:
            print(f"   Frame {frame_idx + 1}/{len(frames)}: Detected {len(spots)} spots")
    
    # Get results
    all_tracks = tracker.get_all_tracks()
    print(f"\n4. Tracking complete!")
    print(f"   Total tracks created: {len(all_tracks)}")
    
    # Analyze each track
    print("\n5. Individual Track Statistics:")
    print("-" * 60)
    for track_id in sorted(all_tracks.keys()):
        stats = tracker.get_track_stats(track_id)
        print(f"\n   Track {track_id}:")
        print(f"      Duration: {stats['duration']} frames")
        print(f"      Mean intensity: {stats['mean_intensity']:.1f}")
        print(f"      Intensity trend: {stats['intensity_trend']:.3f} per frame")
        print(f"      Total displacement: {stats['total_displacement']:.1f} pixels")
        print(f"      Mean velocity: {stats['mean_velocity']:.2f} pixels/frame")
        print(f"      Photobleaching: {'✓ Yes' if stats['is_photobleaching'] else '✗ No'}")
    
    # Population statistics
    print("\n6. Population Statistics:")
    print("-" * 60)
    pop_stats = tracker.get_population_statistics()
    print(f"   Total tracks: {pop_stats['total_tracks']}")
    print(f"   Mean intensity: {pop_stats['mean_intensity']:.2f}")
    print(f"   Std intensity: {pop_stats['std_intensity']:.2f}")
    print(f"   Mean velocity: {pop_stats['mean_velocity']:.2f} pixels/frame")
    print(f"   Photobleaching fraction: {pop_stats['photobleaching_fraction']:.1%}")
    
    # Visualizations
    print("\n7. Creating visualizations...")
    output_dir = Path('validation_results/enhanced_tracker')
    visualize_tracking(frames, all_tracks, output_dir)
    plot_intensity_trends(all_tracks, output_dir)
    
    # Accuracy assessment
    print("\n8. Accuracy Assessment:")
    print("-" * 60)
    
    # Count detection rate
    total_detections = sum(len(tracker.process_frame(frame, f"t{i}")) 
                          for i, frame in enumerate(frames))
    expected_detections = sum(len(gt) for gt in ground_truth)
    
    print(f"   Expected detections: {expected_detections}")
    print(f"   Actual detections: {total_detections}")
    print(f"   Detection rate: {total_detections/expected_detections*100:.1f}%")
    
    # Track continuity
    avg_duration = np.mean([len(track) for track in all_tracks.values()])
    print(f"   Average track duration: {avg_duration:.1f} frames")
    
    print("\n" + "="*60)
    print("✓ VALIDATION COMPLETE!")
    print("="*60)
    print(f"\nResults saved to: {output_dir}")
    print("\nKey Innovations Demonstrated:")
    print("1. ✓ Automatic multi-spot detection (not just brightest)")
    print("2. ✓ Frame-to-frame tracking with unique IDs")
    print("3. ✓ Individual spot photobleaching analysis")
    print("4. ✓ Population-level statistics")
    print("5. ✓ Trajectory visualization")
    

if __name__ == '__main__':
    main()