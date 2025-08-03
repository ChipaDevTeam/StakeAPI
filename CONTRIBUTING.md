# Contributing to StakeAPI

Thank you for your interest in contributing to StakeAPI! This document provides guidelines for contributing to the project.

## Code of Conduct

Please be respectful and professional in all interactions. We want to maintain a welcoming environment for all contributors.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/StakeAPI.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
5. Install dependencies: `pip install -e ".[dev]"`
6. Install pre-commit hooks: `pre-commit install`

## Development Workflow

1. Create a new branch for your feature: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests: `pytest`
4. Run linting: `black . && isort . && flake8`
5. Commit your changes with a descriptive message
6. Push to your fork and create a pull request

## Code Style

- We use Black for code formatting
- We use isort for import sorting
- We use flake8 for linting
- Follow PEP 8 guidelines
- Add type hints to all functions
- Write docstrings for all public methods

## Testing

- Write tests for all new features
- Ensure all tests pass before submitting a PR
- Aim for high test coverage
- Use pytest for testing

## Pull Request Process

1. Ensure your code follows the style guidelines
2. Add tests for new functionality
3. Update documentation if needed
4. Ensure all tests pass
5. Create a clear PR description explaining your changes

## Reporting Issues

When reporting issues, please include:
- A clear description of the problem
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment details (Python version, OS, etc.)

## Feature Requests

Feature requests are welcome! Please:
- Check if the feature already exists or is planned
- Provide a clear description of the feature
- Explain the use case and benefits
- Be open to discussion about implementation

Thank you for contributing!
