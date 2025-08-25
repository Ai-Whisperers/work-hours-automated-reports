# clockify-ADO-automated-report

**Goal:** Automate the process of fetching, matching, and reporting work hours from **Clockify** (time entries) and **Azure DevOps** (Work Items).
The output is a clean, elegant report showing **who worked how many hours on which task** — with no manual downloads.

## Project Status

✅ **Phase 1 Complete** - Core automation with clean architecture implementation
🚧 **Phase 2 Planned** - Web UI with FastAPI backend

## Tech Stack (Implemented)

- **Python 3.11+** — Core language
- **httpx** — Async API calls with retry logic
- **pydantic v2** — Data validation and settings management
- **polars** — Fast DataFrame operations
- **typer** — Rich CLI interface
- **openpyxl** — Excel report generation
- **jinja2** — HTML report templates
- **rich** — Enhanced terminal output
- **tenacity** — Retry logic with exponential backoff

## Architecture (Hexagonal/Clean Architecture)

The project follows **Hexagonal Architecture** with clear separation of concerns:

```
src/
├── domain/                 # Core business logic
│   ├── entities/          # TimeEntry, WorkItem, User
│   ├── value_objects/     # WorkItemId, Duration, DateRange
│   ├── repositories/      # Repository interfaces (ports)
│   └── services/          # MatchingService, AggregationService
├── application/           # Use cases and application services
│   ├── use_cases/        # GenerateReportUseCase
│   ├── ports/            # External service interfaces
│   └── dto/              # Data transfer objects
├── infrastructure/        # External adapters
│   ├── api_clients/      # ClockifyClient, AzureDevOpsClient
│   ├── repositories/     # Repository implementations
│   ├── adapters/         # Cache, Report generators
│   └── config/           # Settings and configuration
└── presentation/          # User interfaces
    ├── cli/              # Typer CLI application
    └── api/              # FastAPI (future)
```

## Quickstart

1. Install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

3. Validate configuration:
   ```bash
   python main.py validate
   ```

4. Generate report:
   ```bash
   # Last 7 days (default)
   python main.py run
   
   # Custom date range
   python main.py run --start 2024-01-01 --end 2024-01-31
   
   # HTML format
   python main.py run --format html --output report.html
   ```

5. Output formats:
   - **Excel** (`report.xlsx`):
     - Summary sheet with statistics
     - ByPerson sheet (hours by user and work item)
     - ByWorkItem sheet (hours by work item)
     - RawData sheet (all entries)
   - **HTML** (`report.html`):
     - Dark-themed responsive design
     - Summary statistics
     - Top contributors and work items

## Environment Variables (for API mode)

Copy `.env.example` to `.env` and fill in:
- `CLOCKIFY_API_KEY`
- `CLOCKIFY_WORKSPACE_ID`
- `ADO_ORG`
- `ADO_PROJECT`
- `ADO_PAT` (personal access token)

## Matching Logic

- Extract **Work Item IDs** from Clockify descriptions.
- If multiple IDs exist in one entry, the script currently explodes rows (creates one row per ID).
- Planned enhancements:
  - Priority rules (choose first ID, or based on tags).
  - Fuzzy matching (map entries to WI titles if no ID is present).

## Output Formats

- **Excel report** (`report.xlsx`) for structured tabular analysis.
- **HTML report** (`report.html`) as a quick, elegant, human-readable summary.
- Future: JSON/CSV API endpoints for integration with other systems.

## Implementation Status

### ✅ Completed Features
- [x] Full API integration with pagination and batch fetching
- [x] Local and Redis caching support
- [x] Pydantic v2 models for validation
- [x] Rich CLI with Typer
- [x] Excel and HTML report generation
- [x] Docker and docker-compose support
- [x] Retry logic with exponential backoff
- [x] Hexagonal architecture implementation
- [x] Comprehensive error handling
- [x] Multiple work item ID pattern matching
- [x] Fuzzy matching for work items

### 🚧 In Progress
- [ ] Automated tests (unit, integration, e2e)
- [ ] GitHub Actions CI/CD pipeline
- [ ] Sample data for testing

### 📋 Future Enhancements
- [ ] FastAPI web backend
- [ ] React/Next.js frontend
- [ ] Scheduling with cron/GitHub Actions
- [ ] Extended metrics (sprint/epic level)
- [ ] PDF report generation
- [ ] Email notifications
- [ ] Multi-tenant support

## Why This Approach?

- **Phase 1:** Guarantee a robust, automated pipeline with clean outputs.
- **Phase 2+:** Add UI once automation is reliable.
- **Benefit:** Reduces manual overhead immediately, while keeping future scalability and elegance in mind.
