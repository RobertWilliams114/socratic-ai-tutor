
import logging
from typing import Any

from socratic.graph.storage import GraphStorage
from socratic.models import KnowledgeGraph
from socratic.query.engine import QueryEngine
from socratic.utils.llm_client import llm_client

logger = logging.getLogger(__name__)


class TutoringEngine(QueryEngine):
    """Enhanced query engine with prerequisite understanding checks.

    This is where the magic happens! This engine ensures students understand
    prerequisites before explaining complex concepts. It's like a good TA who
    checks "do you know X?" before teaching Y.

    Key innovation: We track what the student understands throughout the session
    and only teach new concepts when they're ready.
    """

    def __init__(self, knowledge_graph: KnowledgeGraph):
        """Initialize tutoring engine.

        Args:
            knowledge_graph: Knowledge graph to query
        """
        super().__init__(knowledge_graph)
        # This set tracks which concepts the student has demonstrated understanding of
        # It persists throughout the session so we don't keep asking the same questions
        self.understood_concepts = set()

    def check_prerequisite_understanding(
        self, concept_id: str, user_response: str = None
    ) -> dict[str, Any]:
        """Check if student understands prerequisites for a concept.

        This is the main prerequisite checking logic. When a student asks about
        a concept, we:
        1. Look up what prerequisites are needed (from the knowledge graph)
        2. Check which ones they haven't demonstrated understanding of yet
        3. Generate questions to verify their understanding

        Args:
            concept_id: The concept the student wants to learn about
            user_response: Optional - student's response to a prerequisite check

        Returns:
            Dictionary with:
            - ready: bool (are they ready to learn this?)
            - missing_prerequisites: list of concept titles they need first
            - questions: list of check questions to ask them
        """
        # Get prerequisite chain from the knowledge graph
        # This uses graph traversal to find all prerequisites (not just direct ones)
        prereq_chain = self.storage.get_prerequisite_chain(concept_id)

        # Filter out prerequisites the student has already demonstrated understanding of
        # No need to re-check concepts they already know!
        missing_prereqs = [
            p for p in prereq_chain if p not in self.understood_concepts
        ]

        # If they know all prerequisites, they're ready!
        if not missing_prereqs:
            return {
                "ready": True,
                "missing_prerequisites": [],
                "questions": [],
            }

        # Get full concept objects for the missing prerequisites
        prereq_concepts = []
        for prereq_id in missing_prereqs:
            if prereq_id in self.kg.concepts:
                prereq_concepts.append(self.kg.concepts[prereq_id])

        # Sort by difficulty - we want to teach easier concepts first
        # Makes sense pedagogically to start with foundations
        prereq_concepts.sort(key=lambda c: c.difficulty)

        # Generate understanding check questions for each missing prerequisite
        # We limit to 3 questions max to avoid overwhelming the student
        questions = []
        for prereq in prereq_concepts[:3]:  # Check up to 3 prerequisites
            question = self._generate_understanding_check(prereq)
            questions.append({
                "concept_id": prereq.id,
                "concept_title": prereq.title,
                "question": question,
            })

        return {
            "ready": False,
            "missing_prerequisites": [p.title for p in prereq_concepts],
            "questions": questions,
        }

    def _generate_understanding_check(self, concept: Any) -> str:
        """Generate a question to check understanding of a concept.

        Args:
            concept: Concept to check understanding of

        Returns:
            Understanding check question
        """
        system_prompt = """You are an AI tutor. Generate a brief question to check if a student understands a concept.
The question should be simple and direct, requiring a short answer.
Don't ask for definitions - ask for application or explanation."""

        prompt = f"""Generate a brief question to check if a student understands this concept:

Concept: {concept.title}
Definition: {concept.definitions[0] if concept.definitions else 'N/A'}
Difficulty: {concept.difficulty}/5

Return ONLY the question text, nothing else."""

        try:
            question = llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=100,
            )
            return question.strip()
        except Exception as e:
            logger.error(f"Error generating check question: {e}")
            return f"Can you explain what {concept.title} means to you?"

    def evaluate_understanding(
        self, concept_id: str, user_response: str
    ) -> dict[str, Any]:
        """Evaluate if student's response shows understanding.

        Args:
            concept_id: Concept being checked
            user_response: Student's response

        Returns:
            Evaluation result with feedback
        """
        if concept_id not in self.kg.concepts:
            return {"understood": False, "feedback": "Concept not found."}

        concept = self.kg.concepts[concept_id]

        # IMPORTANT: We use the LLM to evaluate student responses
        # This is stricter than it was initially - we fixed it to require concrete understanding
        # not just vague awareness. Students need to show they actually GET the concept.
        system_prompt = """You are an AI tutor evaluating student understanding.
Be rigorous in your evaluation - students must demonstrate CONCRETE understanding, not just vague awareness.

Criteria for "understood = true":
- Student can explain the concept in their own words with specific details
- Student can give examples or describe how it works
- Student shows they understand WHY or HOW, not just WHAT

Criteria for "understood = false":
- Vague statements like "it's about X" or "computers do Y"
- No specific examples or mechanisms
- Just repeating buzzwords without explanation
- Uncertain language ("I think...", "maybe...", "something about...")

Be encouraging but HONEST. Return JSON with: understood (boolean) and feedback (string)."""

        prompt = f"""Concept: {concept.title}
Definition: {concept.definitions[0] if concept.definitions else 'N/A'}

Student's response: {user_response}

Does the student demonstrate CONCRETE understanding with specific details?
Return JSON: {{"understood": true/false, "feedback": "brief encouraging feedback"}}

Examples:
- "It's about computers learning" → understood: false (too vague)
- "Systems learn patterns from data to make predictions" → understood: true (specific mechanism)"""

        try:
            response = llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=200,
            )

            import json
            result = json.loads(response)

            # Track understanding
            if result.get("understood", False):
                self.understood_concepts.add(concept_id)
                logger.info(f"Student demonstrated understanding of: {concept.title}")

            return result

        except Exception as e:
            logger.error(f"Error evaluating understanding: {e}")
            return {
                "understood": False,
                "feedback": "I couldn't evaluate your response. Could you try explaining again?"
            }

    def answer_with_prerequisite_checks(
        self, query: str, skip_checks: bool = False
    ) -> dict[str, Any]:
        """Answer query with prerequisite understanding checks.

        Args:
            query: User question
            skip_checks: Skip prerequisite checks (for testing)

        Returns:
            Answer with prerequisite check results
        """
        logger.info(f"Processing query with prerequisite checks: {query}")

        # Step 1: Identify relevant concepts
        concept_ids = self.identify_relevant_concepts(query)

        if not concept_ids:
            return {
                "answer": "I couldn't identify any relevant concepts for your question. "
                "Could you rephrase or provide more context?",
                "requires_prerequisite_check": False,
            }

        # Step 2: Check prerequisites for main concepts
        if not skip_checks:
            for concept_id in concept_ids:
                prereq_check = self.check_prerequisite_understanding(concept_id)

                if not prereq_check["ready"]:
                    # Student needs to understand prerequisites first
                    return {
                        "answer": self._format_prerequisite_message(
                            concept_id, prereq_check
                        ),
                        "requires_prerequisite_check": True,
                        "target_concept": self.kg.concepts[concept_id].title,
                        "missing_prerequisites": prereq_check["missing_prerequisites"],
                        "check_questions": prereq_check["questions"],
                        "concepts_used": concept_ids,
                    }

        # Step 3: All prerequisites understood - generate full answer
        context = self.retrieve_context(concept_ids)
        result = self.generate_scaffolded_answer(query, context)

        # Mark concepts as understood after successful explanation
        for concept_id in concept_ids:
            self.understood_concepts.add(concept_id)

        result["requires_prerequisite_check"] = False
        return result

    def _format_prerequisite_message(
        self, concept_id: str, prereq_check: dict
    ) -> str:
        """Format message about missing prerequisites.

        Args:
            concept_id: Target concept ID
            prereq_check: Prerequisite check results

        Returns:
            Formatted message
        """
        concept = self.kg.concepts[concept_id]
        prereqs = prereq_check["missing_prerequisites"]

        message = f"""Before we dive into **{concept.title}**, I want to make sure you understand the foundational concepts first.

To fully grasp {concept.title}, you should understand:
"""
        for i, prereq in enumerate(prereqs, 1):
            message += f"\n{i}. {prereq}"

        message += "\n\nLet's start with the first concept. "

        if prereq_check["questions"]:
            first_question = prereq_check["questions"][0]
            message += f"\n\n**Quick check**: {first_question['question']}"
            message += "\n\n(Answer this, and we'll build up to your original question!)"

        return message

    def mark_concept_understood(self, concept_id: str):
        """Manually mark a concept as understood.

        Args:
            concept_id: Concept ID to mark as understood
        """
        self.understood_concepts.add(concept_id)
        logger.info(f"Marked as understood: {concept_id}")

    def reset_understanding(self):
        """Reset all understanding tracking (new student session)."""
        self.understood_concepts.clear()
        logger.info("Reset student understanding tracking")

    def get_learning_path(self, target_concept_id: str) -> list[dict]:
        """Get the learning path to reach a target concept.

        Args:
            target_concept_id: Target concept to learn

        Returns:
            Ordered list of concepts to learn
        """
        if target_concept_id not in self.kg.concepts:
            return []

        # Get prerequisite chain
        prereq_chain = self.storage.get_prerequisite_chain(target_concept_id)

        # Build learning path
        path = []
        for prereq_id in prereq_chain:
            if prereq_id in self.kg.concepts:
                concept = self.kg.concepts[prereq_id]
                path.append({
                    "concept_id": prereq_id,
                    "title": concept.title,
                    "difficulty": concept.difficulty,
                    "understood": prereq_id in self.understood_concepts,
                })

        # Add target concept
        target = self.kg.concepts[target_concept_id]
        path.append({
            "concept_id": target_concept_id,
            "title": target.title,
            "difficulty": target.difficulty,
            "understood": target_concept_id in self.understood_concepts,
        })

        return path
