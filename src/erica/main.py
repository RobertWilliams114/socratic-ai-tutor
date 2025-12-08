## This is how use actually use Erica
## You just need to run `python -m erica.main`

import argparse
import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

from erica.chat import TutoringInterface
from erica.config import settings
from erica.graph import HybridKnowledgeGraphBuilder

console = Console()

## Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)

## This function runs the erica chat interface
def main():
    parser = argparse.ArgumentParser(description="Erica AI Tutor - Interactive Learning")
    parser.add_argument(
        "--working-dir",
        type=Path,
        default=Path("data/hybrid_graph"),
        help="Path to hybrid knowledge graph working directory",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild knowledge graph from scratch",
    )
    parser.add_argument(
        "--no-prerequisite-checks",
        action="store_true",
        help="Disable prerequisite understanding checks (simple mode)",
    )
    args = parser.parse_args()

    try:
        ## Load hybrid knowledge graph
        console.print(f"[cyan]Loading hybrid knowledge graph from {args.working_dir}...[/cyan]")
        builder = HybridKnowledgeGraphBuilder(working_dir=args.working_dir)

        ## Check if graph exists
        metadata_path = args.working_dir / "erica_metadata.json"
        if args.rebuild or not metadata_path.exists():
            console.print(
                "[yellow]Knowledge graph not found or rebuild requested.[/yellow]"
            )
            console.print(
                "[yellow]Please run the data ingestion notebooks first:[/yellow]"
            )
            console.print(
                "[yellow]  1. notebooks/01_data_ingestion.ipynb[/yellow]"
            )
            console.print(
                "[yellow]  2. notebooks/02_nano_graphrag_integration.ipynb[/yellow]"
            )
            return

        kg = builder.load()
        console.print(
            f"[green]Loaded knowledge graph with {len(kg.concepts)} concepts, "
            f"{len(kg.resources)} resources, {len(kg.examples)} examples[/green]\n"
        )

        ## Choose interface mode
        if args.no_prerequisite_checks:
            from erica.chat import ChatInterface
            console.print("[yellow]Running in simple mode (no prerequisite checks)[/yellow]\n")
            chat = ChatInterface(kg)
        else:
            console.print("[green]Running in tutoring mode (with prerequisite checks)[/green]\n")
            chat = TutoringInterface(kg)

        ## Start chat interface
        chat.run()

        ## Optionally save conversation
        save = console.input("\n[cyan]Save conversation? (y/n):[/cyan] ").lower()
        if save == "y":
            output_path = Path("conversation.json")
            chat.save_conversation(str(output_path))

    except KeyboardInterrupt:
        console.print("\n[cyan]Goodbye![/cyan]")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
