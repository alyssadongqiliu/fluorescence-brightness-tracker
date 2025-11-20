# Contributing to FluoTrack

Thank you for your interest in contributing to FluoTrack! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful and constructive in all interactions. We aim to create a welcoming environment for researchers and developers of all backgrounds.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on GitHub with:

1. **Description**: Clear description of the bug
2. **Steps to reproduce**: Minimal example that triggers the bug
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Environment**: Python version, OS, FluoTrack version
6. **Screenshots**: If applicable

### Suggesting Enhancements

Feature requests are welcome! Please open an issue with:

1. **Use case**: Describe the scientific problem this would solve
2. **Proposed solution**: How you envision the feature working
3. **Alternatives**: Other approaches you've considered

### Pull Requests

1. **Fork the repository** and create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards below

3. **Add tests** for new functionality

4. **Update documentation** if you change APIs or add features

5. **Run tests** to ensure nothing breaks:
   ```bash
   pytest tests/
   ```

6. **Submit a pull request** with:
   - Clear description of changes
   - Link to related issues
   - Screenshots/examples if applicable

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints for function arguments and returns
- Maximum line length: 88 characters (Black formatter)

### Code Formatting

We use [Black](https://github.com/psf/black) for code formatting:

```bash
black src/fluotrack/
```

### Documentation

- All public functions/classes need docstrings
- Use NumPy-style docstrings
- Include examples in docstrings for complex functions

Example:
```python
def track_brightness(roi: Tuple[int, int, int, int], 
                    duration: int = 60) -> pd.DataFrame:
    """
    Track brightness in a region of interest.
    
    Parameters
    ----------
    roi : tuple of int
        Region of interest as (x1, y1, x2, y2)
    duration : int, default=60
        Tracking duration in seconds
        
    Returns
    -------
    pd.DataFrame
        DataFrame with columns: timestamp, x, y, brightness
        
    Examples
    --------
    >>> roi = (100, 100, 500, 500)
    >>> data = track_brightness(roi, duration=30)
    >>> print(data.head())
    """
```

### Testing

- Write unit tests for all new functionality
- Aim for >80% code coverage
- Use descriptive test names: `test_<function>_<scenario>`
- Use fixtures for common test data

Example:
```python
def test_find_brightest_point_with_single_spot():
    """Test brightest point detection with one bright pixel"""
    frame = np.zeros((100, 100), dtype=np.uint8)
    frame[50, 50] = 255
    
    result = find_brightest_point(frame)
    
    assert result['location'] == (50, 50)
    assert result['intensity'] == 255
```

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/alyssadongqiliu/fluotrack.git
   cd fluotrack
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode**:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run tests**:
   ```bash
   pytest tests/ -v --cov=fluotrack
   ```

## Project Structure

```
fluotrack/
├── src/fluotrack/        # Source code
│   ├── __init__.py
│   ├── tracker.py        # Core tracking algorithms
│   ├── analysis.py       # Data analysis
│   └── app.py           # GUI application
├── tests/               # Unit tests
├── examples/            # Example scripts and data
├── docs/                # Documentation
├── paper.md            # JOSS paper
└── README.md
```

## Commit Messages

Use clear, descriptive commit messages:

- Start with a verb in present tense: "Add", "Fix", "Update"
- First line: brief summary (<50 chars)
- Blank line
- Detailed explanation if needed

Example:
```
Add photobleaching half-life calculation

Implement exponential fitting to estimate photobleaching
half-life from intensity time series. Includes validation
against synthetic data.

Closes #42
```

## Questions?

Feel free to open an issue for questions about contributing or development setup.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
