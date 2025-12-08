#!/usr/bin/env python3
"""Quick start script for Erica AI Tutor."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

console = Console()


def check_ollama():
    """Check if Ollama is running."""
    import requests

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


def main():
    """Run quick start setup."""
    console.print(
        Panel.fit(
            "[bold cyan]Erica AI Tutor - Quick Start[/bold cyan]\n"
            "This script will help you set up your environment.",
            border_style="cyan",
        )
    )

    # Check Ollama
    console.print("\n[bold]Step 1:[/bold] Checking Ollama...")
    if check_ollama():
        console.print("  ✅ Ollama is running")
    else:
        console.print("  ❌ Ollama is not running")
        console.print("\n[yellow]Please install and start Ollama:[/yellow]")
        console.print("  1. Download from https://ollama.ai")
        console.print("  2. Run: ollama pull qwen2.5:latest")
        console.print("  3. Run: ollama pull nomic-embed-text")
        console.print("\nThen run this script again.")
        return

    # Check .env
    console.print("\n[bold]Step 2:[/bold] Checking configuration...")
    env_file = Path(".env")
    if env_file.exists():
        console.print("  ✅ .env file exists")
    else:
        console.print("  ⚠️  .env file not found")
        if Confirm.ask("  Create .env file from template?"):
            import shutil

            shutil.copy(".env.example", ".env")
            console.print("  ✅ Created .env file")

    # Test LLM connection
    console.print("\n[bold]Step 3:[/bold] Testing LLM connection...")
    try:
        from erica.utils.llm_client import llm_client

        response = llm_client.generate(
            "Say 'Hello!' in one word.", temperature=0.1, max_tokens=10
        )
        console.print(f"  ✅ LLM responded: {response.strip()}")
    except Exception as e:
        console.print(f"  ❌ Error: {e}")
        return

    # Check for data
    console.print("\n[bold]Step 4:[/bold] Checking for data...")
    data_dir = Path("data")
    kg_file = data_dir / "hybrid_graph" / "erica_metadata.json"

    if kg_file.exists():
        console.print(f"  ✅ Hybrid knowledge graph found: {kg_file}")

        if Confirm.ask("\n[cyan]Start chat interface?[/cyan]"):
            console.print("\n[green]Starting Erica...[/green]\n")
            from erica.main import main as run_chat

            run_chat()
    else:
        console.print("  ⚠️  No hybrid knowledge graph found")
        console.print("\n[yellow]Next steps:[/yellow]")
        console.print("  1. Run notebooks/01_data_ingestion.ipynb")
        console.print("  2. Run notebooks/02_nano_graphrag_integration.ipynb")
        console.print("  3. Run this script again to start chatting!")

        if Confirm.ask("\n[cyan]Open data ingestion notebook?[/cyan]"):
            import subprocess

            subprocess.run(
                ["jupyter", "notebook", "notebooks/01_data_ingestion.ipynb"]
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[cyan]Goodbye![/cyan]")
