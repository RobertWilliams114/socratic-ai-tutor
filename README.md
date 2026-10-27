# Socratic

**A GraphRAG tutor that refuses to answer until you understand the prerequisites.**

Most RAG chatbots answer whatever you ask. Socratic doesn't. Ask it to explain AI agents and it first walks the concept graph backwards, finds that you need machine learning and reinforcement learning first, generates a comprehension question for each, evaluates your free-text answer with an LLM, and only then gives you the full explanation — built up in order.

Runs entirely on local models. No API keys, no data leaving the machine.

---

## What it looks like

```
You: Explain AI agents

Socratic:
Before we dive into AI Agents, I want to make sure you understand
the foundational concepts first.

To fully grasp AI Agents, you should understand:
  1. Machine Learning
  2. Reinforcement Learning

Quick check: Can you give an example of how machine learning is used?

You: Recommendation systems like Netflix, where the algorithm learns
     from viewing history to suggest shows.

Socratic:
✓ Excellent! You understand how ML applies to real-world systems.

Next prerequisite check:
Reinforcement Learning — how do RL agents learn through interaction
with their environment?

You: They try actions, get rewards or penalties, and learn which
     actions lead to better outcomes over time.

Socratic:
✓ Perfect! You've captured the core RL learning mechanism.

Great — now you're ready for the full explanation.
[detailed explanation of AI Agents, with citations]

✓ Concepts covered: machine_learning, reinforcement_learning, ai_agents
```

Other commands: `path <topic>` shows the full prerequisite chain and how much of it you've mastered; `reset` clears your progress; `quit` exits.

---

## How it works

Socratic runs two retrieval systems side by side and merges them at query time.

```
   Course materials (web pages, PDFs, slides)
                    │
            Ingestion pipeline
                    │
        ┌───────────┴────────────┐
        │                        │
   nano-graphrag          Custom concept graph
   ─────────────          ───────────────────
   entity extraction      concepts + difficulty
   community detection    prereq_of edges
   vector retrieval       worked examples
        │                 cited source spans
        └───────────┬────────────┘
                    │
            Tutoring engine
     (traverse prereqs → generate check
      questions → evaluate answers → gate)
                    │
            Terminal chat interface
```

**Why hybrid?** nano-graphrag is good at "find me relevant text about X" but has no notion of *pedagogical order*. The custom NetworkX graph adds what teaching actually needs: difficulty ratings, `prereq_of` relationships, and worked examples. The tutoring engine walks that second graph to decide what to ask before it lets the first one answer.

### Knowledge graph, as built

| | |
|---|---|
| Concepts | 20 |
| Resources | 5 |
| Worked examples | 1 |
| Edges | 59 — of which **25 are `prereq_of`** |
| nano-graphrag entity graph | 113 nodes, 41 edges |

Edge types: `prereq_of`, `explains`, `exemplifies`, `contrasts_with`, `is_a`, `part_of`.

### Design decisions

**Gating answers instead of just ranking them.** The obvious way to build a tutor is to retrieve the best passage and return it. That produces a search engine with a friendly tone — it will happily explain backpropagation to someone who doesn't know what a gradient is. Socratic inverts the flow: before generating anything, the tutoring engine traverses `prereq_of` edges from the requested concept, generates a comprehension question for each unmet prerequisite, and evaluates the student's free-text answer with the LLM. The explanation is withheld until the chain is satisfied. This makes the concept graph load-bearing rather than decorative — the pedagogy lives in the graph structure, not in the prompt.

**Recording provenance at ingestion, not at answer time.** Every ingested source is written to a manifest with its URL and identifier before any graph construction happens. That means citations are traceable to a specific document and span rather than reconstructed after the fact, and rebuilding the graph can't silently orphan a citation. It also makes it obvious what the corpus actually contains — which matters when the retrieval quality is only ever as good as what went in.

---

## Quickstart

**Requirements:** Python 3.10–3.13 (3.12 recommended), [Ollama](https://ollama.com), ~5 GB disk for models.

```bash
# 1. Models
ollama pull qwen2.5
ollama pull nomic-embed-text

# 2. Environment  (uv recommended; python -m venv works too)
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e .

# 3. Run
python -m socratic.main
```

> **Note on Python version:** the dependency set does not yet support 3.14. If your system Python is newer, `uv venv --python 3.12` will fetch a suitable interpreter for you.

### Building the knowledge base

**The repository ships the concept graph but not the source corpus**, because the ingested material is third-party course content that isn't mine to redistribute. `data/graph/knowledge_graph.json` contains the full graph structure — every concept, edge, and citation URL — with the scraped page bodies removed.

To build a runnable knowledge base from your own sources, run the notebooks in order:

| Notebook | Produces |
|---|---|
| `00_setup_and_test.ipynb` | Verifies Ollama connectivity |
| `01_data_ingestion.ipynb` | Scrapes/parses sources → `data/raw/`, `data/processed/` |
| `02_nano_graphrag_integration.ipynb` | Builds the hybrid graph → `data/hybrid_graph/` |
| `03_evaluation_queries.ipynb` | Runs the evaluation queries → `data/evaluation/` |

Point `01_data_ingestion.ipynb` at your own URLs and the rest of the pipeline follows.

---

## Evaluation

Three queries chosen to exercise different retrieval paths. Results are checked in under `data/evaluation/`.

| Query | Tests |
|---|---|
| How do attention mechanisms work in transformers? | Technical depth, code examples |
| What is the CLIP architecture? | Multimodal / vision concepts |
| Explain the variational lower bound and Jensen's inequality | Mathematical reasoning |

Each result records the answer, the graph nodes used, and resource citations with URLs — so retrieval is auditable rather than a black box.

---

## Project layout

```
src/socratic/
├── ingestion/   scraper.py, processor.py      web, PDF, PPTX → text
├── graph/       builder.py, hybrid_builder.py, nano_graphrag_wrapper.py, storage.py
├── query/       engine.py, hybrid_engine.py, tutoring_engine.py
├── chat/        interface.py, tutoring_interface.py
└── utils/       llm_client.py
```

21 modules, ~2,600 lines. `tutoring_engine.py` holds the prerequisite logic; `hybrid_builder.py` is where the two graphs get merged.

---

## Stack

Python 3.12 · nano-graphrag · NetworkX · Pydantic · Rich · BeautifulSoup / pypdf / python-pptx · Ollama (Qwen2.5 + nomic-embed-text)

## Limitations

- The demo corpus is small (5 documents, 20 concepts) — enough to exercise every code path, not a broad knowledge base
- Prerequisite edges are LLM-extracted and not hand-verified; some are arguable
- Answer evaluation is LLM-judged, so a confidently wrong answer can occasionally pass
- Terminal-only; no web UI
- `data/graph/knowledge_graph.json` is a snapshot and won't auto-refresh if you rebuild the graph

## Roadmap

- Ingest a broader corpus — lecture video transcripts and papers, not just web pages
- Improve concept-extraction precision so prerequisite edges need less manual review
- Generate practice questions per concept, not only prerequisite checks
- Persistent student profiles, so mastery survives between sessions
- A web interface

## References

- [nano-graphrag](https://github.com/gusye1234/nano-graphrag) — the retrieval layer this builds on
- [Qwen2.5](https://qwenlm.github.io/blog/qwen2.5/) and [nomic-embed-text](https://www.nomic.ai/blog/posts/nomic-embed-text-v1) — the local models used

## Provenance

Originally built as the capstone for CS 370 (Introduction to AI) at NJIT, Fall 2025; cleaned up and extended since. The hybrid-graph design, prerequisite-gating engine, and tutoring interface are my own.
