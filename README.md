# CodeCompass 
**AI-Powered Issue-to-Code Navigator**

CodeCompass is a web-based tool that maps GitHub issues to the most relevant code locations in large repositories. It answers the critical question for new contributors: *"I see this bug report — where do I start looking?"*

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
