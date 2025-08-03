# StakeAPI Development Setup Script for Windows
# Run this script in PowerShell to set up your development environment

Write-Host "Setting up StakeAPI development environment..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Yellow
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or later from https://python.org" -ForegroundColor Red
    exit 1
}

# Check Python version
$versionNumber = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$requiredVersion = 3.8
if ([decimal]$versionNumber -lt $requiredVersion) {
    Write-Host "Error: Python $versionNumber found, but Python $requiredVersion or later is required" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists, removing old one..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force venv
}

python -m venv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install the package in development mode
Write-Host "Installing StakeAPI in development mode..." -ForegroundColor Yellow
pip install -e ".[dev]"

# Install pre-commit hooks
Write-Host "Setting up pre-commit hooks..." -ForegroundColor Yellow
pre-commit install

# Create .env file from example if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please edit .env file and add your actual API credentials" -ForegroundColor Cyan
}

# Run initial tests to verify setup
Write-Host "Running initial tests to verify setup..." -ForegroundColor Yellow
pytest tests/ -v

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Development environment setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Edit .env file with your API credentials" -ForegroundColor White
    Write-Host "2. Run tests: pytest" -ForegroundColor White
    Write-Host "3. Run examples: python examples/basic_usage.py" -ForegroundColor White
    Write-Host "4. Start developing!" -ForegroundColor White
    Write-Host ""
    Write-Host "Useful commands:" -ForegroundColor Cyan
    Write-Host "- Run tests: pytest" -ForegroundColor White
    Write-Host "- Format code: black . && isort ." -ForegroundColor White
    Write-Host "- Lint code: flake8 stakeapi tests examples" -ForegroundColor White
    Write-Host "- Type check: mypy stakeapi" -ForegroundColor White
} else {
    Write-Host "❌ Setup completed but tests failed" -ForegroundColor Red
    Write-Host "Please check the error messages above" -ForegroundColor Red
}
