## Socratic interface that checks for prerequisite understanding

import logging
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from socratic.models import KnowledgeGraph
from socratic.query.tutoring_engine import TutoringEngine

logger = logging.getLogger(__name__)
console = Console()

## Interactive interface that has prerequisite checks
class TutoringInterface:

    ## This function initializes the tutoring interface and uses the knowledge graph as its input
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.tutoring_engine = TutoringEngine(knowledge_graph)
        self.conversation_history = []
        self.pending_prerequisite_check = None

    ## This function displays the welcome message when you first enter the interface
    def display_welcome(self) -> None:
        welcome = """# Welcome to Socratic - Your AI Course Tutor

I'm here to help you truly understand AI concepts, not just memorize them!

**How I teach:**
- I'll check if you understand prerequisite concepts first
- I'll ask questions to gauge your understanding
- I'll build your knowledge step-by-step from simple to complex
- I'll provide examples and resources along the way

**You can ask me about:**
- Machine learning algorithms
- Neural networks and deep learning
- Computer vision
- Natural language processing
- And more!

**Commands:**
- `quit` or `exit` - End the session
- `reset` - Start fresh (reset my memory of what you know)
- `path <topic>` - Show the learning path for a topic

Let's start learning!
"""
        console.print(Panel(Markdown(welcome), border_style="blue"))

    ## This function displays the formatted answer and takes the query result from the tutoring engine as its input
    def display_answer(self, result: dict[str, Any]) -> None:

        ## Display answer
        console.print("\n[bold cyan]Socratic:[/bold cyan]")
        console.print(Markdown(result["answer"]))

        ## If this requires prerequisite checks, show the questions
        if result.get("requires_prerequisite_check"):
            self._handle_prerequisite_check(result)
            return

        ## Display concepts used
        if result.get("concepts_used"):
            console.print("\n[dim]✓ Concepts covered:[/dim]", end=" ")
            console.print("[dim]" + ", ".join(result["concepts_used"]) + "[/dim]")

        ## Display citations
        if result.get("citations"):
            console.print("\n[bold]📚 Resources:[/bold]")
            for i, citation in enumerate(result["citations"], 1):
                title = citation.get("title", "Unknown")
                url = citation.get("url", "")
                console.print(f"  {i}. {title}")
                if url:
                    console.print(f"     [dim]{url}[/dim]")

        console.print()
    
    ## This function checks all of the prerequisites before teaching the next topic. The parameter for this function is the result which contains the prerequisite check questions
    def _handle_prerequisite_check(self, result: dict[str, Any]) -> None:

        ## Store the pending check
        self.pending_prerequisite_check = result

        ## Display missing prerequisites
        console.print("\n[bold yellow]📋 Prerequisites needed:[/bold yellow]")
        for prereq in result["missing_prerequisites"]:
            console.print(f"  • {prereq}")

        console.print()

    ## This function evaluates the users response to hte prerequisite check. The only parameter is the users response to the question.
    def _evaluate_prerequisite_response(self, user_response: str) -> None:

        if not self.pending_prerequisite_check:
            return

        ## Get the current question being checked
        questions = self.pending_prerequisite_check.get("check_questions", [])
        if not questions:
            self.pending_prerequisite_check = None
            return

        current_question = questions[0]
        concept_id = current_question["concept_id"]

        ## Evaluate understanding
        with console.status("[bold yellow]Evaluating your understanding...[/bold yellow]"):
            evaluation = self.tutoring_engine.evaluate_understanding(
                concept_id, user_response
            )

        ## Display feedback
        console.print("\n[bold cyan]Socratic:[/bold cyan]")
        if evaluation["understood"]:
            console.print(f"[green]✓[/green] {evaluation['feedback']}")

            ## Remove this question from pending checks
            questions.pop(0)

            ## Check if there are more prerequisites to check
            if questions:
                console.print(f"\n[bold yellow]Next prerequisite check:[/bold yellow]")
                next_question = questions[0]
                console.print(f"\n**{next_question['concept_title']}**")
                console.print(f"{next_question['question']}\n")
            else:
                ## All prerequisites understood! Now answer the original question
                console.print("\n[green]Great! Now you're ready for the full explanation.[/green]\n")

                ## Get the original query from history
                if self.conversation_history:
                    original_query = self.conversation_history[-1]["query"]

                    with console.status("[bold yellow]Preparing your answer...[/bold yellow]"):
                        result = self.tutoring_engine.answer_with_prerequisite_checks(
                            original_query, skip_checks=True
                        )

                    self.display_answer(result)

                self.pending_prerequisite_check = None

        else:
            console.print(f"[yellow]⚠[/yellow] {evaluation['feedback']}")
            console.print(f"\n[dim]Let me explain {current_question['concept_title']}:[/dim]\n")

            ## Explain the prerequisite concept
            with console.status("[bold yellow]Preparing explanation...[/bold yellow]"):
                explanation = self.tutoring_engine.answer_query(
                    f"Explain {current_question['concept_title']} in simple terms"
                )

            console.print(Markdown(explanation["answer"]))

            ## Ask the question again
            console.print(f"\n[bold yellow]Let's try again:[/bold yellow]")
            console.print(f"{current_question['question']}\n")

    ## This function displays the learning path for a topic and takes the topic that it is showing the path for as the parameter.
    def display_learning_path(self, topic: str) -> None:

        ## Identify the concept
        with console.status("[bold yellow]Finding learning path...[/bold yellow]"):
            concept_ids = self.tutoring_engine.identify_relevant_concepts(topic)

        if not concept_ids:
            console.print(f"[red]I couldn't find a concept for '{topic}'[/red]\n")
            return

        ## Get learning path
        path = self.tutoring_engine.get_learning_path(concept_ids[0])

        if not path:
            console.print(f"[yellow]No learning path found for '{topic}'[/yellow]\n")
            return

        ## Display path
        console.print(f"\n[bold cyan]Learning Path for {path[-1]['title']}:[/bold cyan]\n")

        for i, step in enumerate(path, 1):
            status = "✓" if step["understood"] else "○"
            difficulty = "⭐" * step["difficulty"]
            console.print(
                f"  {status} {i}. {step['title']} {difficulty}"
            )

        console.print(
            f"\n[dim]You've mastered {sum(1 for s in path if s['understood'])}/{len(path)} concepts[/dim]\n"
        )

    ## This function runns the interactive tutoring chat loop
    def run(self) -> None:
        self.display_welcome()

        while True:
            try:
                ## Get user input
                query = console.input("[bold green]You:[/bold green] ").strip()

                if not query:
                    continue

                ## Handle commands
                if query.lower() in ["quit", "exit", "bye"]:
                    console.print("\n[cyan]Goodbye! Keep learning![/cyan]")
                    break

                if query.lower() == "reset":
                    self.tutoring_engine.reset_understanding()
                    self.pending_prerequisite_check = None
                    console.print(
                        "\n[green]✓ Memory reset! Let's start fresh.[/green]\n"
                    )
                    continue

                if query.lower().startswith("path "):
                    topic = query[5:].strip()
                    self.display_learning_path(topic)
                    continue

                ## Check if we're in the middle of prerequisite checks
                if self.pending_prerequisite_check:
                    self._evaluate_prerequisite_response(query)
                    continue

                ## Normal query processing
                with console.status("[bold yellow]Thinking...[/bold yellow]"):
                    result = self.tutoring_engine.answer_with_prerequisite_checks(query)

                ## Display result
                self.display_answer(result)

                ## Save to conversation history
                self.conversation_history.append({"query": query, "result": result})

            except KeyboardInterrupt:
                console.print("\n\n[cyan]Session interrupted. Goodbye![/cyan]")
                break
            except Exception as e:
                logger.error(f"Error in tutoring loop: {e}", exc_info=True)
                console.print(f"\n[red]Error: {e}[/red]\n")
                console.print("[dim]Try asking your question differently.[/dim]\n")

    ## This function saves the conversation history to a file and takes the path that the user would send it to as the parameter.
    def save_conversation(self, path: str) -> None:
        import json

        ## Include understanding state
        conversation_data = {
            "conversation": self.conversation_history,
            "understood_concepts": list(self.tutoring_engine.understood_concepts),
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(conversation_data, f, indent=2)

        console.print(f"[green]Conversation saved to {path}[/green]")
