"""Query engine for answering student questions."""

import json
import logging
from typing import Any

from erica.graph.storage import GraphStorage
from erica.models import KnowledgeGraph
from erica.utils.llm_client import llm_client

logger = logging.getLogger(__name__)


class QueryEngine:
    """Engine for processing queries and generating answers."""

    def __init__(self, knowledge_graph: KnowledgeGraph):
        """Initialize query engine.

        Args:
            knowledge_graph: Knowledge graph to query
        """
        self.kg = knowledge_graph
        self.storage = GraphStorage(knowledge_graph)

    def identify_relevant_concepts(self, query: str) -> list[str]:
        """Identify concepts relevant to the query.

        Args:
            query: User query

        Returns:
            List of relevant concept IDs
        """
        # If no concepts exist, return empty list
        if not self.kg.concepts:
            logger.warning("No concepts in knowledge graph, cannot identify relevant concepts")
            return []

        system_prompt = """You are an expert at understanding student questions and mapping them to course concepts.
You MUST respond with ONLY valid JSON - no other text before or after.

Your response must be a JSON array of concept IDs (strings):
["concept_id_1", "concept_id_2", "concept_id_3"]

If no concepts are relevant, return an empty array: []
IMPORTANT: Return ONLY the JSON array, nothing else."""

        concept_list = "\n".join(
            [
                f"- {cid}: {concept.title} (difficulty {concept.difficulty})"
                for cid, concept in self.kg.concepts.items()
            ]
        )

        prompt = f"""Student question: {query}

Available concepts:
{concept_list[:3000]}

Respond with ONLY a JSON array of the most relevant concept IDs (up to 5).
Example format:
["machine_learning", "neural_networks", "backpropagation"]

If none are relevant, return: []"""

        try:
            response = llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=500,
            )

            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            # Parse JSON
            concept_ids = json.loads(response)

            # Validate it's a list
            if not isinstance(concept_ids, list):
                logger.warning(f"LLM returned non-list JSON, wrapping in list")
                concept_ids = [concept_ids] if concept_ids else []

            # Filter to only valid concept IDs
            valid_ids = [cid for cid in concept_ids if cid in self.kg.concepts]

            logger.info(f"Identified {len(valid_ids)} relevant concepts for query")
            return valid_ids

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error identifying concepts: {e}")
            logger.debug(f"LLM response was: {response[:200]}")
            return []
        except Exception as e:
            logger.error(f"Error identifying concepts: {e}")
            return []

    def retrieve_context(self, concept_ids: list[str]) -> dict[str, Any]:
        """Retrieve context for concepts from the knowledge graph.

        Args:
            concept_ids: List of concept IDs

        Returns:
            Dictionary containing concepts, resources, examples, and prerequisites
        """
        context = {
            "concepts": [],
            "prerequisites": [],
            "resources": [],
            "examples": [],
        }

        for concept_id in concept_ids:
            # Get concept data
            if concept_id in self.kg.concepts:
                context["concepts"].append(self.kg.concepts[concept_id].model_dump())

                # Get prerequisites
                prereqs = self.storage.get_prerequisite_chain(concept_id)
                for prereq_id in prereqs:
                    if prereq_id in self.kg.concepts:
                        context["prerequisites"].append(
                            self.kg.concepts[prereq_id].model_dump()
                        )

                # Get resources
                resources = self.storage.get_resources_for_concept(concept_id)
                context["resources"].extend(resources)

                # Get examples
                examples = self.storage.get_examples_for_concept(concept_id)
                context["examples"].extend(examples)

        logger.info(
            f"Retrieved context: {len(context['concepts'])} concepts, "
            f"{len(context['prerequisites'])} prerequisites, "
            f"{len(context['resources'])} resources, "
            f"{len(context['examples'])} examples"
        )

        return context

    def generate_scaffolded_answer(
        self, query: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate a scaffolded answer that progresses from simple to complex.

        Args:
            query: User query
            context: Retrieved context

        Returns:
            Dictionary containing answer, concepts used, and resource citations
        """
        system_prompt = """You are Erica, an AI tutor for an Introduction to AI course.
Your role is to help students learn by:
1. Starting with prerequisite concepts if needed
2. Building up to the main concepts in order of difficulty
3. Providing clear explanations with examples
4. Citing specific resources for further reading

Use a scaffolded approach: explain simpler concepts first, then build to more complex ones.
Always cite your sources using the format [Resource: title, span]."""

        # Format context for prompt
        context_str = self._format_context(context)

        prompt = f"""Student Question: {query}

Available Context:
{context_str}

Generate a comprehensive, scaffolded answer that:
1. Addresses any necessary prerequisites first
2. Explains the main concepts in increasing difficulty
3. Includes examples where relevant
4. Cites specific resources

Format your response as JSON with fields: answer, concepts_used (array of IDs), citations (array of resource info)."""

        try:
            response = llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2000,
            )

            result = json.loads(response)
            logger.info("Generated scaffolded answer")
            return result

        except json.JSONDecodeError:
            # If LLM doesn't return valid JSON, wrap the text response
            logger.warning("LLM did not return valid JSON, wrapping text response")
            return {
                "answer": response,
                "concepts_used": [c["id"] for c in context["concepts"]],
                "citations": [
                    {"title": r["title"], "url": r["url"]} for r in context["resources"][:3]
                ],
            }
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return {
                "answer": "I encountered an error generating the answer. Please try again.",
                "concepts_used": [],
                "citations": [],
            }

    def _format_context(self, context: dict[str, Any]) -> str:
        """Format context for inclusion in prompt.

        Args:
            context: Context dictionary

        Returns:
            Formatted context string
        """
        parts = []

        # Prerequisites
        if context["prerequisites"]:
            parts.append("Prerequisites:")
            for concept in context["prerequisites"]:
                parts.append(f"  - {concept['title']}: {concept['definitions'][0]}")

        # Main concepts
        if context["concepts"]:
            parts.append("\nMain Concepts:")
            for concept in sorted(context["concepts"], key=lambda c: c["difficulty"]):
                parts.append(
                    f"  - {concept['title']} (difficulty {concept['difficulty']}): "
                    f"{concept['definitions'][0] if concept['definitions'] else 'N/A'}"
                )

        # Examples
        if context["examples"]:
            parts.append("\nExamples:")
            for example in context["examples"][:3]:  # Limit to top 3
                parts.append(f"  - {example['title']}: {example['content'][:200]}...")

        # Resources
        if context["resources"]:
            parts.append("\nResources:")
            for resource in context["resources"][:5]:  # Limit to top 5
                span = resource.get("span", "")
                parts.append(f"  - {resource['title']} ({span}): {resource['url']}")

        return "\n".join(parts)

    def answer_query(self, query: str) -> dict[str, Any]:
        """Answer a user query end-to-end.

        Args:
            query: User question

        Returns:
            Complete answer with context
        """
        logger.info(f"Processing query: {query}")

        # Step 1: Identify relevant concepts
        concept_ids = self.identify_relevant_concepts(query)

        if not concept_ids:
            return {
                "answer": "I couldn't identify any relevant concepts for your question. "
                "Could you rephrase or provide more context?",
                "concepts_used": [],
                "citations": [],
            }

        # Step 2: Retrieve context
        context = self.retrieve_context(concept_ids)

        # Step 3: Generate answer
        result = self.generate_scaffolded_answer(query, context)

        return result
