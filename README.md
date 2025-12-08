# Erica AI Tutor - GraphRAG-based Intelligent Tutoring System

**Student:** Robert Williams
**Course:** CS 370
**Project:** Erica - AI-Powered Course Tutor with Prerequisite Checking

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Ollama** with models:
  - `qwen2.5:latest` (LLM)
  - `nomic-embed-text` (embeddings)

### Installation

```bash
# 1. Install Ollama (if not installed)
# Download from: https://ollama.ai

# 2. Pull required models
ollama pull qwen2.5:latest
ollama pull nomic-embed-text

# 3. Install Python dependencies
cd project
pip install -e .

# 4. Verify Ollama is running
curl http://localhost:11434/api/tags
```

### Run the System

```bash
# Option 1: Use notebooks (RECOMMENDED for grading)
jupyter notebook notebooks/

# Option 2: Command-line interface
python -m erica.main

# Option 3: Quick start script
python quickstart.py
```

---

## System Architecture

### Hybrid GraphRAG Design

```
┌─────────────────────────────────────────────────────────────┐
│                    ERICA AI TUTOR                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌─────────────────────────┐   │
│  │  nano-graphrag   │         │  Custom Concept Graph   │   │
│  │  ─────────────────         │  ───────────────────────   │
│  │  • Document      │         │  • Concepts            │   │
│  │    indexing      │         │  • Prerequisites       │   │
│  │  • Entity        │    +    │  • Examples            │   │
│  │    extraction    │         │  • Difficulty levels   │   │
│  │  • Vector DB     │         │  • Scaffolding logic   │   │
│  └──────────────────┘         └─────────────────────────┘   │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐   │
│  │         Tutoring Engine (Prerequisite Checking)      │   │
│  │  ────────────────────────────────────────────────────────   │
│  │  • Detect prerequisite chains                        │   │
│  │  • Generate understanding check questions            │   │
│  │  • Evaluate student responses                        │   │
│  │  • Track learning progress                           │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐   │
│  │              Interactive Chat Interface               │   │
│  │  ────────────────────────────────────────────────────────   │
│  │  • Terminal-based chat                                │   │
│  │  • Learning path visualization                        │   │
│  │  • Progress tracking                                  │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Installation

### Step 1: Environment Setup

```bash
# Navigate to project directory
cd project

# Install dependencies
pip install -e .

# This installs:
# - nano-graphrag (GraphRAG implementation)
# - networkx (graph algorithms)
# - pydantic (data validation)
# - beautifulsoup4 (web scraping)
# - PyPDF2, python-pptx (document processing)
# - openai (Ollama API client)
# - rich (terminal UI)
# - jupyter (notebooks)
```

### Step 2: Verify Ollama

```bash
# Check Ollama is running
ollama list

# Should show:
# qwen2.5:latest
# nomic-embed-text
```

### Step 3: Configuration

The project uses default configurations. No `.env` file is required unless you want to customize:

```bash
# Optional: Create .env from template
cp .env.example .env

# Defaults (already configured):
# - LLM: qwen2.5:latest
# - Embeddings: nomic-embed-text
# - Ollama URL: http://localhost:11434
```

---

## Running the Notebooks

### IMPORTANT: Run notebooks in ORDER

The notebooks build on each other and must be executed sequentially:

### Notebook 1: Data Ingestion

```bash
jupyter notebook notebooks/01_data_ingestion.ipynb
```

**What it does:**
- Scrapes course website (https://pantelis.github.io/courses/ai/in-person.html)
- Processes web pages, PDFs(I checked even though there weren't any), and slides(Same as PDFs)
- Stores raw content in `data/raw/`
- Creates `data/processed/ingestion_manifest.json`

**Expected output:**
- ~5 resources ingested
- Manifest file with URLs and metadata

### Notebook 2: Knowledge Graph Construction

```bash
jupyter notebook notebooks/02_nano_graphrag_integration.ipynb
```

**What it does:**
- Builds nano-graphrag index from ingested documents
- Extracts concepts, examples, and relationships using LLM
- Creates hybrid graph in `data/hybrid_graph/`
- Generates graph statistics

**Expected output:**
- 20 concepts extracted
- 4 prerequisite relationships
- 5 resources indexed
- 38 total edges in graph

### Notebook 3: Evaluation Queries

```bash
jupyter notebook notebooks/03_evaluation_queries.ipynb
```

**What it does:**
- Tests 3 required evaluation queries
- Demonstrates scaffolded answer generation
- Shows concept identification and resource citations
- Saves results to `data/evaluation/`

**Expected output:**
- 3 JSON files with query results
- Answers in English with proper citations
- Concepts and resources identified

---

## Using the Chat Interface

### Start the Interface

```bash
python -m erica.main
```

### Example Session

```
Loading hybrid knowledge graph from data/hybrid_graph...
Loaded knowledge graph with 20 concepts, 5 resources, 1 examples

Running in tutoring mode (with prerequisite checks)

┌─────────────────────────────────────────────────────────┐
│ Welcome to Erica - Your AI Course Tutor                 │
│                                                          │
│ How I teach:                                             │
│ - I'll check if you understand prerequisites first      │
│ - I'll ask questions to gauge your understanding        │
│ - I'll build your knowledge step-by-step               │
└─────────────────────────────────────────────────────────┘

You: Explain AI agents

Erica:
Before we dive into AI Agents, I want to make sure you understand
the foundational concepts first.

To fully grasp AI Agents, you should understand:
1. Machine Learning
2. Reinforcement Learning

Let's start with the first concept.

Quick check: Can you give an example of how machine learning is used?

You: Machine learning is used in recommendation systems like Netflix,
     where algorithms learn from viewing history to suggest shows.

Erica:
✓ Excellent! You understand how ML applies to real-world systems.

Next prerequisite check:

Reinforcement Learning (RL)
How do RL agents learn through interaction with their environment?

You: They try actions, get rewards or penalties, and learn which
     actions lead to better outcomes over time.

Erica:
✓ Perfect! You've captured the core RL learning mechanism.

Great! Now you're ready for the full explanation.

[Provides detailed explanation of AI Agents...]

✓ Concepts covered: machine_learning, reinforcement_learning, ai_agents
```

### Available Commands

| Command | Description |
|---------|-------------|
| Normal questions | Ask about any AI topic |
| `path <topic>` | Show learning path with prerequisites |
| `reset` | Clear understanding memory |
| `quit` or `exit` | End session |

### Example: Learning Path

```
You: path ai_agents

Learning Path for AI Agents:

  ○ 1. Machine Learning ⭐⭐⭐
  ○ 2. Reinforcement Learning (RL) ⭐⭐⭐⭐
  ○ 3. AI Agents ⭐⭐⭐⭐

You've mastered 0/3 concepts
```

---

## Key Features

### 1. Prerequisite Checking

**How it works:**
1. Student asks about a complex topic (e.g., "AI Agents")
2. System checks prerequisite chain: AI Agents → RL → ML
3. Identifies missing prerequisites
4. Generates understanding check questions
5. Evaluates student responses using LLM
6. Only proceeds when prerequisites are understood

**Implementation:**
- `src/erica/query/tutoring_engine.py` - Core logic
- `src/erica/chat/tutoring_interface.py` - Interactive flow
- Uses NetworkX for graph traversal
- LLM-based question generation and evaluation

### 2. Hybrid GraphRAG

**nano-graphrag component:**
- Lightweight GraphRAG implementation
- Entity extraction from documents
- Community detection
- Vector-based retrieval

**Custom graph component:**
- Concept hierarchy with difficulty levels
- Prerequisite relationships (`prereq_of` edges)
- Examples and worked solutions
- Resource citations with spans

### 3. Scaffolded Learning

**Answer generation follows:**
1. Check prerequisites
2. Explain simpler concepts first
3. Build to more complex ideas
4. Provide examples
5. Cite resources for further reading

### 4. Progress Tracking

**System tracks:**
- Which concepts student understands
- Learning paths for each topic
- Session history
- Can reset and start fresh

---

## Technical Details

### Knowledge Graph Schema

```json
{
  "concepts": {
    "concept_id": {
      "id": "machine_learning",
      "title": "Machine Learning",
      "difficulty": 3,
      "aliases": ["ML", "machine-learning"],
      "definitions": ["Systems that learn from data..."]
    }
  },
  "resources": [
    {
      "id": "resource_id",
      "title": "Introduction to AI",
      "type": "web",
      "url": "https://...",
      "span": "Section 2.1",
      "content": "..."
    }
  ],
  "examples": [...],
  "edges": [
    {
      "source_id": "machine_learning",
      "target_id": "reinforcement_learning",
      "relation_type": "prereq_of"
    }
  ]
}
```

### Evaluation Query Format

Each query result includes:

```json
{
  "query": "How do attention mechanisms work in transformers?",
  "answer": "Attention mechanisms are crucial components...",
  "nodes_used": ["natural_language_processing", "language_models"],
  "citations": [
    {
      "title": "Resource Title",
      "url": "https://...",
      "type": "web"
    }
  ],
  "mode": "local",
  "source": "nano-graphrag"
}
```

### Prerequisites in Graph

Current prerequisite relationships:
1. Machine Learning → Natural Language Processing
2. Machine Learning → Reinforcement Learning
3. Reinforcement Learning → AI Agents
4. Optimization Algorithms → Logistic Regression

---


## Evaluation Queries

The three required evaluation queries test different aspects:

### Query 1: Attention Mechanisms in Transformers
**Tests:** Code examples, NLP concepts, technical depth

### Query 2: CLIP Architecture
**Tests:** Computer vision, multimodal learning, architecture explanation

### Query 3: Variational Lower Bound
**Tests:** Mathematical concepts, theoretical foundations, Jensen's inequality

All three queries demonstrate:
- ✅ Scaffolded answers (simple → complex)
- ✅ Concept identification from knowledge graph
- ✅ Resource citations with URLs
- ✅ Technical accuracy
- ✅ English-language responses

---

## Running the Complete System

### Full Workflow

```bash
# 1. Setup
cd project
pip install -e .

# 2. Run ingestion
jupyter notebook notebooks/01_data_ingestion.ipynb
# Execute all cells

# 3. Build knowledge graph
jupyter notebook notebooks/02_nano_graphrag_integration.ipynb
# Execute all cells

# 4. Run evaluation queries
jupyter notebook notebooks/03_evaluation_queries.ipynb
# Execute all cells

# 5. Test chat interface
python -m erica.main

# 6. Try prerequisite checking
# When prompted, ask: "Explain AI agents"
# Follow the prerequisite questions
```

---

## Submission Contents

This submission includes:

1. ✅ All source code (`src/erica/`)
2. ✅ All Jupyter notebooks (`notebooks/`)
3. ✅ All deliverable files (`data/`)
4. ✅ Documentation (`README.md`, `PROJECT_REPORT.md`, `DELIVERABLES.md`)
5. ✅ Configuration files (`pyproject.toml`, `docker-compose.yml`, etc.)
6. ✅ Working chat interface
7. ✅ Prerequisite checking fully implemented
8. ✅ Three evaluation queries with results

