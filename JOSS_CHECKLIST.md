# JOSS Submission Checklist

This checklist covers all requirements for submitting to the Journal of Open Source Software (JOSS).

## Pre-submission Requirements

### Repository Setup
- [ ] Code hosted on GitHub (or similar) with public access
- [ ] Repository has a clear README.md
- [ ] Software has an OSI-approved open source license (✓ MIT)
- [ ] Software has a version number/tag (e.g., v0.1.0)

### Documentation
- [ ] README includes:
  - [ ] Statement of need / purpose
  - [ ] Installation instructions
  - [ ] Usage examples
  - [ ] Dependencies listed
  - [ ] Link to documentation
  - [ ] Citation information
- [ ] API documentation (docstrings in code)
- [ ] CONTRIBUTING.md file with contribution guidelines

### Testing
- [ ] Automated tests present
- [ ] Tests cover core functionality
- [ ] CI/CD setup (GitHub Actions, Travis, etc.)
- [ ] Tests pass on multiple Python versions
- [ ] Tests pass on multiple operating systems

### Paper (paper.md)
- [ ] Paper follows JOSS template
- [ ] Title is descriptive and concise
- [ ] Authors listed with affiliations and ORCID IDs
- [ ] Summary section (1-2 paragraphs)
- [ ] Statement of need section
- [ ] References section with paper.bib file
- [ ] Paper length: 250-1000 words (excluding references)

### Code Quality
- [ ] Code follows language conventions (PEP 8 for Python)
- [ ] Functions and classes have docstrings
- [ ] Code is well-structured and modular
- [ ] No major code quality issues (linting passes)

## JOSS-Specific Requirements

### Scientific Content
- [ ] Software has a clear research application
- [ ] Statement of need explains why this tool is needed
- [ ] Comparison with similar/existing tools
- [ ] Software adds value to the research community

### Functionality
- [ ] Software works as described
- [ ] Installation process is straightforward
- [ ] Examples run without errors
- [ ] Core functionality is complete

### Community Guidelines
- [ ] Clear contribution guidelines
- [ ] Issue tracker enabled
- [ ] Code of conduct (optional but recommended)
- [ ] Active maintenance planned

## Action Items Before Submission

### 1. Update Personal Information
- [ ] Replace placeholder name/email in all files
- [ ] Get ORCID ID: https://orcid.org/register
- [ ] Update author information in:
  - [ ] paper.md
  - [ ] pyproject.toml
  - [ ] README.md
  - [ ] LICENSE

### 2. Create GitHub Repository
```bash
# Create new repo on GitHub, then:
cd fluorescence-brightness-tracker
git init
git add .
git commit -m "Initial commit for JOSS submission"
git branch -M main
git remote add origin https://github.com/alyssadongqiliu/fluotrack.git
git push -u origin main
```

### 3. Get ORCID ID
- Visit https://orcid.org/register
- Create account
- Add to paper.md authors section

### 4. Tag a Release
```bash
git tag -a v0.1.0 -m "First release for JOSS submission"
git push origin v0.1.0
```

### 5. Run Tests Locally
```bash
cd fluorescence-brightness-tracker
pip install -e ".[dev]"
pytest tests/ -v --cov=fluotrack
```

### 6. Check Paper Formatting
```bash
# Install pandoc if not already installed
# Ubuntu/Debian:
sudo apt-get install pandoc pandoc-citeproc

# macOS:
brew install pandoc

# Compile paper to check formatting
cd fluorescence-brightness-tracker
pandoc paper.md -o paper.pdf --bibliography=paper.bib --citeproc
```

### 7. Get Zenodo DOI
- Link GitHub repo to Zenodo: https://zenodo.org/
- Create a release on GitHub
- Zenodo automatically creates DOI
- Add DOI badge to README.md

### 8. Optional: Add Example Data
- [ ] Create sample fluorescence microscopy images
- [ ] Add to examples/ directory
- [ ] Document in README how to use examples

### 9. Review JOSS Submission Guidelines
Read full guidelines: https://joss.readthedocs.io/en/latest/submitting.html

Key points:
- Software must be open source
- Authors must have made substantial contributions
- Paper should be 250-1000 words
- Code must be archived (Zenodo, Figshare, etc.)
- Statement of need is required

### 10. Submit to JOSS
1. Go to https://joss.theoj.org/
2. Click "Submit a Paper"
3. Fill in repository URL
4. Wait for editor assignment
5. Respond to reviewer comments

## Common Reviewer Comments to Address Proactively

### Documentation
- "Please add more examples"
  - ✓ Added examples/basic_tracking.py
  
- "API documentation is incomplete"
  - ✓ All public functions have NumPy-style docstrings

### Testing
- "Tests don't cover edge cases"
  - ✓ Added tests for invalid inputs, empty frames, etc.
  
- "No continuous integration"
  - ✓ GitHub Actions workflow added

### Paper
- "Statement of need is unclear"
  - ✓ Explicitly explains why real-time tracking matters
  
- "Missing comparison with existing tools"
  - ✓ Table comparing with ImageJ, TrackMate, CellProfiler

### Code Quality
- "Code organization could be improved"
  - ✓ Modular structure with tracker, analysis, app modules
  
- "Missing type hints"
  - ✓ Type hints added to all public functions

## Post-Submission

After submission, reviewers will:
1. Check that software works
2. Review paper quality
3. Test installation process
4. Verify tests pass
5. Check documentation completeness

Be prepared to:
- Respond to reviews within 2 weeks
- Make code improvements if requested
- Clarify paper content
- Add missing documentation

## Timeline

Typical JOSS review timeline:
- Editor assignment: 1-2 weeks
- Review process: 2-8 weeks (depends on responsiveness)
- Acceptance: After revisions addressed

Total time: Usually 1-3 months from submission to acceptance

## Resources

- JOSS website: https://joss.theoj.org/
- Submission guidelines: https://joss.readthedocs.io/en/latest/submitting.html
- Review criteria: https://joss.readthedocs.io/en/latest/review_criteria.html
- Paper template: https://github.com/openjournals/joss-papers
- Example papers: Browse published papers at https://joss.theoj.org/papers

## Questions?

If you have questions:
1. Check JOSS FAQ: https://joss.readthedocs.io/en/latest/faq.html
2. Look at recently published papers for examples
3. Ask on JOSS Gitter: https://gitter.im/openjournals/joss

Good luck with your submission! 🎉
