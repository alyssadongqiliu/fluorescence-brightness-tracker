# Quick Start Guide for JOSS Submission

This guide will help you prepare FluoTrack for JOSS submission in ~2-3 hours.

## Step 1: Personal Information (5 minutes)

### Get Your ORCID ID
1. Go to https://orcid.org/register
2. Create an account (takes 2 minutes)
3. Copy your ORCID (format: 0000-0000-0000-0000)

### Update Files
Replace placeholders in these files:
- `paper.md`: Add your ORCID and full name
- `pyproject.toml`: Update author info
- `README.md`: Update contact information
- `src/fluotrack/__init__.py`: Update author info
- `LICENSE`: Add your full name

```bash
# Quick find-and-replace (adjust names as needed)
grep -r "Alyssa \[Your Last Name\]" . --exclude-dir=.git
grep -r "your.email@unc.edu" . --exclude-dir=.git
```

## Step 2: GitHub Repository (10 minutes)

### Create Repository
1. Go to https://github.com/new
2. Name: `fluotrack`
3. Description: "Real-time fluorescence brightness tracking for microscopy"
4. Make it **Public**
5. Don't initialize with README (we already have one)

### Push Code
```bash
cd /path/to/fluorescence-brightness-tracker
git init
git add .
git commit -m "Initial commit: FluoTrack for JOSS submission"
git branch -M main
git remote add origin https://github.com/[your-username]/fluotrack.git
git push -u origin main
```

### Create Release
```bash
git tag -a v0.1.0 -m "Version 0.1.0 - Initial JOSS submission"
git push origin v0.1.0
```

## Step 3: Testing (15 minutes)

### Install and Test
```bash
# Create fresh virtual environment
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# Install package
cd fluorescence-brightness-tracker
pip install -e ".[dev]"

# Run tests
pytest tests/ -v --cov=fluotrack

# Should see: All tests passed ✓
```

### Fix Any Test Failures
If tests fail:
1. Read error messages carefully
2. Fix issues in source code
3. Commit fixes: `git commit -am "Fix: [describe fix]"`
4. Push: `git push`

## Step 4: Example Data (30 minutes - Optional but Recommended)

### Create Sample Images
If you have microscopy data from Kerry's lab:

```bash
mkdir -p examples/sample_data
# Copy 1-2 small sample images (< 5 MB total)
# Or create synthetic fluorescence images
```

Add to README:
```markdown
## Example Data

Sample fluorescence microscopy images are provided in `examples/sample_data/`.
To run with example data:
\`\`\`python
python examples/basic_tracking.py
\`\`\`
```

### Or Skip This
You can submit without example images. Just make sure to note in `paper.md`:
"Example usage with synthetic data is provided in the examples/ directory."

## Step 5: Zenodo DOI (10 minutes)

### Link to Zenodo
1. Go to https://zenodo.org/ and log in with GitHub
2. Go to https://zenodo.org/account/settings/github/
3. Find your `fluotrack` repository
4. Toggle it ON
5. Go back to GitHub and create a release (you already did this in Step 2)
6. Zenodo automatically creates a DOI

### Add DOI Badge
Once you have the DOI:

Edit `README.md` and update the DOI badge:
```markdown
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
```

Replace `XXXXXXX` with your actual Zenodo DOI number.

## Step 6: Review Paper (20 minutes)

### Check Paper Content
Read through `paper.md` and verify:
- [ ] Summary clearly explains what FluoTrack does
- [ ] Statement of need explains the problem it solves
- [ ] Mentions your work in Kerry Bloom's lab
- [ ] References are appropriate
- [ ] Comparison table is accurate

### Compile Paper (Check Formatting)
```bash
# Install pandoc if needed
# Ubuntu: sudo apt-get install pandoc
# macOS: brew install pandoc
# Windows: https://pandoc.org/installing.html

# Compile to check formatting
pandoc paper.md -o paper.pdf --bibliography=paper.bib --citeproc
open paper.pdf  # Check that it looks good
```

### Update References
If you want to add more references (e.g., your own research):

Edit `paper.bib`:
```bibtex
@article{YourPaper2025,
  title={Your Paper Title},
  author={Your Name and Co-authors},
  journal={Journal Name},
  year={2025},
  doi={10.xxxx/xxxxx}
}
```

Then cite in `paper.md`:
```markdown
Our approach builds on chromatin dynamics studies [@Bloom2018; @YourPaper2025].
```

## Step 7: Final Checks (15 minutes)

### Run Through Checklist
Open `JOSS_CHECKLIST.md` and verify all items:

**Critical items:**
- [ ] Repository is public on GitHub
- [ ] LICENSE file present (MIT)
- [ ] README has installation instructions
- [ ] Tests pass
- [ ] paper.md and paper.bib files present
- [ ] ORCID in paper.md
- [ ] Zenodo DOI obtained

### Test Installation from GitHub
```bash
# In a NEW terminal/environment
python -m venv test_install
source test_install/bin/activate

# Install from GitHub
pip install git+https://github.com/[your-username]/fluotrack.git

# Try to run
python -c "from fluotrack import BrightnessTracker; print('Success!')"
```

## Step 8: Submit to JOSS (10 minutes)

### Go to JOSS
1. Visit https://joss.theoj.org/
2. Click "Submit a paper"
3. Log in with GitHub
4. Fill in the form:
   - **Repository URL**: https://github.com/[your-username]/fluotrack
   - **Version**: v0.1.0
   - **Archive DOI**: Your Zenodo DOI
   - **Software license**: MIT
   - Check the boxes confirming requirements

5. Submit!

### What Happens Next?
1. **Editor assignment** (1-2 weeks)
   - An editor will be assigned to your paper
   - They'll do a quick check

2. **Reviewer assignment** (2-4 weeks)
   - Usually 2 reviewers
   - They'll test installation, review code, read paper

3. **Review** (2-8 weeks)
   - Reviewers will post comments as GitHub issues
   - You respond and make changes
   - Iterate until accepted

4. **Acceptance** 🎉
   - Paper published on JOSS website
   - Citable DOI assigned

## Common Issues and Solutions

### "Tests fail on Windows"
- Make sure all file paths use `Path` from `pathlib`
- Check for platform-specific issues in OpenCV

### "Reviewer can't install package"
- Test installation yourself first
- Make sure all dependencies are in `pyproject.toml`
- Provide clear error messages if deps missing

### "Paper needs more scientific context"
- Explain how this was used in Kerry's lab research
- Add more detail about TAD simulations
- Cite relevant chromatin dynamics papers

### "Need more examples"
- Add examples/basic_tracking.py (already included)
- Consider adding examples/photobleaching_analysis.py
- Add screenshots to README

## Time-Saving Tips

### If You're Short on Time
Priority order:
1. **Must do:** Steps 1, 2, 3, 8 (Setup, GitHub, Testing, Submit)
2. **Should do:** Steps 5, 6 (Zenodo, Paper review)
3. **Nice to have:** Step 4 (Example data)

You can always add examples and improve documentation during the review process.

### Get Help
- **Kerry Bloom**: Ask for feedback on paper content
- **Lab members**: Ask them to beta test installation
- **JOSS Gitter**: https://gitter.im/openjournals/joss for questions

## After Submission

### During Review
Check GitHub issues daily for reviewer comments:
```bash
# Set up email notifications
# Go to https://github.com/[your-username]/fluotrack/settings/notifications
```

### Responding to Reviews
- Be polite and professional
- Respond within 2 weeks
- If you disagree, explain why respectfully
- Make requested changes and reference them

Example response:
```markdown
Thank you for the helpful feedback!

1. Added more docstrings to public functions (commit abc123)
2. Expanded installation instructions in README (commit def456)
3. Regarding the photobleaching algorithm, we chose linear regression
   over exponential fitting because... [explain reasoning]
```

## Success Metrics

After acceptance:
- ✓ Citable publication for your CV
- ✓ DOI for citing in future papers
- ✓ Open source contribution to bioimaging community
- ✓ Evidence of software development skills for PhD applications

## Questions?

If you get stuck:
1. Check `JOSS_CHECKLIST.md` for detailed requirements
2. Look at recently published JOSS papers for examples
3. Ask me (Claude) for help!
4. Post on JOSS Gitter: https://gitter.im/openjournals/joss

---

**Estimated total time: 2-3 hours**
- Setup & GitHub: 30 min
- Testing: 30 min  
- Zenodo & Paper: 45 min
- Final checks & submit: 45 min

Good luck! You've got this! 🚀
