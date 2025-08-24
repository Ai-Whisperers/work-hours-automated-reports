"""Main CLI application using Typer."""

import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
import logging
from enum import Enum

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler

from ...infrastructure.config import get_settings, Settings
from ...infrastructure.api_clients import ClockifyClient, AzureDevOpsClient
from ...domain.value_objects import DateRange
from ...domain.services import MatchingService
from ...application.use_cases import GenerateReportUseCase
from ...application.use_cases.generate_report_use_case import (
    GenerateReportRequest,
    ReportFormat
)

# Set up rich console for better output
console = Console()

# Create Typer app
app = typer.Typer(
    name="clockify-ado",
    help="Clockify-ADO Automated Report Generator",
    add_completion=True,
    rich_markup_mode="rich"
)

# Configure logging with Rich
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)


class OutputFormat(str, Enum):
    """Output format options."""
    excel = "excel"
    html = "html"
    json = "json"
    pdf = "pdf"


def setup_logging(verbose: bool = False, quiet: bool = False):
    """Set up logging based on verbosity."""
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)


@app.command()
def run(
    start_date: Optional[str] = typer.Option(
        None,
        "--start",
        "-s",
        help="Start date (YYYY-MM-DD). Default: 7 days ago"
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--end",
        "-e",
        help="End date (YYYY-MM-DD). Default: today"
    ),
    output: Path = typer.Option(
        Path("report.xlsx"),
        "--output",
        "-o",
        help="Output file path"
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.excel,
        "--format",
        "-f",
        help="Output format"
    ),
    users: Optional[List[str]] = typer.Option(
        None,
        "--user",
        "-u",
        help="Filter by user ID (can be specified multiple times)"
    ),
    projects: Optional[List[str]] = typer.Option(
        None,
        "--project",
        "-p",
        help="Filter by project ID (can be specified multiple times)"
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Disable caching"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output"
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Quiet mode (errors only)"
    )
):
    """Generate a time tracking report.
    
    This command fetches time entries from Clockify, matches them to Azure DevOps
    work items, and generates a comprehensive report.
    """
    setup_logging(verbose, quiet)
    
    # Parse dates
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start = datetime.now() - timedelta(days=7)
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end = datetime.now()
    
    # Create date range
    date_range = DateRange(start, end)
    
    console.print(f"\n[bold cyan]Generating report for:[/bold cyan] {date_range.format_for_display()}\n")
    
    # Run async report generation
    asyncio.run(generate_report_async(
        date_range=date_range,
        output_path=output,
        format=ReportFormat(format.value),
        user_ids=users,
        project_ids=projects,
        use_cache=not no_cache
    ))


async def generate_report_async(
    date_range: DateRange,
    output_path: Path,
    format: ReportFormat,
    user_ids: Optional[List[str]] = None,
    project_ids: Optional[List[str]] = None,
    use_cache: bool = True
):
    """Async report generation logic."""
    settings = get_settings()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Initialize clients
        task = progress.add_task("Initializing API clients...", total=None)
        
        clockify_client = ClockifyClient(settings)
        ado_client = AzureDevOpsClient(settings)
        
        # Test connections
        progress.update(task, description="Testing connections...")
        
        clockify_ok = await clockify_client.test_connection()
        ado_ok = await ado_client.test_connection()
        
        if not clockify_ok:
            console.print("[bold red]Failed to connect to Clockify API[/bold red]")
            raise typer.Exit(1)
        
        if not ado_ok:
            console.print("[bold red]Failed to connect to Azure DevOps API[/bold red]")
            raise typer.Exit(1)
        
        progress.update(task, description="Connections verified ✓")
        
        # Import repository implementations
        from ...infrastructure.repositories import (
            ClockifyTimeEntryRepository,
            AzureDevOpsWorkItemRepository
        )
        
        # Create repositories
        time_entry_repo = ClockifyTimeEntryRepository(clockify_client)
        work_item_repo = AzureDevOpsWorkItemRepository(ado_client)
        
        # Create services
        matching_service = MatchingService()
        
        # Import report generator
        from ...infrastructure.adapters import ExcelReportGenerator
        report_generator = ExcelReportGenerator()
        
        # Create cache service if enabled
        cache_service = None
        if use_cache and settings.enable_caching:
            from ...infrastructure.adapters import LocalCacheService
            cache_service = LocalCacheService(settings.cache_directory)
        
        # Create use case
        use_case = GenerateReportUseCase(
            time_entry_repo=time_entry_repo,
            work_item_repo=work_item_repo,
            matching_service=matching_service,
            report_generator=report_generator,
            cache_service=cache_service
        )
        
        # Create request
        request = GenerateReportRequest(
            date_range=date_range,
            format=format,
            output_path=output_path,
            user_ids=user_ids,
            project_ids=project_ids,
            include_unmatched=True,
            group_by=["user", "work_item"]
        )
        
        # Execute use case
        progress.update(task, description="Generating report...")
        
        try:
            response = await use_case.execute(request)
            
            if response.success:
                # Display results
                console.print("\n[bold green]✓ Report generated successfully![/bold green]\n")
                
                # Create summary table
                table = Table(title="Report Summary")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Output File", str(response.report_path))
                table.add_row("Total Entries", str(response.total_entries))
                table.add_row("Matched Entries", f"{response.matched_entries} ({response.matched_entries/response.total_entries*100:.1f}%)")
                table.add_row("Unmatched Entries", str(response.unmatched_entries))
                table.add_row("Total Hours", f"{response.total_hours:.1f}")
                
                console.print(table)
                
                # Display warnings if any
                if response.warnings:
                    console.print("\n[yellow]⚠ Warnings:[/yellow]")
                    for warning in response.warnings:
                        console.print(f"  • {warning}")
                
            else:
                console.print("\n[bold red]✗ Report generation failed![/bold red]\n")
                
                if response.errors:
                    console.print("[red]Errors:[/red]")
                    for error in response.errors:
                        console.print(f"  • {error}")
                
                raise typer.Exit(1)
                
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}")
            raise typer.Exit(1)
        
        finally:
            # Clean up
            await clockify_client.close()
            await ado_client.close()


@app.command()
def validate():
    """Validate configuration and API connections."""
    console.print("[bold cyan]Validating configuration...[/bold cyan]\n")
    
    try:
        settings = get_settings()
        
        # Check required settings
        required = [
            ("Clockify API Key", bool(settings.clockify_api_key)),
            ("Clockify Workspace ID", bool(settings.clockify_workspace_id)),
            ("Azure DevOps Org", bool(settings.ado_organization)),
            ("Azure DevOps Project", bool(settings.ado_project)),
            ("Azure DevOps PAT", bool(settings.ado_pat))
        ]
        
        table = Table(title="Configuration Status")
        table.add_column("Setting", style="cyan")
        table.add_column("Status", style="green")
        
        all_valid = True
        for name, is_set in required:
            status = "✓ Set" if is_set else "✗ Missing"
            style = "green" if is_set else "red"
            table.add_row(name, f"[{style}]{status}[/{style}]")
            all_valid = all_valid and is_set
        
        console.print(table)
        
        if not all_valid:
            console.print("\n[bold red]Configuration incomplete. Please check your .env file.[/bold red]")
            raise typer.Exit(1)
        
        # Test connections
        console.print("\n[bold cyan]Testing API connections...[/bold cyan]\n")
        
        async def test_connections():
            clockify = ClockifyClient(settings)
            ado = AzureDevOpsClient(settings)
            
            try:
                clockify_ok = await clockify.test_connection()
                ado_ok = await ado.test_connection()
                
                return clockify_ok, ado_ok
            finally:
                await clockify.close()
                await ado.close()
        
        clockify_ok, ado_ok = asyncio.run(test_connections())
        
        connection_table = Table(title="Connection Status")
        connection_table.add_column("Service", style="cyan")
        connection_table.add_column("Status", style="green")
        
        connection_table.add_row(
            "Clockify API",
            f"[{'green' if clockify_ok else 'red'}]{'✓ Connected' if clockify_ok else '✗ Failed'}[/]"
        )
        connection_table.add_row(
            "Azure DevOps API",
            f"[{'green' if ado_ok else 'red'}]{'✓ Connected' if ado_ok else '✗ Failed'}[/]"
        )
        
        console.print(connection_table)
        
        if clockify_ok and ado_ok:
            console.print("\n[bold green]✓ All validations passed![/bold green]")
        else:
            console.print("\n[bold red]✗ Some validations failed. Please check your configuration.[/bold red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"\n[bold red]Validation error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def cache(
    action: str = typer.Argument(
        ...,
        help="Action to perform: clear, stats"
    )
):
    """Manage cache."""
    settings = get_settings()
    
    if action == "clear":
        console.print("[cyan]Clearing cache...[/cyan]")
        
        from ...infrastructure.adapters import LocalCacheService
        cache_service = LocalCacheService(settings.cache_directory)
        
        async def clear_cache():
            return await cache_service.clear()
        
        success = asyncio.run(clear_cache())
        
        if success:
            console.print("[green]✓ Cache cleared successfully![/green]")
        else:
            console.print("[red]✗ Failed to clear cache[/red]")
            
    elif action == "stats":
        console.print("[cyan]Cache statistics:[/cyan]\n")
        
        cache_dir = settings.cache_directory
        if cache_dir.exists():
            files = list(cache_dir.glob("*.cache"))
            total_size = sum(f.stat().st_size for f in files)
            
            table = Table(title="Cache Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Cache Directory", str(cache_dir))
            table.add_row("Number of Files", str(len(files)))
            table.add_row("Total Size", f"{total_size / 1024:.1f} KB")
            
            console.print(table)
        else:
            console.print("[yellow]Cache directory does not exist[/yellow]")
    
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Available actions: clear, stats")
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    from ... import __version__
    
    console.print(f"[bold cyan]Clockify-ADO Report Generator[/bold cyan]")
    console.print(f"Version: [green]{__version__}[/green]")
    
    settings = get_settings()
    console.print(f"Environment: [yellow]{settings.environment.value}[/yellow]")
    console.print(f"Debug Mode: [yellow]{settings.debug}[/yellow]")


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()