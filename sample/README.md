# Sample Data for Testing

This directory contains sample CSV files that can be used to test the Clockify-ADO Report Generator without requiring actual API access.

## Files

### clockify_sample.csv
Sample time entries that simulate Clockify data export. Contains:
- 10 sample time entries
- Various work item ID patterns (#12345, ADO-67890, WI:11111, etc.)
- Different users, projects, and tags
- Mix of billable and non-billable time

### ado_work_items_sample.csv
Sample work items that simulate Azure DevOps data. Contains:
- 10 sample work items
- Different work item types (User Story, Bug, Task)
- Various states (New, Active, In Progress, Resolved, Closed)
- Story points and tags
- Matches most IDs from the Clockify sample data

## Usage

These files can be used for:
1. **Testing the matching logic** - Most work item IDs in Clockify entries have corresponding work items
2. **Testing report generation** - Verify Excel and HTML output formats
3. **Development** - Test changes without hitting real APIs
4. **Demo purposes** - Show the system capabilities without real data

## Testing with Sample Data

```python
import polars as pl
from src.domain.entities import TimeEntry, WorkItem

# Load sample data
clockify_df = pl.read_csv("sample/clockify_sample.csv")
ado_df = pl.read_csv("sample/ado_work_items_sample.csv")

# Process and generate reports
# ... your code here
```

## Data Privacy

These files contain only fictional data and do not represent any real person, project, or organization.