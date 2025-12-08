## Data models for knowledge graph

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

## Types of learning resources
class ResourceType(str, Enum):

    PDF = "pdf"
    SLIDE = "slide"
    VIDEO = "video"
    WEB = "web"

## Types of relationships between nodes
class RelationType(str, Enum):

    PREREQ_OF = "prereq_of"  ## Prerequisite chain
    EXPLAINS = "explains"  ## Resource explains concept
    EXEMPLIFIES = "exemplifies"  ## Example demonstrates concept
    CONTRASTS_WITH = "contrasts_with"  ## Near transfer
    IS_A = "is_a"  ## Hierarchical relationship
    PART_OF = "part_of"  ## Component relationship

## A course concept node
class Concept(BaseModel):

    id: str
    title: str
    difficulty: int = Field(ge=1, le=5, description="Difficulty level from 1-5")
    aliases: list[str] = Field(default_factory=list)
    definitions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

## A learning resource node
class Resource(BaseModel):

    id: str
    type: ResourceType
    url: str
    title: str = ""
    span: str | None = None  # Page numbers, slide numbers, etc.
    timecodes: list[str] = Field(default_factory=list)  # For videos
    content: str = ""  # Extracted text content
    metadata: dict[str, Any] = Field(default_factory=dict)

## A worked example node
class Example(BaseModel):

    id: str
    title: str
    content: str  ## The actual example content
    code_snippet: str | None = None
    language: str | None = None  ## Programming language if applicable
    metadata: dict[str, Any] = Field(default_factory=dict)

## A relationship between nodes
class Edge(BaseModel):

    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)

## The complete knowledge graph
class KnowledgeGraph(BaseModel):

    concepts: dict[str, Concept] = Field(default_factory=dict)
    resources: dict[str, Resource] = Field(default_factory=dict)
    examples: dict[str, Example] = Field(default_factory=dict)
    edges: list[Edge] = Field(default_factory=list)
