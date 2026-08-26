"""Graph storage and retrieval using NetworkX."""

import logging
from typing import Any

import networkx as nx

from socratic.models import KnowledgeGraph, RelationType

logger = logging.getLogger(__name__)


class GraphStorage:
    """Manages graph storage and querying using NetworkX."""

    def __init__(self, knowledge_graph: KnowledgeGraph):
        """Initialize graph storage.

        Args:
            knowledge_graph: Knowledge graph to store
        """
        self.kg = knowledge_graph
        self.graph = nx.MultiDiGraph()
        self._build_networkx_graph()

    def _build_networkx_graph(self) -> None:
        """Build NetworkX graph from knowledge graph."""
        # Add concept nodes
        for concept_id, concept in self.kg.concepts.items():
            self.graph.add_node(
                concept_id,
                type="concept",
                title=concept.title,
                difficulty=concept.difficulty,
                data=concept.model_dump(),
            )

        # Add resource nodes
        for resource_id, resource in self.kg.resources.items():
            self.graph.add_node(
                resource_id,
                type="resource",
                title=resource.title,
                resource_type=resource.type,
                data=resource.model_dump(),
            )

        # Add example nodes
        for example_id, example in self.kg.examples.items():
            self.graph.add_node(
                example_id, type="example", title=example.title, data=example.model_dump()
            )

        # Add edges
        for edge in self.kg.edges:
            self.graph.add_edge(
                edge.source_id,
                edge.target_id,
                relation=edge.relation_type.value,
                weight=edge.weight,
            )

        logger.info(
            f"NetworkX graph built: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges"
        )

    def find_concept_by_title(self, title: str) -> str | None:
        """Find concept ID by title (case-insensitive).

        Args:
            title: Concept title to search for

        Returns:
            Concept ID if found, None otherwise
        """
        title_lower = title.lower()
        for node, data in self.graph.nodes(data=True):
            if data.get("type") == "concept":
                if data.get("title", "").lower() == title_lower:
                    return node
        return None

    def get_subgraph_for_concepts(self, concept_ids: list[str], depth: int = 2) -> nx.Graph:
        """Extract subgraph containing specified concepts and their neighbors.

        Args:
            concept_ids: List of concept IDs to include
            depth: How many hops to include from each concept

        Returns:
            Subgraph containing concepts and related nodes
        """
        nodes_to_include = set(concept_ids)

        # Add neighbors up to specified depth
        for concept_id in concept_ids:
            if concept_id in self.graph:
                # Get all nodes within depth hops
                for node in nx.single_source_shortest_path_length(
                    self.graph, concept_id, cutoff=depth
                ):
                    nodes_to_include.add(node)

        subgraph = self.graph.subgraph(nodes_to_include).copy()
        logger.info(f"Extracted subgraph with {subgraph.number_of_nodes()} nodes")
        return subgraph

    def get_prerequisite_chain(self, concept_id: str) -> list[str]:
        """Get ordered list of prerequisite concepts.

        Args:
            concept_id: Concept to find prerequisites for

        Returns:
            List of concept IDs in prerequisite order (leaf to target)
        """
        prereqs = []

        # Find all nodes that have prereq_of edge to this concept
        for source, target, data in self.graph.in_edges(concept_id, data=True):
            if data.get("relation") == RelationType.PREREQ_OF.value:
                # Recursively get prerequisites
                prereqs.extend(self.get_prerequisite_chain(source))
                prereqs.append(source)

        return prereqs

    def get_resources_for_concept(self, concept_id: str) -> list[dict[str, Any]]:
        """Get all resources that explain a concept.

        Args:
            concept_id: Concept ID

        Returns:
            List of resource data
        """
        resources = []

        for source, target, data in self.graph.in_edges(concept_id, data=True):
            if data.get("relation") == RelationType.EXPLAINS.value:
                node_data = self.graph.nodes[source]
                if node_data.get("type") == "resource":
                    resources.append(node_data.get("data"))

        return resources

    def get_examples_for_concept(self, concept_id: str) -> list[dict[str, Any]]:
        """Get all examples that demonstrate a concept.

        Args:
            concept_id: Concept ID

        Returns:
            List of example data
        """
        examples = []

        for source, target, data in self.graph.in_edges(concept_id, data=True):
            if data.get("relation") == RelationType.EXEMPLIFIES.value:
                node_data = self.graph.nodes[source]
                if node_data.get("type") == "example":
                    examples.append(node_data.get("data"))

        return examples

    def visualize_subgraph(self, concept_ids: list[str], output_path: str) -> None:
        """Create visualization of subgraph.

        Args:
            concept_ids: Concepts to visualize
            output_path: Path to save visualization
        """
        import matplotlib.pyplot as plt

        subgraph = self.get_subgraph_for_concepts(concept_ids)

        # Color nodes by type
        color_map = {
            "concept": "#FF6B6B",
            "resource": "#4ECDC4",
            "example": "#95E1D3",
        }

        node_colors = [
            color_map.get(subgraph.nodes[node].get("type"), "#CCCCCC")
            for node in subgraph.nodes()
        ]

        plt.figure(figsize=(15, 10))
        pos = nx.spring_layout(subgraph, k=1, iterations=50)

        nx.draw(
            subgraph,
            pos,
            node_color=node_colors,
            with_labels=True,
            labels={node: subgraph.nodes[node].get("title", node) for node in subgraph.nodes()},
            node_size=1000,
            font_size=8,
            font_weight="bold",
            arrows=True,
            edge_color="#888888",
            arrowsize=20,
        )

        plt.title("Knowledge Graph Subgraph")
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Subgraph visualization saved to {output_path}")
