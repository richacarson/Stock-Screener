# CLAUDE.md

## Project Overview

Stock-Screener is a stock screening application that filters and analyzes stocks based on user-defined criteria.

## Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov
```

### Linting

```bash
# Format code
black .

# Lint
ruff check .
```

## Code Style

- Python 3.10+
- Follow PEP 8 conventions
- Use type hints for function signatures
- Keep functions focused and under 50 lines where practical

## Project Structure

```
Stock-Screener/
├── CLAUDE.md
├── requirements.txt
├── main.py
├── screener/       # Core screening logic
├── data/           # Data fetching and storage
└── tests/          # Test files
```

## Key Conventions

- Use descriptive variable names; avoid single-letter names outside loops
- Write docstrings for public functions and classes
- Keep commits atomic and messages descriptive
- Handle API rate limits and network errors gracefully
