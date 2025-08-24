# Development Setup Guide

## Overview

This guide will help you set up a complete development environment for the Clockify-ADO Automated Report project. Follow these steps to get your local environment ready for development.

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: 3.10 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 2GB free space
- **Internet**: Required for API access

### Recommended Tools
- **IDE**: Visual Studio Code or PyCharm
- **Terminal**: Windows Terminal, iTerm2, or native terminal
- **Git Client**: Git CLI or GitHub Desktop
- **API Testing**: Postman or Insomnia
- **Database Browser**: SQLite Browser (for cache inspection)

## Step 1: Install Prerequisites

### Python Installation

#### Windows
```powershell
# Using Windows Package Manager
winget install Python.Python.3.10

# Or download from python.org
# https://www.python.org/downloads/
```

#### macOS
```bash
# Using Homebrew
brew install python@3.10

# Or using pyenv
pyenv install 3.10.12
pyenv global 3.10.12
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev
```

### Git Installation
```bash
# Windows
winget install Git.Git

# macOS
brew install git

# Linux
sudo apt install git
```

### Verify Installations
```bash
python --version  # Should show Python 3.10.x
git --version     # Should show git version
pip --version     # Should show pip version
```

## Step 2: Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/clockify-ado-automated-report.git
cd clockify-ado-automated-report

# Or if starting from scratch
mkdir clockify-ado-automated-report
cd clockify-ado-automated-report
git init
```

## Step 3: Set Up Python Environment

### Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (Command Prompt)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate

# Your prompt should now show (venv)
```

### Upgrade pip
```bash
python -m pip install --upgrade pip
```

## Step 4: Install Dependencies

### Create requirements.txt
```txt
# Core dependencies
httpx==0.25.0
pydantic==2.4.2
pydantic-settings==2.0.3
polars==0.19.3
typer[all]==0.9.0
python-dotenv==1.0.0
tenacity==8.2.3

# Report generation
openpyxl==3.1.2
jinja2==3.1.2
markdown==3.4.4
plotly==5.17.0

# Development tools
pytest==7.4.2
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.11.1
black==23.9.1
ruff==0.0.291
mypy==1.5.1
pre-commit==3.4.0

# Documentation
mkdocs==1.5.3
mkdocs-material==9.4.2

# Optional
redis==5.0.0
rich==13.5.3
```

### Install Dependencies
```bash
pip install -r requirements.txt

# For development dependencies only
pip install -r requirements-dev.txt
```

## Step 5: Configure Environment

### Create .env File
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# Windows
notepad .env

# macOS/Linux
nano .env
```

### Required Environment Variables
```bash
# Clockify Configuration
CLOCKIFY_API_KEY=your_api_key_here
CLOCKIFY_WORKSPACE_ID=your_workspace_id

# Azure DevOps Configuration
ADO_ORG=your_organization
ADO_PROJECT=your_project
ADO_PAT=your_personal_access_token

# Development Settings
ENV=development
LOG_LEVEL=DEBUG
CACHE_BACKEND=local
```

## Step 6: Set Up IDE

### Visual Studio Code

#### Install Extensions
```bash
# Install recommended extensions
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.black-formatter
code --install-extension charliermarsh.ruff
code --install-extension littlefoxteam.vscode-python-test-adapter
```

#### Create .vscode/settings.json
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true,
    ".coverage": true,
    "htmlcov": true
  }
}
```

#### Create .vscode/launch.json
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run CLI",
      "type": "python",
      "request": "launch",
      "module": "app.main",
      "args": ["run"],
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Debug Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v", "tests"],
      "console": "integratedTerminal"
    }
  ]
}
```

### PyCharm Setup

1. Open project in PyCharm
2. Configure Python Interpreter:
   - File → Settings → Project → Python Interpreter
   - Add Interpreter → Add Local Interpreter
   - Select Virtualenv Environment → Existing
   - Choose `venv/bin/python`

3. Configure Run Configurations:
   - Run → Edit Configurations
   - Add Python configuration
   - Module name: `app.main`
   - Parameters: `run`

## Step 7: Set Up Pre-commit Hooks

### Create .pre-commit-config.yaml
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-toml
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.291
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Install Pre-commit
```bash
pre-commit install
pre-commit run --all-files  # Test hooks
```

## Step 8: Initialize Project Structure

```bash
# Create project directories
mkdir -p app/{clients,core,models,reports,utils}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p docs/{api,architecture,deployment,user-guide}
mkdir -p templates logs .cache sample scripts

# Create __init__.py files
touch app/__init__.py
touch app/clients/__init__.py
touch app/core/__init__.py
touch app/models/__init__.py
touch app/reports/__init__.py
touch app/utils/__init__.py
touch tests/__init__.py
```

## Step 9: Database Setup (Optional)

### SQLite for Caching
```bash
# Install SQLite browser for debugging
# Windows
winget install SQLite.SQLiteBrowser

# macOS
brew install --cask db-browser-for-sqlite

# Linux
sudo apt install sqlitebrowser
```

### Redis for Distributed Caching
```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt install redis-server
sudo systemctl start redis

# Windows (using Docker)
docker run -d -p 6379:6379 redis:alpine
```

## Step 10: Verify Setup

### Run Test Script
Create `scripts/verify_setup.py`:
```python
#!/usr/bin/env python
"""Verify development environment setup."""

import sys
import importlib
from pathlib import Path

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print("✅ Python version OK:", sys.version)
        return True
    else:
        print("❌ Python 3.10+ required, found:", sys.version)
        return False

def check_dependencies():
    """Check required packages."""
    packages = [
        "httpx", "pydantic", "polars", "typer",
        "openpyxl", "jinja2", "pytest"
    ]
    
    missing = []
    for package in packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} missing")
            missing.append(package)
    
    return len(missing) == 0

def check_environment():
    """Check environment variables."""
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    required_vars = [
        "CLOCKIFY_API_KEY",
        "CLOCKIFY_WORKSPACE_ID",
        "ADO_ORG",
        "ADO_PROJECT",
        "ADO_PAT"
    ]
    
    missing = []
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var} configured")
        else:
            print(f"❌ {var} not set")
            missing.append(var)
    
    return len(missing) == 0

def check_directories():
    """Check project structure."""
    dirs = [
        "app", "tests", "docs", "templates",
        "logs", ".cache", "sample"
    ]
    
    for dir_name in dirs:
        path = Path(dir_name)
        if path.exists():
            print(f"✅ {dir_name}/ exists")
        else:
            print(f"❌ {dir_name}/ missing")
            path.mkdir(parents=True, exist_ok=True)
            print(f"  Created {dir_name}/")
    
    return True

def main():
    """Run all checks."""
    print("🔍 Verifying Development Setup\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment Variables", check_environment),
        ("Project Structure", check_directories)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 Checking {name}:")
        results.append(check_func())
    
    print("\n" + "="*50)
    if all(results):
        print("✅ Development environment ready!")
    else:
        print("❌ Some issues found. Please fix them before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

Run verification:
```bash
python scripts/verify_setup.py
```

## Step 11: Run Sample Tests

### Create Sample Test
```python
# tests/test_setup.py
def test_import():
    """Test basic imports work."""
    import app
    import httpx
    import polars
    assert True

def test_environment():
    """Test environment loading."""
    from app.config import settings
    assert settings is not None
```

### Run Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html
```

## Development Workflow

### Daily Development Cycle
```bash
# 1. Start your day
git pull origin main
source venv/bin/activate  # Activate virtual environment

# 2. Create feature branch
git checkout -b feature/your-feature

# 3. Make changes and test
# Edit files...
pytest tests/  # Run tests
black app/  # Format code
ruff check app/  # Lint code

# 4. Commit changes
git add .
git commit -m "feat: your feature description"

# 5. Push changes
git push origin feature/your-feature
```

### Running the Application
```bash
# Run CLI
python -m app.main run

# Run with custom dates
python -m app.main run --start-date 2024-01-01 --end-date 2024-01-31

# Run in debug mode
LOG_LEVEL=DEBUG python -m app.main run

# Run tests
pytest

# Run specific test
pytest tests/unit/test_matcher.py::test_extract_ids
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| ImportError: No module named 'app' | Add project root to PYTHONPATH |
| Permission denied on Windows | Run as administrator or check antivirus |
| SSL certificate errors | Update certificates or use `--trusted-host` |
| Virtual environment not activating | Check execution policy on Windows |
| Tests not discovered | Ensure `__init__.py` files exist |

### Windows-Specific Issues
```powershell
# Fix execution policy for scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Fix SSL issues
pip config set global.trusted-host "pypi.org files.pythonhosted.org"
```

### macOS-Specific Issues
```bash
# Fix SSL certificate issues
brew install ca-certificates

# Fix Python path issues
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## Additional Resources

### Documentation
- [Python 3.10 Documentation](https://docs.python.org/3.10/)
- [Polars Documentation](https://pola-rs.github.io/polars-book/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

### Learning Resources
- [Real Python Tutorials](https://realpython.com/)
- [Python Testing 101](https://realpython.com/python-testing/)
- [Async Python](https://realpython.com/async-io-python/)

### Community
- Project Issues: GitHub Issues page
- Python Discord: https://pythondiscord.com/
- Stack Overflow: Tag with `python`, `clockify`, `azure-devops`

## Next Steps

1. ✅ Complete environment setup
2. ✅ Verify all dependencies installed
3. ✅ Configure API credentials
4. 📝 Read project documentation
5. 🧪 Run test suite
6. 🚀 Start developing!

---

**Need help?** Check the troubleshooting section or create an issue in the repository.