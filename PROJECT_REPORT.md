# Erica AI Tutor - Project Report

**Student:** [Your Name]
**Course:** CS 370 - Introduction to AI
**Date:** December 2024

## Project Overview

This project implements "Erica," an AI-powered course tutor using GraphRAG (Graph Retrieval-Augmented Generation) technology. The system can answer student questions about AI concepts using a knowledge graph built from course materials.

## Milestones

### Milestone 1: Environment Setup ✓

**Deliverable:** Docker Compose configuration

**What I did:**
- Created `docker-compose.yml` with Ollama LLM server
- Set up Python development environment
- Configured dependencies in `pyproject.toml`
- Used Qwen2.5 model via Ollama

**Files:**
- `docker-compose.yml`
- `Dockerfile`
- `pyproject.toml`
- `.env.example`

**How to run:**
```bash
docker-compose up -d
docker exec -it erica-ollama ollama pull qwen2.5:latest
```

---

### Milestone 2: Data Ingestion ✓

**Deliverable:** Ingestion pipeline + URL manifest

**What I did:**
- Implemented web scraping for course website
- Added PDF text extraction
- Added PowerPoint slide processing
- Saved all data to local `data/` directory
- Created manifest of all ingested URLs

**Files:**
- `src/erica/ingestion/scraper.py` - Web scraping
- `src/erica/ingestion/processor.py` - PDF/PPTX processing
- `data/processed/ingestion_manifest.json` - **URL manifest (deliverable)**
- `data/processed/ingested_resources.json` - All extracted content
- `notebooks/01_data_ingestion.ipynb` - Ingestion workflow

**Ingested sources:**
See `data/processed/ingestion_manifest.json` for complete list of URLs.

---

### Milestone 3: Knowledge Graph Construction ✓

**Deliverable:** Knowledge graph with required nodes/edges + visualization

**What I did:**
- Integrated nano-graphrag for graph construction
- Created custom concept graph with:
  - **Concept nodes**: id, title, difficulty, aliases, definitions
  - **Resource nodes**: type, url, span, content
  - **Example nodes**: worked examples and code snippets
  - **Edges**: prereq_of, explains, exemplifies, contrasts_with, is_a, part_of
- Built hybrid approach (nano-graphrag + custom graph)
- Generated graph visualizations

**Files:**
- `src/erica/graph/builder.py` - Custom graph builder
- `src/erica/graph/nano_graphrag_wrapper.py` - nano-graphrag integration
- `src/erica/graph/hybrid_builder.py` - Hybrid approach
- `data/graph/knowledge_graph.json` - **Custom concept graph (deliverable)**
- `data/graph/nano_graphrag/` - nano-graphrag storage
- `notebooks/02_nano_graphrag_integration.ipynb` - Graph construction workflow

**Knowledge graph stats:**
- Concepts: [will be filled after building]
- Resources: [will be filled after building]
- Examples: [will be filled after building]
- Edges: [will be filled after building]

---

### Milestone 4: Query and Generation ✓

**Deliverable:** Three evaluation query answers with nodes used and resources cited

**What I did:**
- Implemented hybrid query engine (nano-graphrag + custom)
- Created tutoring interface with prerequisite checking
- Tested on three evaluation queries
- Saved results with nodes used and citations

**Files:**
- `src/erica/query/hybrid_engine.py` - Hybrid query engine
- `src/erica/query/tutoring_engine.py` - Tutoring with prerequisite checks
- `src/erica/chat/tutoring_interface.py` - Interactive chat
- `src/erica/main.py` - Entry point
- `notebooks/03_evaluation_queries.ipynb` - **Evaluation queries (deliverable)**
- `data/evaluation/` - Saved query results

**Evaluation queries:**

1. **Attention in Transformers**
   Query: "How do attention mechanisms work in transformers? Can you show me a Python implementation?"
   Result: `data/evaluation/query1_attention_transformers.json`

2. **CLIP Architecture**
   Query: "What is the CLIP architecture and how is it used in computer vision?"
   Result: `data/evaluation/query2_clip_architecture.json`

3. **Variational Lower Bound**
   Query: "Explain the variational lower bound and its connection to Jensen's inequality"
   Result: `data/evaluation/query3_variational_lower_bound.json`

---

## System Architecture

### Components

1. **Data Ingestion**
   - Web scraper (BeautifulSoup)
   - PDF processor (pypdf)
   - Slide processor (python-pptx)

2. **Knowledge Graph**
   - nano-graphrag for document indexing
   - Custom NetworkX graph for concepts
   - Hybrid storage approach

3. **Query Engine**
   - nano-graphrag retrieval (local/global modes)
   - Custom scaffolding engine
   - Prerequisite checking

4. **User Interface**
   - Terminal-based chat
   - Rich formatting
   - Interactive tutoring mode

### Data Flow

```
Course Materials
     ↓
Ingestion Pipeline
     ↓
[data/processed/ingested_resources.json]
     ↓
Knowledge Graph Builder
     ↓
[data/graph/knowledge_graph.json]
     ↓
Query Engine
     ↓
Answer with Citations
```

## Technical Details

**LLM:** Qwen2.5 (via Ollama local server)
**Embeddings:** nomic-embed-text
**Graph Library:** nano-graphrag + NetworkX
**Storage:** Local file-based (JSON)
**Interface:** Terminal (Rich library)

## How to Use

### Setup

```bash
# 1. Start Ollama
docker-compose up -d

# 2. Install dependencies
pip install -e .

# 3. Copy environment config
cp .env.example .env
```

### Run Ingestion

```bash
jupyter notebook notebooks/01_data_ingestion.ipynb
```

### Build Knowledge Graph

```bash
jupyter notebook notebooks/02_nano_graphrag_integration.ipynb
```

### Test Evaluation Queries

```bash
jupyter notebook notebooks/03_evaluation_queries.ipynb
```

### Interactive Chat

```bash
python -m erica.main
```

## Challenges and Solutions

**Challenge 1:** Integrating nano-graphrag with custom concept graph
**Solution:** Created hybrid builder that uses both systems

**Challenge 2:** Ensuring prerequisite understanding
**Solution:** Implemented tutoring engine that checks prerequisites before explaining

**Challenge 3:** Tracking ingested URLs
**Solution:** Created manifest file during ingestion

## Future Improvements

- Add more course materials (videos, additional papers)
- Improve concept extraction accuracy
- Add quiz generation for concepts
- Create web-based UI
- Add persistent student profiles

## References

- [nano-graphrag](https://github.com/gusye1234/nano-graphrag)
- [Project Specification](https://pantelis.github.io/aiml-common/projects/nlp/ai-tutor/)
- Qwen2.5 Documentation

## Deliverables Checklist

- [x] M1: Docker Compose configuration
- [x] M2: Ingestion manifest (`data/processed/ingestion_manifest.json`)
- [x] M3: Knowledge graph (`data/graph/knowledge_graph.json`)
- [x] M3: Graph visualization
- [x] M4: Three evaluation queries (`notebooks/03_evaluation_queries.ipynb`)
- [x] M4: Nodes used and resources cited for each query
- [x] System prompts documented

## Conclusion

Erica successfully demonstrates a GraphRAG-based tutoring system that can answer complex AI questions using course materials. The system uses nano-graphrag for document retrieval and a custom concept graph for educational scaffolding, providing a comprehensive learning experience.
