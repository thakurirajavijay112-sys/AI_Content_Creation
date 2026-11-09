"""
AI-CONTENT-AUTOMATION — Main Entry Point
==========================================
Provides CLI commands to launch the dashboard, scheduler,
and run individual engines.

Usage:
    python main.py dashboard          # Launch Streamlit dashboard
    python main.py scheduler          # Start the daily scheduler
    python main.py status             # Show system status
    python main.py init               # Initialise database and config
    python main.py check              # Check all dependencies
"""

import sys
import subprocess
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()
PROJECT_ROOT = Path(__file__).parent


# ── CLI ───────────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """AI-CONTENT-AUTOMATION — Automated Video Production System"""
    pass


@cli.command()
def init():
    """Initialise the database and verify configuration."""
    console.print(Panel.fit(
        "[bold cyan]AI-CONTENT-AUTOMATION[/bold cyan]\nInitialising system...",
        border_style="cyan"
    ))

    # Import here to catch config errors early
    try:
        from config import config
        from database.db_manager import db

        # Initialise database
        console.print("  [bold]Creating database schema...[/bold]")
        db.initialise_schema()
        console.print("  [green]✓[/green] Database ready")

        # Check config
        warnings = config.validate()
        if warnings:
            console.print("\n  [yellow]Configuration warnings:[/yellow]")
            for w in warnings:
                console.print(f"    [yellow]⚠[/yellow]  {w}")
        else:
            console.print("  [green]✓[/green] Configuration valid")

        # Health check
        health = db.health_check()
        console.print(f"  [green]✓[/green] Database health: {health['status']}")

        console.print("\n[green]✓ Initialisation complete![/green]")
        console.print(f"  Dashboard:  python main.py dashboard")
        console.print(f"  Scheduler:  python main.py scheduler")
        console.print(f"  Status:     python main.py status")

    except Exception as e:
        console.print(f"\n[red]✗ Initialisation failed: {e}[/red]")
        sys.exit(1)


@cli.command()
def check():
    """Check all system dependencies and report their status."""
    console.print(Panel.fit(
        "[bold]System Dependency Check[/bold]",
        border_style="blue"
    ))

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Dependency", width=25)
    table.add_column("Status", width=12)
    table.add_column("Details", width=45)

    # Python
    import sys
    table.add_row(
        "Python",
        "[green]✓ OK[/green]",
        f"{sys.version.split()[0]} at {sys.executable}"
    )

    # FFmpeg
    import shutil
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
            )
            version_line = result.stdout.split("\n")[0] if result.stdout else "unknown"
            table.add_row("FFmpeg", "[green]✓ OK[/green]", version_line[:50])
        except Exception:
            table.add_row("FFmpeg", "[yellow]⚠ Found[/yellow]", f"at {ffmpeg}")
    else:
        table.add_row(
            "FFmpeg",
            "[red]✗ MISSING[/red]",
            "Install from: gyan.dev/ffmpeg/builds"
        )

    # Gemini API
    from config import config
    if config.ai.gemini.is_configured:
        table.add_row("Gemini API", "[green]✓ Configured[/green]", f"Model: {config.ai.gemini.default_model}")
    else:
        table.add_row("Gemini API", "[yellow]⚠ Not set[/yellow]", "Set GEMINI_API_KEY in .env")

    # Ollama
    try:
        import httpx
        resp = httpx.get(f"{config.ai.ollama.base_url}/api/tags", timeout=3)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            model_names = [m["name"] for m in models[:3]]
            table.add_row("Ollama", "[green]✓ Running[/green]", f"Models: {', '.join(model_names) or 'none pulled'}")
        else:
            table.add_row("Ollama", "[yellow]⚠ Running[/yellow]", "Connected but returned error")
    except Exception:
        table.add_row("Ollama", "[dim]○ Offline[/dim]", "Start with: ollama serve")

    # edge-tts
    try:
        import edge_tts
        table.add_row("edge-tts", "[green]✓ Installed[/green]", "Free Microsoft TTS")
    except ImportError:
        table.add_row("edge-tts", "[yellow]○ Missing[/yellow]", "pip install edge-tts")

    # pyttsx3 (offline TTS)
    try:
        import pyttsx3
        table.add_row("pyttsx3", "[green]✓ Installed[/green]", "Offline TTS fallback")
    except ImportError:
        table.add_row("pyttsx3", "[yellow]○ Missing[/yellow]", "pip install pyttsx3")

    # Whisper
    try:
        import whisper
        table.add_row("Whisper", "[green]✓ Installed[/green]", "Local transcription")
    except ImportError:
        table.add_row("Whisper", "[yellow]○ Missing[/yellow]", "pip install openai-whisper")

    # NVIDIA GPU
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            gpu_info = result.stdout.strip().split("\n")[0]
            table.add_row("NVIDIA GPU", "[green]✓ Available[/green]", gpu_info)
        else:
            table.add_row("NVIDIA GPU", "[yellow]? Unknown[/yellow]", "nvidia-smi returned no data")
    except Exception:
        table.add_row("NVIDIA GPU", "[dim]○ N/A[/dim]", "No NVIDIA GPU or driver found")

    # Database
    try:
        from database.db_manager import db
        health = db.health_check()
        size = health.get("size_mb", 0)
        table.add_row("Database", f"[green]✓ {health['status']}[/green]", f"SQLite — {size} MB")
    except Exception as e:
        table.add_row("Database", "[red]✗ Error[/red]", str(e)[:45])

    # Streamlit
    try:
        import streamlit
        table.add_row("Streamlit", "[green]✓ Installed[/green]", f"v{streamlit.__version__}")
    except ImportError:
        table.add_row("Streamlit", "[yellow]○ Missing[/yellow]", "pip install streamlit")

    console.print(table)


@cli.command()
def dashboard():
    """Launch the Streamlit dashboard."""
    dashboard_path = PROJECT_ROOT / "dashboard" / "app.py"
    if not dashboard_path.exists():
        console.print("[red]Dashboard not found. Run Phase 2 setup first.[/red]")
        sys.exit(1)

    console.print(Panel.fit(
        "[bold cyan]Launching Dashboard[/bold cyan]\n"
        f"Opening at: http://localhost:{_get_dashboard_port()}",
        border_style="cyan"
    ))

    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(dashboard_path),
        "--server.port", str(_get_dashboard_port()),
        "--server.headless", "false",
        "--browser.gatherUsageStats", "false",
    ])


@cli.command()
def scheduler():
    """Start the daily video production scheduler."""
    console.print(Panel.fit(
        "[bold cyan]Starting Scheduler[/bold cyan]\n"
        "[yellow]⚠  Scheduler requires this computer to stay ON and awake.[/yellow]\n"
        "Videos will be produced at scheduled times (Nepal time).",
        border_style="cyan"
    ))
    try:
        from scheduler.daily_scheduler import DailyScheduler
        s = DailyScheduler()
        s.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Scheduler stopped by user.[/yellow]")
    except ImportError:
        console.print("[yellow]Scheduler not yet implemented. Coming in Phase 9.[/yellow]")


@cli.command()
def status():
    """Show current system status and statistics."""
    try:
        from config import config
        from database.db_manager import db

        db.initialise_schema()
        health = db.health_check()

        console.print(Panel.fit(
            f"[bold cyan]{config.app.name}[/bold cyan]\n"
            f"Environment: {config.app.env} | Timezone: {config.app.timezone}",
            border_style="cyan"
        ))

        # Database stats
        table = Table(title="Database Statistics", box=box.SIMPLE)
        table.add_column("Table", style="cyan")
        table.add_column("Records", justify="right")

        for table_name, count in health.get("tables", {}).items():
            table.add_row(table_name, str(count))

        console.print(table)

        # Config summary
        summary = config.summary()
        config_table = Table(title="Configuration Summary", box=box.SIMPLE)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value")

        for key, value in summary.items():
            status_str = str(value)
            if isinstance(value, bool):
                status_str = "[green]Yes[/green]" if value else "[red]No[/red]"
            config_table.add_row(key.replace("_", " ").title(), status_str)

        console.print(config_table)

        # Warnings
        warnings = config.validate()
        if warnings:
            console.print("\n[yellow]Configuration Warnings:[/yellow]")
            for w in warnings:
                console.print(f"  [yellow]⚠[/yellow]  {w}")

    except Exception as e:
        console.print(f"[red]Status check failed: {e}[/red]")
        sys.exit(1)


def _get_dashboard_port() -> int:
    try:
        from config import config
        return config.dashboard.port
    except Exception:
        return 8501


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cli()
