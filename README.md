# FluoTrack: Multi-Target Fluorescence Tracker

Automated multi-target fluorescence tracking with adaptive detection and the Hungarian algorithm.

## Features

- 🎯 Automatic multi-target detection
- 🔗 Hungarian algorithm for optimal tracking
- 📊 Individual + population-level analysis
- 💡 Photobleaching detection

## Installation
```bash
pip install -e .
pip install scipy tifffile
```

## Quick Start
```python
from fluotrack.enhanced_tracker import EnhancedFluoTracker

tracker = EnhancedFluoTracker()
spots = tracker.process_frame(frame, timestamp)
```

## Validation

See `examples/validate_enhanced.py` for validation on synthetic data.

## Citation

Paper submitted to Journal of Open Source Software.

## License

MIT License

