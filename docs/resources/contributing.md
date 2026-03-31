---
layout: default
title: Contributing
parent: Resources
nav_order: 5
---

# Contributing to StakeAPI
{: .fs-9 }

Help make StakeAPI even better — contributions of all kinds are welcome!
{: .fs-6 .fw-300 }

---

{% include affiliate-cta.html %}

## How to Contribute

### 1. Fork & Clone

```bash
git clone https://github.com/yourusername/StakeAPI.git
cd StakeAPI
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

Or use the setup script (Windows):

```powershell
.\setup_dev.ps1
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes

- Write clean, well-documented code
- Follow the existing code style (Black + isort)
- Add tests for new functionality
- Update documentation if needed

### 5. Run Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=stakeapi

# Run specific test file
pytest tests/test_client.py
```

### 6. Format & Lint

```bash
# Format code
black stakeapi/ tests/
isort stakeapi/ tests/

# Lint
flake8 stakeapi/ tests/

# Type check
mypy stakeapi/
```

### 7. Submit a Pull Request

Push your branch and open a pull request against the `main` branch.

## Contribution Guidelines

### Code Style

- **Formatter:** Black (line length: 88)
- **Import sorting:** isort (profile: black)
- **Linting:** flake8
- **Type hints:** Required for all public methods
- **Docstrings:** Google style

### Testing

- All new features must include tests
- Maintain or improve code coverage
- Use `pytest-asyncio` for async tests
- Mock external API calls

### Commit Messages

Follow conventional commits:

```
feat: add WebSocket support
fix: handle token expiration correctly
docs: update authentication guide
test: add tests for rate limiter
refactor: simplify GraphQL request handling
```

### What to Contribute

- **Bug fixes** — Find and fix bugs
- **New features** — Add API endpoint wrappers
- **Documentation** — Improve guides, add examples
- **Tests** — Increase test coverage
- **Performance** — Optimize request handling
- **Types** — Add or improve type annotations

## Project Structure

```
StakeAPI/
├── stakeapi/              # Main package
│   ├── __init__.py        # Package exports
│   ├── _version.py        # Version info
│   ├── auth.py            # Authentication
│   ├── client.py          # Main client
│   ├── endpoints.py       # API endpoints
│   ├── exceptions.py      # Custom exceptions
│   ├── models.py          # Pydantic models
│   └── utils.py           # Utility functions
├── tests/                 # Test suite
│   ├── conftest.py        # Test fixtures
│   ├── test_client.py     # Client tests
│   ├── test_models.py     # Model tests
│   └── test_utils.py      # Utility tests
├── docs/                  # Documentation (GitHub Pages)
├── examples/              # Example scripts
├── pyproject.toml         # Project configuration
└── Makefile               # Dev commands
```

## Code of Conduct

Be respectful and constructive. We're all here to build something great together.

{% include affiliate-banner.html %}

---

{: .note }
> Want to test your contributions? You'll need a [Stake.com account](https://stake.com/?c=WY7953wQ) for integration testing.
