---
layout: default
title: Installation
parent: Getting Started
nav_order: 1
---

# Installation
{: .fs-9 }

Install StakeAPI and all its dependencies in seconds.
{: .fs-6 .fw-300 }

---

## Quick Install

The easiest way to install StakeAPI is with pip:

```bash
pip install stakeapi
```

This installs StakeAPI and all required dependencies:

| Dependency | Purpose |
|:-----------|:--------|
| `aiohttp` ≥ 3.8.0 | Async HTTP client for API requests |
| `pydantic` ≥ 2.0.0 | Data validation and type-safe models |
| `python-dotenv` ≥ 0.19.0 | Environment variable management |
| `websockets` ≥ 10.0 | Real-time WebSocket connections |
| `cryptography` ≥ 3.4.8 | Secure token handling |

## Install from Source

If you want the latest development version:

```bash
git clone https://github.com/yourusername/StakeAPI.git
cd StakeAPI
pip install -e .
```

## Install with Development Dependencies

For contributors and developers who want to run tests and linting:

```bash
pip install -e ".[dev]"
```

This adds:

| Tool | Purpose |
|:-----|:--------|
| `pytest` | Test framework |
| `pytest-asyncio` | Async test support |
| `pytest-cov` | Code coverage |
| `black` | Code formatting |
| `isort` | Import sorting |
| `flake8` | Linting |
| `mypy` | Type checking |
| `pre-commit` | Git hooks |

## Install with Documentation Dependencies

```bash
pip install -e ".[docs]"
```

## Virtual Environment Setup (Recommended)

We recommend using a virtual environment to avoid dependency conflicts:

### Using venv (Built-in)

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install StakeAPI
pip install stakeapi
```

### Using conda

```bash
conda create -n stakeapi python=3.11
conda activate stakeapi
pip install stakeapi
```

### Using Poetry

```bash
poetry add stakeapi
```

## Verify Installation

After installation, verify everything works:

```python
import stakeapi
print(f"StakeAPI version: {stakeapi.__version__}")
```

You should see output like:

```
StakeAPI version: 0.1.0
```

## System Requirements

| Requirement | Minimum |
|:------------|:--------|
| Python | 3.8+ |
| OS | Windows, macOS, Linux |
| Memory | 64 MB |
| Network | Internet connection required |

{% include affiliate-cta.html %}

## Next Steps

Now that StakeAPI is installed, you need a Stake.com account and access token:

- [Sign up on Stake.com](https://stake.com/?c=WY7953wQ) if you don't have an account
- [Authentication Guide]({% link getting-started/authentication.md %}) — Learn how to get your access token
- [Quick Start]({% link getting-started/quickstart.md %}) — Make your first API call

{% include affiliate-banner.html %}
