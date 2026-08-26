"""Hybrid query engine using nano-graphrag + custom graph."""

import logging
from typing import Any

from socratic.graph.hybrid_builder import HybridKnowledgeGraphBuilder
from socratic.graph.storage import GraphStorage
from socratic.query.engine import QueryEngine

logger = logging.getLogger(__name__)


class HybridQueryEngine:
    """Query engine that combines nano-graphrag retrieval with custom graph operations.

    This provides:
    1. nano-graphrag for powerful document retrieval
    2. Custom graph for concept relationships and scaffolding
    3. Best retrieval + best answer generation
    """

    def __init__(self, hybrid_builder: HybridKnowledgeGraphBuilder):
        """Initialize hybrid query engine.

        Args:
            hybrid_builder: Hybrid knowledge graph builder
        """
        self.hybrid_builder = hybrid_builder
        self.nano_rag = hybrid_builder.nano_rag

        # Also initialize custom query engine for concept-based queries
        kg = hybrid_builder.get_custom_graph()
        self.custom_engine = QueryEngine(kg)
        self.storage = GraphStorage(kg)

    def answer_query(
        self,
        query: str,
        use_nano_graphrag: bool = True,
        mode: str = "local"
    ) -> dict[str, Any]:
        """Answer a query using hybrid approach.

        Args:
            query: User question
            use_nano_graphrag: Whether to use nano-graphrag retrieval
            mode: Query mode for nano-graphrag (local/global/naive)

        Returns:
            Answer with context and metadata
        """
        logger.info(f"Processing hybrid query: {query}")

        if use_nano_graphrag:
            # Strategy 1: Use nano-graphrag for direct retrieval
            result = self._nano_graphrag_query(query, mode)
        else:
            # Strategy 2: Use custom concept-based query
            result = self.custom_engine.answer_query(query)

        return result

    def _nano_graphrag_query(self, query: str, mode: str) -> dict[str, Any]:
        """Query using nano-graphrag.

        Args:
            query: User question
            mode: Query mode

        Returns:
            Query result
        """
        # Get answer from nano-graphrag
        nano_result = self.nano_rag.query(query, mode=mode)

        # Also identify relevant concepts from custom graph
        concept_ids = self.custom_engine.identify_relevant_concepts(query)

        # Get additional context from custom graph
        context = self.custom_engine.retrieve_context(concept_ids) if concept_ids else {}

        return {
            "answer": nano_result["answer"],
            "concepts_used": concept_ids,
            "citations": self._extract_citations_from_context(context),
            "mode": mode,
            "source": "nano-graphrag",
        }

    def _extract_citations_from_context(self, context: dict) -> list[dict]:
        """Extract citations from context.

        Args:
            context: Retrieved context

        Returns:
            List of citations
        """
        citations = []
        for resource in context.get("resources", [])[:5]:
            citations.append({
                "title": resource.get("title", "Unknown"),
                "url": resource.get("url", ""),
                "type": resource.get("type", ""),
            })
        return citations

    def answer_with_scaffolding(self, query: str) -> dict[str, Any]:
        """Answer query with scaffolded learning approach.

        This uses the custom concept graph to build progressive explanations.

        Args:
            query: User question

        Returns:
            Scaffolded answer
        """
        logger.info(f"Generating scaffolded answer for: {query}")

        # Use custom engine for scaffolding
        return self.custom_engine.answer_query(query)

    def compare_approaches(self, query: str) -> dict[str, Any]:
        """Compare nano-graphrag vs custom graph approaches.

        Useful for evaluation and understanding trade-offs.

        Args:
            query: User question

        Returns:
            Results from both approaches
        """
        logger.info(f"Comparing query approaches for: {query}")

        # Get answers from both approaches
        nano_local = self._nano_graphrag_query(query, mode="local")
        nano_global = self._nano_graphrag_query(query, mode="global")
        custom = self.custom_engine.answer_query(query)

        return {
            "query": query,
            "nano_graphrag_local": nano_local,
            "nano_graphrag_global": nano_global,
            "custom_scaffolded": custom,
        }
