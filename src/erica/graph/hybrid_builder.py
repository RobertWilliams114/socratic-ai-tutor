## This is the implementation of the nanograph rag with alterations and additions

import logging
from pathlib import Path

from erica.config import settings
from erica.graph.builder import KnowledgeGraphBuilder
from erica.graph.nano_graphrag_wrapper import NanoGraphRAGWrapper
from erica.models import KnowledgeGraph, Resource

logger = logging.getLogger(__name__)

## Builds knowledge graph using both nano-graphrag and NetworkX graph.
class HybridKnowledgeGraphBuilder:

    ## This function initializes the hybrid builder and takes the working directory for graph storage.
    def __init__(self, working_dir: Path | None = None):
        self.working_dir = working_dir or settings.graph_storage_path

        ## Initialize nano-graphrag wrapper
        self.nano_rag = NanoGraphRAGWrapper(working_dir=self.working_dir)

        ## Initialize custom graph builder for concepts/examples/edges
        self.custom_builder = KnowledgeGraphBuilder()

    ## This function builds the hybrid knowledge graph from teh resources.
    ## It takes the list of resource objects from data ingestion as the parameter
    ## and returns the KnowledgeGraph object with concepts, resources, examples, and edges
    def build_from_resources(self, resources: list[Resource]) -> KnowledgeGraph:
        logger.info(
            f"Building hybrid knowledge graph from {len(resources)} resources"
        )

        ## Step 1: Insert into nano-graphrag for document indexing
        ## This creates the GraphRAG entities, relationships, and communities
        ## nano-graphrag stores its own files: graph_chunk_entity_relation.graphml, etc.
        logger.info("Step 1: Inserting into nano-graphrag...")
        self.nano_rag.insert_resources(resources)

        ## Step 2: Build custom graph for concepts, examples, and relationships
        ## This extracts educational concepts, prerequisites, examples using LLM prompts
        ## Stored in erica_metadata.json for our custom logic
        logger.info("Step 2: Building custom concept graph...")
        kg = self.custom_builder.build_from_resources(resources)

        ## Step 3: Save custom metadata alongside nano-graphrag
        ## Both graphs live in the same directory but serve different purposes
        self.nano_rag.save_custom_metadata(kg)

        logger.info(
            f"Hybrid graph built: "
            f"{len(kg.concepts)} concepts, "
            f"{len(kg.resources)} resources, "
            f"{len(kg.examples)} examples, "
            f"{len(kg.edges)} edges"
        )

        return kg

    ## This function queries using nano-graphrag retrieval.
    ## It takes in the users question and the mode as arguments and returns the query result from nano-graphrag
    def query_nano_graphrag(
        self, question: str, mode: str = "local"
    ) -> dict:
        return self.nano_rag.query(question, mode=mode)

    ## This function gets the custom knowledge graph.
    def get_custom_graph(self) -> KnowledgeGraph:
        return self.custom_builder.kg

    ## This function loads the knowledge graph
    def load(self) -> KnowledgeGraph:
        ## Load custom metadata
        kg = self.nano_rag.load_custom_metadata()

        if kg:
            self.custom_builder.kg = kg
            logger.info("Loaded hybrid knowledge graph")
        else:
            logger.warning("No custom metadata found")
            kg = KnowledgeGraph()

        return kg

    ## This function saves the knowledge graph
    def save(self) -> None:
        ## nano-graphrag saves automatically on insert
        ## Save custom metadata
        self.nano_rag.save_custom_metadata(self.custom_builder.kg)
        logger.info("Saved hybrid knowledge graph")

    ## This function gets the stats about the hybrid graph and returns a dictionary with the stats
    def get_stats(self) -> dict:
        nano_stats = self.nano_rag.get_graph_stats()
        custom_stats = {
            "concepts": len(self.custom_builder.kg.concepts),
            "resources": len(self.custom_builder.kg.resources),
            "examples": len(self.custom_builder.kg.examples),
            "edges": len(self.custom_builder.kg.edges),
        }

        return {
            "nano_graphrag": nano_stats,
            "custom_graph": custom_stats,
        }
