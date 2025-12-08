## Construction of knowledge graph from resources

import json
import logging
from pathlib import Path

from erica.config import settings
from erica.models import Concept, Edge, Example, KnowledgeGraph, RelationType, Resource
from erica.utils.llm_client import llm_client

logger = logging.getLogger(__name__)

## Builds knowledge graph from ingested resources
class KnowledgeGraphBuilder:

    ## This function initializes the knowledge graph builder
    def __init__(self):
        self.kg = KnowledgeGraph()

    ## This function extracts concepts from the resource using LLM. The only parameter is the resource it is extracting from and returns a list of concepts.
    def extract_concepts_from_resource(self, resource: Resource) -> list[Concept]:
        system_prompt = """You are an expert at analyzing educational content and extracting key concepts.
You MUST respond with ONLY valid JSON - no other text before or after.
Extract the main concepts from the provided text.

Your response must be a JSON array following this exact format:
[
  {
    "id": "concept_id_lowercase",
    "title": "Concept Title",
    "difficulty": 3,
    "aliases": ["alternative name"],
    "definitions": ["clear definition"]
  }
]

IMPORTANT: Return ONLY the JSON array, nothing else."""

        prompt = f"""Analyze this educational content and extract 3-5 key concepts:

Title: {resource.title}
Content:
{resource.content[:4000]}

Respond with ONLY a JSON array. Each concept must have: id, title, difficulty (1-5), aliases (array), definitions (array).
Example format:
[
  {{"id": "machine_learning", "title": "Machine Learning", "difficulty": 3, "aliases": ["ML"], "definitions": ["A field of AI focused on learning from data"]}}
]"""

        try:
            response = llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=2000,
            )

            ## Clean response - remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            ## Parse JSON response
            concepts_data = json.loads(response)

            ## Validate it's a list
            if not isinstance(concepts_data, list):
                logger.warning(f"LLM returned non-list JSON for {resource.id}, wrapping in list")
                concepts_data = [concepts_data]

            ## Convert to Concept objects with validation
            concepts = []
            for c_data in concepts_data:
                try:
                    ## Ensure required fields exist with defaults
                    if "id" not in c_data or "title" not in c_data:
                        logger.warning(f"Skipping concept with missing id/title: {c_data}")
                        continue

                    ## Set defaults for optional fields
                    c_data.setdefault("difficulty", 3)
                    c_data.setdefault("aliases", [])
                    c_data.setdefault("definitions", [])

                    ## Ensure definitions is a list
                    if isinstance(c_data.get("definitions"), str):
                        c_data["definitions"] = [c_data["definitions"]]

                    concept = Concept(**c_data)
                    concepts.append(concept)
                except Exception as e:
                    logger.warning(f"Failed to create concept from {c_data}: {e}")
                    continue

            logger.info(f"Extracted {len(concepts)} concepts from {resource.id}")
            return concepts

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error for {resource.id}: {e}")
            logger.debug(f"LLM response was: {response[:200]}")
            return []
        except Exception as e:
            logger.error(f"Error extracting concepts from {resource.id}: {e}")
            return []

    ## This function extracts worked examples from a resource using LLM . This function returns a list of extracted examples
    def extract_examples_from_resource(self, resource: Resource) -> list[Example]:
 
        system_prompt = """You are an expert at identifying worked examples in educational content.
You MUST respond with ONLY valid JSON - no other text before or after.

Your response must be a JSON array following this exact format:
[
  {
    "id": "example_id_lowercase",
    "title": "Example Title",
    "content": "Full example content",
    "code_snippet": "optional code",
    "language": "python"
  }
]

If there are no examples, return an empty array: []
IMPORTANT: Return ONLY the JSON array, nothing else."""

        prompt = f"""Find worked examples, code snippets, or demonstrations in this content:

{resource.content[:4000]}

Respond with ONLY a JSON array of examples (or empty array [] if none found).
Each example must have: id, title, content. Optional: code_snippet, language.
Example format:
[
  {{"id": "linear_regression_example", "title": "Linear Regression Example", "content": "Step by step solution...", "code_snippet": "y = mx + b", "language": "python"}}
]"""

        try:
            response = llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=2000,
            )

            ## Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            ## Parse JSON
            examples_data = json.loads(response)

            ## Validate it's a list
            if not isinstance(examples_data, list):
                logger.warning(f"LLM returned non-list JSON for examples in {resource.id}")
                examples_data = [examples_data] if examples_data else []

            ## Convert to Example objects
            examples = []
            for e_data in examples_data:
                try:
                    ## Ensure required fields
                    if "id" not in e_data or "title" not in e_data or "content" not in e_data:
                        logger.warning(f"Skipping example with missing required fields: {e_data}")
                        continue

                    ## Set defaults
                    e_data.setdefault("code_snippet", None)
                    e_data.setdefault("language", None)

                    example = Example(**e_data)
                    examples.append(example)
                except Exception as e:
                    logger.warning(f"Failed to create example from {e_data}: {e}")
                    continue

            logger.info(f"Extracted {len(examples)} examples from {resource.id}")
            return examples

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error for examples in {resource.id}: {e}")
            logger.debug(f"LLM response was: {response[:200]}")
            return []
        except Exception as e:
            logger.error(f"Error extracting examples from {resource.id}: {e}")
            return []

    ## This function identifies relationships between concepts so that it knows what to teach first using LLM.
    ## It takes in concepts as well as the resource that is used to get the relationship.
    ## This function then returns a list of edges which represents the relationships between the concepts
    def identify_relationships(
        self, concepts: list[Concept], resource: Resource
    ) -> list[Edge]:
        if len(concepts) < 2:
            return []

        system_prompt = """You are an expert at understanding relationships between concepts.
You MUST respond with ONLY valid JSON - no other text before or after.

Valid relationship types:
- prereq_of: A is a prerequisite for B
- contrasts_with: A and B are contrasting concepts
- is_a: A is a type of B (hierarchical)
- part_of: A is a component of B

Your response must be a JSON array following this exact format:
[
  {
    "source_id": "concept_a_id",
    "target_id": "concept_b_id",
    "relation_type": "prereq_of"
  }
]

If there are no relationships, return an empty array: []
IMPORTANT: Return ONLY the JSON array, nothing else."""

        concept_list = "\n".join([f"- {c.id}: {c.title}" for c in concepts])

        prompt = f"""Given these concepts from the same resource:

{concept_list}

Identify relationships between them.
Respond with ONLY a JSON array (or empty array [] if no clear relationships).
Each relationship must have: source_id, target_id, relation_type (one of: prereq_of, contrasts_with, is_a, part_of).
Example format:
[
  {{"source_id": "linear_algebra", "target_id": "machine_learning", "relation_type": "prereq_of"}}
]"""

        try:
            response = llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=1500,
            )

            ## Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            ## Parse JSON
            edges_data = json.loads(response)

            ## Validate it's a list
            if not isinstance(edges_data, list):
                logger.warning(f"LLM returned non-list JSON for relationships")
                edges_data = [edges_data] if edges_data else []

            edges = []
            valid_concept_ids = {c.id for c in concepts}

            for edge_dict in edges_data:
                try:
                    ## Validate required fields
                    if "source_id" not in edge_dict or "target_id" not in edge_dict or "relation_type" not in edge_dict:
                        logger.warning(f"Skipping edge with missing fields: {edge_dict}")
                        continue

                    ## Validate concept IDs exist
                    if edge_dict["source_id"] not in valid_concept_ids or edge_dict["target_id"] not in valid_concept_ids:
                        logger.warning(f"Skipping edge with invalid concept IDs: {edge_dict}")
                        continue

                    ## Validate relation type
                    try:
                        relation_type = RelationType(edge_dict["relation_type"])
                    except ValueError:
                        logger.warning(f"Invalid relation type '{edge_dict['relation_type']}', skipping edge")
                        continue

                    edge = Edge(
                        source_id=edge_dict["source_id"],
                        target_id=edge_dict["target_id"],
                        relation_type=relation_type,
                    )
                    edges.append(edge)

                except Exception as e:
                    logger.warning(f"Failed to create edge from {edge_dict}: {e}")
                    continue

            logger.info(f"Identified {len(edges)} relationships")
            return edges

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error for relationships: {e}")
            logger.debug(f"LLM response was: {response[:200]}")
            return []
        except Exception as e:
            logger.error(f"Error identifying relationships: {e}")
            return []

    ## This function builds the knowledge graph from a list of resources.
    ## It takes in a list of resources that are processed and returns the constructed knowledge graph.
    def build_from_resources(self, resources: list[Resource]) -> KnowledgeGraph:

        logger.info(f"Building knowledge graph from {len(resources)} resources")

        all_concepts = []

        for resource in resources:
            ## Extract concepts
            concepts = self.extract_concepts_from_resource(resource)
            for concept in concepts:
                self.kg.concepts[concept.id] = concept
                all_concepts.append(concept)

            ## Extract examples
            examples = self.extract_examples_from_resource(resource)
            for example in examples:
                self.kg.examples[example.id] = example

                ## Link example to concepts (by matching keywords)
                for concept in concepts:
                    if concept.title.lower() in example.content.lower():
                        edge = Edge(
                            source_id=example.id,
                            target_id=concept.id,
                            relation_type=RelationType.EXEMPLIFIES,
                        )
                        self.kg.edges.append(edge)

            ## Add resource to graph
            self.kg.resources[resource.id] = resource

            ## Link resource to concepts
            for concept in concepts:
                edge = Edge(
                    source_id=resource.id,
                    target_id=concept.id,
                    relation_type=RelationType.EXPLAINS,
                )
                self.kg.edges.append(edge)

            ## Identify relationships between concepts
            if len(concepts) >= 2:
                edges = self.identify_relationships(concepts, resource)
                self.kg.edges.extend(edges)

        logger.info(
            f"Knowledge graph built: {len(self.kg.concepts)} concepts, "
            f"{len(self.kg.resources)} resources, {len(self.kg.examples)} examples, "
            f"{len(self.kg.edges)} edges"
        )

        return self.kg

    ## This function saves the knowledge graph to a file and takes in the path to save the file to as the argument.
    def save(self, path: Path | None = None) -> None:

        path = path or settings.graph_storage_path / "knowledge_graph.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(self.kg.model_dump_json(indent=2))

        logger.info(f"Knowledge graph saved to {path}")

    ## This function loads the knowledge graph from a file.
    ## It takes in the path to load from and returns the loaded knowledge graph.
    def load(self, path: Path | None = None) -> KnowledgeGraph:

        path = path or settings.graph_storage_path / "knowledge_graph.json"

        with open(path, "r", encoding="utf-8") as f:
            self.kg = KnowledgeGraph.model_validate_json(f.read())

        logger.info(f"Knowledge graph loaded from {path}")
        return self.kg
