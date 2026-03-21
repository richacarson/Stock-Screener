# Stock Screener — Claude Code Workflow

## Overview

This is IOWN's stock screening application. It screens stocks based on fundamental and technical criteria, generates an HTML report, and deploys to GitHub Pages at https://richacarson.github.io/Stock-Screener/.

## Quick Start

```bash
# Load environment
source .env && export GITHUB_PUSH_TOKEN

# Run the screener
python3 main.py

# Deploy to GitHub Pages
python3 scripts/deploy.py
```

## Workflow

1. **Screen**: Run `python3 main.py` — fetches data, applies screening filters, outputs results to `output/results.json`
2. **Report**: The screener auto-generates `output/index.html` from the results
3. **Deploy**: Run `python3 scripts/deploy.py` — commits output to the `gh-pages` branch and pushes

## Git Operations

- Always commit with clear, descriptive messages
- Push using: `git push -u origin <branch-name>`
- For deploying to GitHub Pages, use `scripts/deploy.py` which handles the `gh-pages` branch
- The `.env` file contains `GITHUB_PUSH_TOKEN` for authenticated pushes. Always `source .env && export GITHUB_PUSH_TOKEN` before pushing.

## Project Structure

```
Stock-Screener/
├── CLAUDE.md              # This file — workflow instructions
├── main.py                # Entry point — runs the screener
├── requirements.txt       # Python dependencies
├── .env                   # GITHUB_PUSH_TOKEN (not committed)
├── .env.example           # Template for .env
├── screener/
│   ├── __init__.py
│   ├── filters.py         # Screening criteria and filters
│   └── rankings.py        # Scoring and ranking logic
├── data/
│   ├── __init__.py
│   └── fetcher.py         # Data fetching from APIs
├── templates/
│   └── report.html        # Jinja2 HTML report template
├── output/                # Generated output (gitignored on main)
│   ├── results.json
│   └── index.html
├── scripts/
│   └── deploy.py          # GitHub Pages deployment script
└── .github/
    └── workflows/
        └── screen.yml     # GitHub Actions workflow
```

## Screening Criteria

Default filters (configurable in `screener/filters.py`):
- **Market cap**: Minimum $1B
- **Volume**: Minimum 500K average daily volume
- **P/E ratio**: Between 5 and 40
- **Revenue growth**: Positive YoY
- **Relative strength**: Above 50-day moving average

Filters can be customized by modifying `screener/filters.py` or passing criteria to `main.py`.

## Data Sources

The screener uses `yfinance` (Yahoo Finance) by default — free, no API key needed. To add other sources (Finnhub, Alpha Vantage), extend `data/fetcher.py`.

## Code Style

- Python 3.10+
- Follow PEP 8
- Use type hints for function signatures
- Keep functions focused and under 50 lines where practical
- Handle API rate limits and network errors gracefully

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black .

# Lint
ruff check .
```
