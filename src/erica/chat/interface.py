## The chat interface for Erica.

import logging
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from erica.models import KnowledgeGraph
from erica.query.engine import QueryEngine

logger = logging.getLogger(__name__)
console = Console()

## Interactive chat for erica
class ChatInterface:

    ## This function initializes the chat interface and uses the knowledge base as its only argument
    def __init__(self, knowledge_graph: KnowledgeGraph):

        self.query_engine = QueryEngine(knowledge_graph)
        self.conversation_history = []

    ## This function just shows the welcome display for the chat interface
    def display_welcome(self) -> None:
        """Display welcome message."""
        welcome = """# Welcome to Erica - Your AI Course Tutor

I'm here to help you learn about AI concepts. Ask me anything about:
- Machine learning algorithms
- Neural networks and deep learning
- Computer vision
- Natural language processing
- And more!

Type 'quit' or 'exit' to end the session.
"""
        console.print(Panel(Markdown(welcome), border_style="blue"))

    ## This function displays the query answer based on the users input and the only inlput is the query result
    def display_answer(self, result: dict[str, Any]) -> None:

        ## Display answer
        console.print("\n[bold cyan]Erica:[/bold cyan]")
        console.print(Markdown(result["answer"]))

        ## Display concepts used
        if result.get("concepts_used"):
            console.print("\n[dim]Concepts covered:[/dim]", end=" ")
            console.print("[dim]" + ", ".join(result["concepts_used"]) + "[/dim]")

        ## Display citations
        if result.get("citations"):
            console.print("\n[bold]Resources:[/bold]")
            for i, citation in enumerate(result["citations"], 1):
                title = citation.get("title", "Unknown")
                url = citation.get("url", "")
                console.print(f"  {i}. {title}")
                if url:
                    console.print(f"     {url}")

        console.print()

    ## Run the interactive chat loop
    def run(self) -> None:
        self.display_welcome()

        while True:
            try:
                ## Get user input
                query = console.input("[bold green]You:[/bold green] ").strip()

                if not query:
                    continue

                if query.lower() in ["quit", "exit", "bye"]:
                    console.print("\n[cyan]Goodbye! Happy learning![/cyan]")
                    break

                ## Process query
                with console.status("[bold yellow]Thinking...[/bold yellow]"):
                    result = self.query_engine.answer_query(query)

                ## Display result
                self.display_answer(result)

                ## Save to conversation history
                self.conversation_history.append({"query": query, "result": result})

            except KeyboardInterrupt:
                console.print("\n\n[cyan]Session interrupted. Goodbye![/cyan]")
                break
            except Exception as e:
                logger.error(f"Error in chat loop: {e}")
                console.print(f"\n[red]Error: {e}[/red]\n")

    ## This function saves the conversation history to a file and the argument is the path to the save conversation
    def save_conversation(self, path: str) -> None:
        import json

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.conversation_history, f, indent=2)

        console.print(f"[green]Conversation saved to {path}[/green]")
