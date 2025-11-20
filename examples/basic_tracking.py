"""
Example: Basic brightness tracking workflow

This script demonstrates how to use FluoTrack for basic fluorescence
brightness tracking and analysis.
"""

import time
import cv2
from fluotrack import BrightnessTracker, RegionSelector, DataLogger, BrightnessAnalyzer


def main():
    print("FluoTrack Example: Basic Brightness Tracking")
    print("=" * 50)
    
    # Step 1: Select region of interest
    print("\n1. Select region of interest...")
    print("   (Draw a box around your fluorescent object)")
    
    selector = RegionSelector()
    bbox = selector.select()
    
    if bbox is None:
        print("Selection cancelled. Exiting.")
        return
        
    print(f"   Selected region: {bbox}")
    
    # Step 2: Initialize tracker and logger
    print("\n2. Initializing tracker...")
    tracker = BrightnessTracker(
        bbox=bbox,
        denoising=True,
        kernel_size=5
    )
    
    logger = DataLogger(
        output_dir='results',
        prefix='example'
    )
    
    print(f"   Logging to: {logger.filename}")
    
    # Step 3: Track for 60 seconds
    print("\n3. Tracking brightness (press 'q' to stop)...")
    
    duration = 60  # seconds
    start_time = time.time()
    frame_count = 0
    fps_update_interval = 30
    
    try:
        while (time.time() - start_time) < duration:
            # Capture and process frame
            frame = tracker.capture_frame()
            gray = tracker.preprocess_frame(frame)
            
            # Find brightest point
            result = tracker.find_brightest_point(gray)
            
            # Log data
            logger.log_point(result)
            
            # Update FPS
            frame_count += 1
            if frame_count % fps_update_interval == 0:
                elapsed = time.time() - start_time
                fps = tracker.calculate_fps(elapsed, fps_update_interval)
                frame_count = 0
                start_time = time.time()
            
            # Visualize
            loc = result['location']
            cv2.circle(frame, loc, 10, (0, 255, 0), 2)
            cv2.putText(
                frame, 
                f"FPS: {tracker.fps:.1f} | Brightness: {result['intensity']:.0f}",
                (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 255, 0), 2
            )
            
            # Show elapsed time
            elapsed = time.time() - start_time
            remaining = max(0, duration - elapsed)
            cv2.putText(
                frame,
                f"Time remaining: {remaining:.0f}s",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 255, 0), 2
            )
            
            cv2.imshow("Brightness Tracking (press 'q' to stop)", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("   Stopped by user")
                break
                
    except KeyboardInterrupt:
        print("\n   Stopped by user (Ctrl+C)")
    finally:
        cv2.destroyAllWindows()
        
    print(f"   Tracked {tracker.frame_count} frames")
    
    # Step 4: Analyze results
    print("\n4. Analyzing data...")
    
    analyzer = BrightnessAnalyzer(str(logger.filename))
    
    # Basic statistics
    stats = analyzer.compute_statistics()
    print("\n   Statistics:")
    print(f"   - Mean brightness: {stats['mean_brightness']:.2f}")
    print(f"   - Std brightness: {stats['std_brightness']:.2f}")
    print(f"   - Min/Max: {stats['min_brightness']:.2f} / {stats['max_brightness']:.2f}")
    print(f"   - Total frames: {stats['total_frames']}")
    print(f"   - Duration: {stats['duration_seconds']:.2f} seconds")
    print(f"   - Average FPS: {stats['average_fps']:.2f}")
    
    # Photobleaching analysis
    bleaching = analyzer.detect_photobleaching()
    print("\n   Photobleaching Analysis:")
    print(f"   - Detected: {bleaching['is_bleaching']}")
    if bleaching['is_bleaching']:
        print(f"   - Rate: {bleaching['slope']:.4f} intensity/frame")
        if bleaching['half_life_frames']:
            print(f"   - Half-life: {bleaching['half_life_frames']} frames")
    
    # Trajectory analysis
    trajectory = analyzer.analyze_trajectory()
    print("\n   Trajectory Analysis:")
    print(f"   - Mean displacement: {trajectory['mean_displacement']:.2f} pixels/frame")
    print(f"   - Total distance: {trajectory['total_distance']:.2f} pixels")
    print(f"   - Confinement radius: {trajectory['confinement_radius']:.2f} pixels")
    print(f"   - Center: ({trajectory['center'][0]:.1f}, {trajectory['center'][1]:.1f})")
    
    # Step 5: Generate reports
    print("\n5. Generating reports...")
    
    # Plots
    analyzer.plot_brightness_trend(output_file='results/brightness_trend.png')
    print("   - Saved brightness_trend.png")
    
    analyzer.plot_trajectory(output_file='results/trajectory.png')
    print("   - Saved trajectory.png")
    
    # Excel report
    analyzer.generate_report('results/analysis_report.xlsx')
    print("   - Saved analysis_report.xlsx")
    
    print("\n" + "=" * 50)
    print("Analysis complete! Check the 'results' folder.")
    print("=" * 50)


if __name__ == '__main__':
    main()
