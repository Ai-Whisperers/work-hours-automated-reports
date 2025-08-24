# Clockify-ADO Automated Report Generator

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Hexagonal-green)](https://en.wikipedia.org/wiki/Hexagonal_architecture_(software))
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black)](https://github.com/psf/black)

A modern, clean-architecture implementation for automated time tracking and work item reporting between Clockify and Azure DevOps.

## 🌟 Features

- **Automated Data Extraction**: Fetches time entries from Clockify and work items from Azure DevOps
- **Intelligent Matching**: Multiple pattern recognition strategies to link time entries with work items
- **Multiple Report Formats**: Excel, HTML, JSON, and PDF reports
- **Clean Architecture**: Hexagonal architecture with SOLID principles
- **Performance Optimized**: Async operations, connection pooling, and caching
- **Docker Support**: Easy deployment with Docker and docker-compose
- **CLI Interface**: Rich command-line interface with progress indicators

## 🏗️ Architecture

This project follows **Hexagonal Architecture** (Ports & Adapters) with clear separation of concerns:

```
src/
├── domain/           # Core business logic (entities, value objects, services)
├── application/      # Use cases and application services
├── infrastructure/   # External adapters (API clients, repositories)
└── presentation/     # User interfaces (CLI, API)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Clockify API key
- Azure DevOps Personal Access Token (PAT)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Ai-Whisperers/clockify-ADO-automated-report.git
cd clockify-ADO-automated-report
```

2. **Set up environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

3. **Configure credentials**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# Required variables:
# - CLOCKIFY_API_KEY
# - CLOCKIFY_WORKSPACE_ID
# - ADO_ORG
# - ADO_PROJECT
# - ADO_PAT
```

4. **Validate configuration**
```bash
python main.py validate
```

5. **Generate your first report**
```bash
# Last 7 days
python main.py run

# Custom date range
python main.py run --start 2024-01-01 --end 2024-01-31

# Excel format (default)
python main.py run --output report.xlsx

# HTML format
python main.py run --format html --output report.html
```

## 🐳 Docker Deployment

### Using Docker

```bash
# Build image
docker build -t clockify-ado-report .

# Run container
docker run --env-file .env clockify-ado-report run
```

### Using Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### With Redis caching
```bash
docker-compose --profile with-redis up -d
```

## 📖 Usage

### CLI Commands

#### Generate Report
```bash
python main.py run [OPTIONS]

Options:
  --start, -s TEXT      Start date (YYYY-MM-DD)
  --end, -e TEXT        End date (YYYY-MM-DD)
  --output, -o PATH     Output file path
  --format, -f TEXT     Output format (excel/html/json/pdf)
  --user, -u TEXT       Filter by user ID
  --project, -p TEXT    Filter by project ID
  --no-cache           Disable caching
  --verbose, -v        Verbose output
  --quiet, -q          Quiet mode
```

#### Validate Configuration
```bash
python main.py validate
```

#### Manage Cache
```bash
# Clear cache
python main.py cache clear

# View cache statistics
python main.py cache stats
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CLOCKIFY_API_KEY` | Your Clockify API key | ✅ |
| `CLOCKIFY_WORKSPACE_ID` | Clockify workspace ID | ✅ |
| `ADO_ORG` | Azure DevOps organization | ✅ |
| `ADO_PROJECT` | Azure DevOps project | ✅ |
| `ADO_PAT` | Azure DevOps Personal Access Token | ✅ |
| `CACHE_BACKEND` | Cache backend (local/redis) | ❌ |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | ❌ |
| `OUTPUT_FORMAT` | Default output format | ❌ |

### Work Item ID Patterns

The system recognizes multiple patterns in time entry descriptions:

- `#12345` - Hash format
- `ADO-12345` - ADO prefix format
- `WI:12345` - Work Item prefix
- `[12345]` - Bracket format
- `(12345)` - Parenthesis format
- `12345` - Plain numbers (with validation)

## 📊 Report Formats

### Excel Report
- **Summary Sheet**: Overview statistics
- **ByPerson Sheet**: Hours grouped by user and work item
- **ByWorkItem Sheet**: Hours grouped by work item
- **RawData Sheet**: All entries with full details

### HTML Report
- Dark-themed responsive design
- Summary statistics cards
- Top work items table
- Top contributors table

## 🏛️ Architecture Details

### Domain Layer
- **Entities**: TimeEntry, WorkItem, User
- **Value Objects**: WorkItemId, Duration, DateRange
- **Services**: MatchingService, AggregationService

### Application Layer
- **Use Cases**: GenerateReportUseCase, SyncTimeEntriesUseCase
- **Ports**: ReportGenerator, CacheService, NotificationService

### Infrastructure Layer
- **API Clients**: ClockifyClient, AzureDevOpsClient
- **Repositories**: Implementation of domain repositories
- **Adapters**: Cache, Report generators

### Clean Code Principles
- **SOLID Principles** throughout
- **Dependency Inversion**: Ports and adapters pattern
- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Extensible without modification

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_matching_service.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Convention
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code style
- `refactor:` Code refactoring
- `test:` Testing
- `chore:` Maintenance

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with modern Python best practices
- Inspired by clean architecture principles
- Uses hexagonal architecture for maintainability

## 📞 Support

For issues or questions:
1. Check the [documentation](docs/index.md)
2. Review [troubleshooting guide](docs/operations/troubleshooting.md)
3. Create an [issue](https://github.com/Ai-Whisperers/clockify-ADO-automated-report/issues)

---

**Built with ❤️ using Clean Architecture and SOLID Principles**