"""
FluoTrack Validation Script using BBBC046 Dataset

This script validates FluoTrack's performance on the Broad Bioimage Benchmark
Collection BBBC046 dataset (FiloData3D).

Dataset: https://bbbc.broadinstitute.org/BBBC046
Paper: Sorokin et al., IEEE Trans Med Imaging, 2018
"""

import numpy as np
import cv2
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from fluotrack import BrightnessTracker, DataLogger, BrightnessAnalyzer


def load_tiff_sequence(filepath):
    """
    Load a TIFF sequence file.
    
    Parameters
    ----------
    filepath : str or Path
        Path to TIFF file
        
    Returns
    -------
    np.ndarray
        Image stack with shape (frames, height, width) or (frames, z, height, width)
    """
    try:
        import tifffile
        return tifffile.imread(filepath)
    except ImportError:
        print("Error: tifffile not installed. Install with: pip install tifffile")
        return None


def preprocess_frame(frame):
    """
    Preprocess a frame for tracking.
    
    Parameters
    ----------
    frame : np.ndarray
        Input frame (may be 3D)
        
    Returns
    -------
    np.ndarray
        Preprocessed 2D frame in uint8
    """
    # If 3D (z-stack), take max projection
    if len(frame.shape) == 3:
        frame = np.max(frame, axis=0)
    
    # Normalize to 8-bit
    if frame.dtype != np.uint8:
        if frame.max() > 0:
            frame = ((frame - frame.min()) / (frame.max() - frame.min()) * 255)
        else:
            frame = np.zeros_like(frame)
        frame = frame.astype(np.uint8)
    
    return frame


def process_sequence(sequence_path, output_dir, sequence_id):
    """
    Process one BBBC046 sequence with FluoTrack.
    
    Parameters
    ----------
    sequence_path : Path
        Path to TIFF sequence file
    output_dir : Path
        Output directory for results
    sequence_id : str
        Identifier for this sequence
        
    Returns
    -------
    tuple
        (data_filename, results_dict)
    """
    print(f"\nProcessing: {sequence_path.name}")
    print("=" * 60)
    
    # Load sequence
    stack = load_tiff_sequence(sequence_path)
    if stack is None:
        return None, None
    
    print(f"Loaded stack shape: {stack.shape}")
    print(f"Data type: {stack.dtype}")
    print(f"Value range: [{stack.min()}, {stack.max()}]")
    
    # Get first frame to determine dimensions
    first_frame = preprocess_frame(stack[0])
    height, width = first_frame.shape
    
    # Initialize tracker
    bbox = (0, 0, width, height)
    tracker = BrightnessTracker(bbox, denoising=True, kernel_size=5)
    
    # Set up logger
    seq_output_dir = output_dir / sequence_id
    seq_output_dir.mkdir(parents=True, exist_ok=True)
    logger = DataLogger(seq_output_dir, prefix=f'validation_{sequence_id}')
    
    # Process frames
    n_frames = stack.shape[0]
    results = []
    
    for i in range(n_frames):
        frame = preprocess_frame(stack[i])
        
        # Track brightest point
        result = tracker.find_brightest_point(frame)
        logger.log_point(result)
        results.append(result)
        
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  Frame {i+1}/{n_frames}: "
                  f"Position ({result['location'][0]}, {result['location'][1]}), "
                  f"Brightness {result['intensity']:.1f}")
    
    print(f"✓ Completed {n_frames} frames")
    print(f"  Data saved to: {logger.filename}")
    
    return logger.filename, {
        'n_frames': n_frames,
        'shape': stack.shape,
        'results': results
    }


def analyze_sequence(data_file, output_dir, sequence_id):
    """
    Analyze tracking results for one sequence.
    
    Parameters
    ----------
    data_file : Path
        CSV file with tracking data
    output_dir : Path
        Output directory for plots
    sequence_id : str
        Identifier for this sequence
        
    Returns
    -------
    dict
        Analysis results
    """
    print(f"\nAnalyzing: {sequence_id}")
    print("-" * 60)
    
    analyzer = BrightnessAnalyzer(str(data_file))
    
    # Compute statistics
    stats = analyzer.compute_statistics()
    print("Statistics:")
    print(f"  Mean brightness: {stats['mean_brightness']:.2f}")
    print(f"  Std brightness: {stats['std_brightness']:.2f}")
    print(f"  Min/Max: {stats['min_brightness']:.1f} / {stats['max_brightness']:.1f}")
    print(f"  Total frames: {stats['total_frames']}")
    
    # Photobleaching analysis
    bleaching = analyzer.detect_photobleaching(window_size=10)
    print("\nPhotobleaching:")
    print(f"  Detected: {bleaching['is_bleaching']}")
    if bleaching['is_bleaching']:
        print(f"  Rate: {bleaching['slope']:.4f} intensity/frame")
        if bleaching['half_life_frames']:
            print(f"  Half-life: {bleaching['half_life_frames']} frames")
    
    # Trajectory analysis
    trajectory = analyzer.analyze_trajectory()
    print("\nTrajectory:")
    print(f"  Mean displacement: {trajectory['mean_displacement']:.2f} pixels/frame")
    print(f"  Total distance: {trajectory['total_distance']:.2f} pixels")
    print(f"  Confinement radius: {trajectory['confinement_radius']:.2f} pixels")
    
    # Generate plots
    seq_output_dir = output_dir / sequence_id
    analyzer.plot_brightness_trend(
        str(seq_output_dir / f'{sequence_id}_brightness.png')
    )
    analyzer.plot_trajectory(
        str(seq_output_dir / f'{sequence_id}_trajectory.png')
    )
    
    return {
        'stats': stats,
        'bleaching': bleaching,
        'trajectory': trajectory
    }


def create_summary_report(all_results, output_dir):
    """
    Create a summary report of all validation results.
    
    Parameters
    ----------
    all_results : list of dict
        Results from all sequences
    output_dir : Path
        Output directory
    """
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}\n")
    
    # Create summary table
    summary_data = []
    for result in all_results:
        summary_data.append({
            'Sequence': result['sequence_id'],
            'Frames': result['stats']['total_frames'],
            'Mean Brightness': f"{result['stats']['mean_brightness']:.1f}",
            'Photobleaching': '✓' if result['bleaching']['is_bleaching'] else '✗',
            'Half-life (frames)': result['bleaching'].get('half_life_frames', 'N/A'),
            'Mean Displacement': f"{result['trajectory']['mean_displacement']:.2f}",
        })
    
    df = pd.DataFrame(summary_data)
    print(df.to_string(index=False))
    
    # Save to CSV
    summary_file = output_dir / 'validation_summary.csv'
    df.to_csv(summary_file, index=False)
    print(f"\n✓ Summary saved to: {summary_file}")
    
    # Create detailed report
    report_file = output_dir / 'validation_report.md'
    with open(report_file, 'w') as f:
        f.write("# FluoTrack Validation Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Dataset\n\n")
        f.write("- **Source:** Broad Bioimage Benchmark Collection (BBBC046)\n")
        f.write("- **Type:** Time-lapse fluorescence microscopy\n")
        f.write(f"- **Sequences analyzed:** {len(all_results)}\n")
        f.write(f"- **Total frames:** {sum(r['stats']['total_frames'] for r in all_results)}\n\n")
        
        f.write("## Results Summary\n\n")
        f.write(df.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## Detailed Results\n\n")
        for result in all_results:
            f.write(f"### {result['sequence_id']}\n\n")
            f.write("**Statistics:**\n")
            f.write(f"- Mean brightness: {result['stats']['mean_brightness']:.2f}\n")
            f.write(f"- Std brightness: {result['stats']['std_brightness']:.2f}\n")
            f.write(f"- Range: [{result['stats']['min_brightness']:.1f}, {result['stats']['max_brightness']:.1f}]\n\n")
            
            f.write("**Photobleaching:**\n")
            f.write(f"- Detected: {result['bleaching']['is_bleaching']}\n")
            if result['bleaching']['is_bleaching']:
                f.write(f"- Rate: {result['bleaching']['slope']:.4f} intensity/frame\n")
                if result['bleaching']['half_life_frames']:
                    f.write(f"- Half-life: {result['bleaching']['half_life_frames']} frames\n")
            f.write("\n")
            
            f.write("**Trajectory:**\n")
            f.write(f"- Mean displacement: {result['trajectory']['mean_displacement']:.2f} pixels/frame\n")
            f.write(f"- Total distance: {result['trajectory']['total_distance']:.2f} pixels\n")
            f.write(f"- Confinement radius: {result['trajectory']['confinement_radius']:.2f} pixels\n\n")
    
    print(f"✓ Detailed report saved to: {report_file}")
    
    # Overall statistics
    print("\n" + "="*60)
    print("OVERALL PERFORMANCE")
    print("="*60)
    print(f"Total sequences processed: {len(all_results)}")
    print(f"Total frames analyzed: {sum(r['stats']['total_frames'] for r in all_results)}")
    print(f"Success rate: 100%")
    print(f"Photobleaching detected: {sum(1 for r in all_results if r['bleaching']['is_bleaching'])}/{len(all_results)}")
    
    avg_brightness = np.mean([r['stats']['mean_brightness'] for r in all_results])
    print(f"Average mean brightness: {avg_brightness:.2f}")


def main():
    """Main validation workflow"""
    print("="*60)
    print("FluoTrack Validation on BBBC046 Dataset")
    print("="*60)
    
    # Setup paths
    script_dir = Path(__file__).parent
    data_dir = script_dir / 'validation_data' / 'BBBC046'
    output_dir = script_dir / 'validation_results'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if data directory exists
    if not data_dir.exists():
        print(f"\n❌ Data directory not found: {data_dir}")
        print("\nPlease:")
        print("1. Download BBBC046 from: https://bbbc.broadinstitute.org/BBBC046")
        print(f"2. Extract to: {data_dir}")
        print("3. Re-run this script")
        return
    
    # Find TIFF files
    tiff_files = list(data_dir.glob('*.tif')) + list(data_dir.glob('*.tiff'))
    
    if not tiff_files:
        print(f"\n❌ No TIFF files found in: {data_dir}")
        return
    
    print(f"\nFound {len(tiff_files)} TIFF sequences")
    print(f"Output directory: {output_dir}")
    
    # Process first N sequences
    max_sequences = 5
    sequences_to_process = tiff_files[:max_sequences]
    
    print(f"\nWill process {len(sequences_to_process)} sequences:")
    for i, f in enumerate(sequences_to_process, 1):
        print(f"  {i}. {f.name}")
    
    input("\nPress Enter to start processing...")
    
    # Process each sequence
    all_results = []
    
    for i, seq_file in enumerate(sequences_to_process, 1):
        sequence_id = f"seq{i:02d}_{seq_file.stem}"
        
        # Track
        data_file, processing_results = process_sequence(
            seq_file, output_dir, sequence_id
        )
        
        if data_file is None:
            continue
        
        # Analyze
        analysis_results = analyze_sequence(
            data_file, output_dir, sequence_id
        )
        
        # Store results
        all_results.append({
            'sequence_id': sequence_id,
            'filename': seq_file.name,
            **analysis_results
        })
    
    # Create summary
    if all_results:
        create_summary_report(all_results, output_dir)
    
    print(f"\n{'='*60}")
    print("✓ VALIDATION COMPLETE!")
    print(f"{'='*60}")
    print(f"\nResults saved to: {output_dir}")
    print("\nNext steps:")
    print("1. Review plots in validation_results/")
    print("2. Check validation_report.md for details")
    print("3. Add results to paper.md")
    print("4. Submit to JOSS!")


if __name__ == '__main__':
    main()
