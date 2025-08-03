.PHONY: help install install-dev test lint format type-check clean build docs

help:
	@echo "Available commands:"
	@echo "  install     Install the package"
	@echo "  install-dev Install in development mode with dev dependencies"
	@echo "  test        Run tests"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code with black and isort"
	@echo "  type-check  Run type checking with mypy"
	@echo "  clean       Clean build artifacts"
	@echo "  build       Build the package"
	@echo "  docs        Build documentation"

install:
	pip install .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest --cov=stakeapi --cov-report=term-missing --cov-report=html

lint:
	flake8 stakeapi tests examples
	black --check stakeapi tests examples
	isort --check-only stakeapi tests examples

format:
	black stakeapi tests examples
	isort stakeapi tests examples

type-check:
	mypy stakeapi

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

docs:
	@echo "Documentation is in docs/ directory"
	@echo "Open docs/README.md for the main documentation"

# Development workflow shortcuts
dev-setup: install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify everything works"

check: lint type-check test
	@echo "All checks passed!"

release-check: clean check build
	@echo "Release checks complete!"
	@echo "Package is ready for release"
