"""
Download and prepare Cell Tracking Challenge datasets for validation.

This script downloads recommended datasets for validating FluoTrack.
"""

import urllib.request
import zipfile
from pathlib import Path
import sys


# Recommended datasets for validation
DATASETS = {
    'Fluo-N2DH-SIM+': {
        'url': 'http://data.celltrackingchallenge.net/training-datasets/Fluo-N2DH-SIM+.zip',
        'description': 'Simulated fluorescent nuclei (2D + time)',
        'size': '~50 MB',
        'best_for': 'Accuracy validation with ground truth'
    },
    'Fluo-N2DL-HeLa': {
        'url': 'http://data.celltrackingchallenge.net/training-datasets/Fluo-N2DL-HeLa.zip',
        'description': 'HeLa cells expressing H2B-GFP (2D + time)',
        'size': '~120 MB',
        'best_for': 'Photobleaching analysis, real microscopy data'
    },
    'Fluo-C2DL-MSC': {
        'url': 'http://data.celltrackingchallenge.net/training-datasets/Fluo-C2DL-MSC.zip',
        'description': 'Mesenchymal stem cells (2D + time, phase contrast)',
        'size': '~200 MB',
        'best_for': 'Low-contrast conditions'
    }
}


def download_with_progress(url, output_path):
    """Download file with progress bar"""
    
    def reporthook(blocknum, blocksize, totalsize):
        """Progress reporter"""
        downloaded = blocknum * blocksize
        percent = min(downloaded * 100.0 / totalsize, 100.0)
        
        # Progress bar
        bar_length = 50
        filled = int(bar_length * percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        size_mb = downloaded / (1024 * 1024)
        total_mb = totalsize / (1024 * 1024)
        
        sys.stdout.write(f'\r  Progress: |{bar}| {percent:.1f}% ({size_mb:.1f}/{total_mb:.1f} MB)')
        sys.stdout.flush()
    
    print(f"Downloading from {url}...")
    urllib.request.urlretrieve(url, output_path, reporthook)
    print("\n  ✓ Download complete!")


def extract_zip(zip_path, extract_to):
    """Extract zip file"""
    print(f"Extracting {zip_path.name}...")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    print(f"  ✓ Extracted to {extract_to}/")


def download_dataset(dataset_name, output_dir='datasets'):
    """
    Download and prepare a Cell Tracking Challenge dataset.
    
    Parameters
    ----------
    dataset_name : str
        Name of dataset (e.g., 'Fluo-N2DH-SIM+')
    output_dir : str
        Directory to save datasets (default: 'datasets')
    """
    
    if dataset_name not in DATASETS:
        print(f"Error: Unknown dataset '{dataset_name}'")
        print(f"Available datasets: {', '.join(DATASETS.keys())}")
        return False
    
    dataset_info = DATASETS[dataset_name]
    
    print("\n" + "="*70)
    print(f"  Downloading: {dataset_name}")
    print("="*70)
    print(f"Description: {dataset_info['description']}")
    print(f"Size: {dataset_info['size']}")
    print(f"Best for: {dataset_info['best_for']}")
    print()
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Download
    zip_filename = f"{dataset_name}.zip"
    zip_path = output_path / zip_filename
    
    if zip_path.exists():
        print(f"Found existing {zip_filename}, skipping download...")
    else:
        download_with_progress(dataset_info['url'], zip_path)
    
    # Extract
    extract_to = output_path / dataset_name
    if extract_to.exists():
        print(f"Dataset already extracted at {extract_to}/")
    else:
        extract_zip(zip_path, output_path)
    
    # Find sequence directories
    sequences = sorted(extract_to.glob("01*"))
    
    if sequences:
        print("\n" + "="*70)
        print("  Dataset Ready!")
        print("="*70)
        print(f"Location: {extract_to}/")
        print(f"Sequences found: {len(sequences)}")
        print("\nTo validate FluoTrack, run:")
        print(f"  python examples/validate_with_public_data.py {sequences[0]}")
        print()
        
        return True
    else:
        print("\nWarning: Could not find sequence directories")
        return False


def download_recommended_datasets():
    """Download all recommended datasets for comprehensive validation"""
    
    print("\n" + "="*70)
    print("  FLUOTRACK VALIDATION DATASETS")
    print("="*70)
    print("\nThis will download the following datasets:")
    print()
    
    for name, info in DATASETS.items():
        print(f"  • {name}")
        print(f"    {info['description']}")
        print(f"    Size: {info['size']}")
        print(f"    Use: {info['best_for']}")
        print()
    
    total_size = "~370 MB"
    print(f"Total download size: {total_size}")
    print()
    
    response = input("Download all datasets? [y/N]: ").strip().lower()
    
    if response in ['y', 'yes']:
        success_count = 0
        for dataset_name in DATASETS.keys():
            if download_dataset(dataset_name):
                success_count += 1
        
        print("\n" + "="*70)
        print(f"  Downloaded {success_count}/{len(DATASETS)} datasets successfully!")
        print("="*70)
    else:
        print("\nSkipping download. To download individual datasets:")
        print("  python download_datasets.py <dataset_name>")
        print()
        print("Available datasets:")
        for name in DATASETS.keys():
            print(f"  - {name}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Download Cell Tracking Challenge datasets for FluoTrack validation'
    )
    parser.add_argument(
        'dataset',
        nargs='?',
        help='Dataset name (leave empty for interactive mode)'
    )
    parser.add_argument(
        '--output',
        default='datasets',
        help='Output directory (default: datasets)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available datasets'
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable datasets for validation:")
        print()
        for name, info in DATASETS.items():
            print(f"  {name}")
            print(f"    Description: {info['description']}")
            print(f"    Size: {info['size']}")
            print(f"    Best for: {info['best_for']}")
            print()
        return
    
    if args.dataset:
        # Download specific dataset
        download_dataset(args.dataset, args.output)
    else:
        # Interactive mode
        download_recommended_datasets()


if __name__ == '__main__':
    # Example usage:
    # python download_datasets.py                    # Interactive mode
    # python download_datasets.py Fluo-N2DH-SIM+    # Download specific dataset
    # python download_datasets.py --list             # List available datasets
    
    main()
