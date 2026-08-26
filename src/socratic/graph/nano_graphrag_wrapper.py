"""Wrapper for nano-graphrag integration."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from nano_graphrag import GraphRAG, QueryParam
from nano_graphrag._utils import wrap_embedding_func_with_attrs

from socratic.config import settings
from socratic.models import KnowledgeGraph, Resource

logger = logging.getLogger(__name__)


class NanoGraphRAGWrapper:
    """Wrapper around nano-graphrag for Socratic AI Tutor.

    This integrates nano-graphrag as the core GraphRAG engine while maintaining
    compatibility with our custom knowledge graph models.
    """

    def __init__(self, working_dir: Path | None = None):
        """Initialize nano-graphrag wrapper.

        Args:
            working_dir: Directory for nano-graphrag storage
        """
        self.working_dir = working_dir or settings.graph_storage_path
        self.working_dir.mkdir(parents=True, exist_ok=True)

        # Initialize nano-graphrag with Ollama backend
        self.graph_rag = self._initialize_graphrag()

    def _initialize_graphrag(self) -> GraphRAG:
        """Initialize GraphRAG with Ollama configuration."""
        from openai import AsyncOpenAI

        # Create async OpenAI client for Ollama
        async_client = AsyncOpenAI(
            base_url=settings.get_llm_base_url(),
            api_key="not-needed"
        )

        # Custom LLM function for nano-graphrag
        async def ollama_model_func(
            prompt, system_prompt=None, history_messages=[], **kwargs
        ) -> str:
            messages = []
            if system_prompt:
                # Force English responses by prepending language instruction
                english_system_prompt = "You must respond in English only. " + system_prompt
                messages.append({"role": "system", "content": english_system_prompt})
            else:
                # Add default English instruction if no system prompt
                messages.append({"role": "system", "content": "You must respond in English only."})

            messages.extend(history_messages)
            messages.append({"role": "user", "content": prompt})

            # Filter out nano-graphrag specific kwargs that OpenAI doesn't accept
            openai_kwargs = {k: v for k, v in kwargs.items()
                           if k not in ['hashing_kv', 'model_name']}

            response = await async_client.chat.completions.create(
                model=settings.model_name,
                messages=messages,
                **openai_kwargs
            )
            return response.choices[0].message.content

        # Custom embedding function for nano-graphrag
        async def ollama_embedding_func(texts: list[str]) -> list[list[float]]:
            embeddings = []
            for text in texts:
                response = await async_client.embeddings.create(
                    model=settings.embedding_model,
                    input=text
                )
                embeddings.append(response.data[0].embedding)
            return embeddings

        # Manually set attributes instead of using wrap function
        ollama_embedding_func.embedding_dim = 768  # nomic-embed-text dimension
        ollama_embedding_func.max_token_size = 8192

        embedding_func = ollama_embedding_func

        # Initialize GraphRAG with Ollama
        return GraphRAG(
            working_dir=str(self.working_dir),
            best_model_func=ollama_model_func,
            cheap_model_func=ollama_model_func,
            embedding_func=embedding_func,
        )

    async def insert_resources_async(self, resources: list[Resource]) -> None:
        """Insert resources into nano-graphrag (async version).

        Args:
            resources: List of resources to insert
        """
        logger.info(f"Inserting {len(resources)} resources into nano-graphrag...")

        # Prepare documents for insertion
        for resource in resources:
            # Format resource for insertion
            document = self._format_resource_for_insertion(resource)

            # Insert into nano-graphrag
            await self.graph_rag.ainsert(document)
            logger.info(f"Inserted: {resource.title}")

    def insert_resources(self, resources: list[Resource]) -> None:
        """Insert resources into nano-graphrag (sync wrapper).

        Args:
            resources: List of resources to insert
        """
        # Try to get running loop (for Jupyter notebooks)
        try:
            loop = asyncio.get_running_loop()
            # If we're in a Jupyter notebook, create a task
            import nest_asyncio
            nest_asyncio.apply()
            loop.run_until_complete(self.insert_resources_async(resources))
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            asyncio.run(self.insert_resources_async(resources))

    def _format_resource_for_insertion(self, resource: Resource) -> str:
        """Format a resource for nano-graphrag insertion.

        Args:
            resource: Resource to format

        Returns:
            Formatted document string
        """
        # Create structured document with metadata
        doc = f"""Title: {resource.title}
Type: {resource.type.value}
URL: {resource.url}
{f"Span: {resource.span}" if resource.span else ""}

Content:
{resource.content}
"""
        return doc

    def query(
        self,
        question: str,
        mode: str = "local",
        only_context: bool = False
    ) -> dict[str, Any]:
        """Query the knowledge graph.

        Args:
            question: User question
            mode: Query mode ("local", "global", or "naive")
            only_context: Return only context without generating answer

        Returns:
            Query result with answer and context
        """
        logger.info(f"Querying nano-graphrag: {question}")

        param = QueryParam(
            mode=mode,
            only_need_context=only_context
        )

        # Query (synchronous wrapper with Jupyter support)
        try:
            loop = asyncio.get_running_loop()
            # If we're in a Jupyter notebook, use nest_asyncio
            import nest_asyncio
            nest_asyncio.apply()
            result = loop.run_until_complete(self.graph_rag.aquery(question, param=param))
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            result = asyncio.run(self.graph_rag.aquery(question, param=param))

        return {
            "answer": result if isinstance(result, str) else result.get("answer", ""),
            "context": result if only_context else None,
        }

    def save_custom_metadata(self, kg: KnowledgeGraph) -> None:
        """Save custom knowledge graph metadata alongside nano-graphrag.

        Args:
            kg: Knowledge graph with custom concepts, examples, etc.
        """
        metadata_path = self.working_dir / "socratic_metadata.json"

        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write(kg.model_dump_json(indent=2))

        logger.info(f"Saved custom metadata to {metadata_path}")

    def load_custom_metadata(self) -> KnowledgeGraph | None:
        """Load custom knowledge graph metadata.

        Returns:
            Knowledge graph if metadata exists, None otherwise
        """
        metadata_path = self.working_dir / "socratic_metadata.json"

        if not metadata_path.exists():
            return None

        with open(metadata_path, "r", encoding="utf-8") as f:
            return KnowledgeGraph.model_validate_json(f.read())

    def get_graph_stats(self) -> dict[str, Any]:
        """Get statistics about the knowledge graph.

        Returns:
            Dictionary with graph statistics
        """
        # Access nano-graphrag internals
        stats = {
            "working_dir": str(self.working_dir),
            "has_graph": (self.working_dir / "graph_chunk_entity_relation.graphml").exists(),
            "has_embeddings": (self.working_dir / "kv_store_full_docs.json").exists(),
        }

        return stats
