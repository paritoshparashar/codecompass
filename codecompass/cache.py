import os
import shutil
import joblib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
CACHE_DIR = Path("./_cache")

def get_cache_path(repo_name: str) -> Path:
    repo_cache_dir = CACHE_DIR / repo_name
    repo_cache_dir.mkdir(parents=True, exist_ok=True)
    return repo_cache_dir

def save_cache(repo_name: str, graph, embeddings: dict):
    cache_dir = get_cache_path(repo_name)
    joblib.dump(graph, cache_dir / "graph.joblib")
    joblib.dump(embeddings, cache_dir / "embeddings.joblib")
    logger.info(f"Cache saved for {repo_name}")

def load_cache(repo_name: str):
    cache_dir = get_cache_path(repo_name)
    graph_path = cache_dir / "graph.joblib"
    emb_path = cache_dir / "embeddings.joblib"
    
    if graph_path.exists() and emb_path.exists():
        logger.info(f"Cache hit for {repo_name}. Loading from disk...")
        return joblib.load(graph_path), joblib.load(emb_path)
    return None, None

def clear_cache(repo_name: str):
    cache_dir = get_cache_path(repo_name)
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        logger.info(f"Cache cleared for {repo_name}")