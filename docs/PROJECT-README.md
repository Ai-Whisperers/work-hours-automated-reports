# clockify-ADO-automated-report

**Goal:** Automate the process of fetching, matching, and reporting work hours from **Clockify** (time entries) and **Azure DevOps** (Work Items).
The output is a clean, elegant report showing **who worked how many hours on which task** — with no manual downloads.

## Project Phases

1. **Core Script (current focus)**
   - Extract data from both sources (Clockify + ADO).
   - Match time entries to Work Items (via Work Item IDs in descriptions).
   - Generate consolidated reports (Excel + HTML).
   - No UI at first, just automation.

2. **User Interface (future phase)**
   - Web app with minimal and elegant UI/UX.
   - Possible stacks:
     - **FastAPI** backend + **Next.js/Tailwind** frontend, or
     - Lightweight alternatives like **Streamlit** / **Reflex**.
   - The UI will consume the same reporting logic, keeping things modular.

## Tech Stack (Phase 1)

- **Python 3.10+** — scripting and ETL core.
- **httpx** — API calls (async, robust).
- **pydantic-settings** — config via `.env`.
- **polars** — fast and clean DataFrame operations.
- **typer** — command-line interface.
- **openpyxl** — Excel export.
- **jinja2** — HTML report templates.

Future (Phase 2+):
- **FastAPI** for API/web backend.
- **Next.js/Tailwind** or **Streamlit/Reflex** for UI.

## Architecture

- `app/clients/clockify.py` → API client for Clockify.
- `app/clients/azure.py` → API client for Azure DevOps Work Items.
- `app/matcher.py` → Work Item ID extraction logic (`#12345`, `ADO-12345`, `(12345)`, `WI:12345`, plain numbers).
- `app/report.py` → Aggregation and report generation (Excel + HTML).
- `app/main.py` → CLI tool (Typer).
- `sample/` → CSVs to run the prototype without API keys.

## Quickstart (Prototype with CSVs)

1. Install dependencies:
   ```bash
   uv venv && uv pip install -r requirements.txt
   ```

2. Run with sample data:
   ```bash
   python -m app.main run --clockify-csv sample/clockify.csv --ado-csv sample/ado.csv --out report.xlsx
   python -m app.main run --clockify-csv sample/clockify.csv --ado-csv sample/ado.csv --html report.html
   ```

3. Outputs:
   - `report.xlsx` with three tabs:
     - **ByPerson** (hours grouped by user & Work Item)
     - **ByWorkItem** (hours grouped by task)
     - **RawMerged** (raw merged dataset)
   - `report.html` — minimal dark-themed report.

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

## Roadmap

- [ ] Full API calls (Clockify pagination + ADO batch Work Item fetch).
- [ ] Local caching (SQLite) for faster re-runs.
- [ ] Validation (pydantic models) and automated tests.
- [ ] Scheduling (cron / GitHub Actions) for daily/weekly reports.
- [ ] Extended metrics (per sprint/iteration, per epic).
- [ ] Full UI with FastAPI + frontend framework.

## Why This Approach?

- **Phase 1:** Guarantee a robust, automated pipeline with clean outputs.
- **Phase 2+:** Add UI once automation is reliable.
- **Benefit:** Reduces manual overhead immediately, while keeping future scalability and elegance in mind.
