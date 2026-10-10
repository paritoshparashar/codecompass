# CodeCompass 

---

## 1. What it is

CodeCompass is an internally-hosted tool that a startup points at its own private GitHub repository. It takes a plain-text ticket (a Jira ticket, a GitHub issue, a Slack message) and instead of writing a generic explanation, it **classifies what kind of problem the ticket is** — bug, missing feature, missing documentation, missing test coverage, or performance issue — and runs a **type-specific evidence pipeline** that produces something concrete and verifiable: a live reproduction of a crash, a working analog of a feature scaffolded into the codebase, the exact test-suite gaps that would let a regression through, or a flame graph of where time actually goes. A small LLM narrates around that evidence rather than authoring the explanation from scratch. The system also **gets better on that specific repository over time**, because every issue that gets closed becomes a training example for a repo-specific reranker.

---
## 2. The use case this is built for

**Persona:** A fast-growing Berlin AI startup with a large, undocumented Python monolith, three newly hired Werkstudents, and a CTO who is spending ~10 hours a week answering "where do I even start" questions instead of building.

**Pain:** Every new ticket requires either (a) reading unfamiliar code cold, or (b) interrupting a senior engineer.

**What CodeCompass changes:** the startup hosts CodeCompass against their private repo once. From then on, a Werkstudent pastes a ticket in and gets back *evidence*, not just a text answer — something they can run, look at, or compare against, that gets them oriented in minutes instead of hours. The product goal is explicitly **"understand the issue faster,"** not "auto-write the PR." A tool that writes the PR for them teaches them nothing and a CTO reviewing junior work doesn't actually want that; a tool that gets them to the right place with the right context, fast, is what actually saves the CTO's time *and* makes the Werkstudent independent.

---

## Key Features
- **Hybrid Ranking Engine:** Combines Semantic Search (sentence-transformers) with Structural Centrality (NetworkX PageRank) to find the most relevant files.
- **Interactive Call Graph:** Visualizes code dependencies using PyVis. Red nodes indicate the top-ranked files.
- **RAG Explanations:** Integrates local LLMs (Ollama) to generate technical explanations for *why* a file is relevant.
- **High-Performance Caching:** Uses Joblib to cache AST graphs and embeddings, reducing query latency from **45s to ~2s** for subsequent searches.

## Architecture
1. **Ingestion:** Clones repositories via GitPython and extracts Python files.
2. **Parsing:** Parses code into an Abstract Syntax Tree (AST) to build a directed call graph.
3. **Embedding:** Converts code chunks and issue text into 384-dimensional vectors using `all-MiniLM-L6-v2`.
4. **Ranking:** Calculates a weighted score: `Score = (α * Semantic Similarity) + ((1-α) * PageRank)`.
5. **Visualization:** Generates an interactive network graph highlighting the root-cause candidates.

## Tech Stack
- **Backend:** FastAPI, Python 3.11
- **ML/NLP:** sentence-transformers, NetworkX, Ollama (Llama 3)
- **Frontend:** Streamlit, PyVis
- **Performance:** Joblib (Disk Caching), NumPy

## Performance Optimization
- **Problem:** Embedding large repositories (e.g., Pydantic, 100+ files) takes ~45 seconds on CPU.
- **Solution:** Implemented disk-based caching for the NetworkX graph and file embeddings.
- **Result:** First run takes ~45s. Subsequent runs on the same repository take **<2 seconds**.

## Project Structure
- `codecompass/repo.py`: Repository cloning and file extraction
- `codecompass/parser.py`: AST parsing and NetworkX graph generation
- `codecompass/embedder.py`: Vector embedding with chunking and mean pooling
- `codecompass/ranker.py`: Hybrid semantic + structural scoring
- `codecompass/explainer.py`: LLM RAG explanation generation
- `codecompass/viz.py`: PyVis interactive graph generation
- `codecompass/cache.py`: Joblib-based disk caching
