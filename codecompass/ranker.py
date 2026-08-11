import networkx as nx
import numpy as np
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class CodeRanker:
    """
    Combines semantic similarity (embeddings) and structural centrality (PageRank)
    to produce a final ranked list of files.
    """

    def __init__(self, graph: nx.DiGraph, alpha: float = 0.7):
        """
        :param graph: NetworkX DiGraph of the codebase.
        :param alpha: Weight for semantic similarity (1-alpha is for structural).
        """
        self.graph = graph
        self.alpha = alpha
        self.page_rank = nx.pagerank(graph)
        self._file_pr_scores = self._aggregate_scores_to_files()

    def _aggregate_scores_to_files(self) -> Dict[str, float]:
        """
        Aggregates node-level PageRank scores up to the file level,
        then normalizes them to a [0, 1] scale.
        """
        file_scores = {}
        for node, score in self.page_rank.items():
            # Node format from parser: "file_path::func_name"
            file_path = node.split("::")[0]
            file_scores[file_path] = file_scores.get(file_path, 0.0) + score
            
        # Min-Max Normalization
        if file_scores:
            max_val = max(file_scores.values())
            min_val = min(file_scores.values())
            rng = max_val - min_val if max_val > min_val else 1.0
            for k in file_scores:
                file_scores[k] = (file_scores[k] - min_val) / rng
                
        return file_scores

    def rank_files(self, issue_embedding: np.ndarray, file_embeddings: Dict[str, np.ndarray], top_k: int = 10) -> List[Dict]:
        """
        Calculates combined score for each file and returns the top_k results.
        """
        results = []
        
        paths = list(file_embeddings.keys())
        embeddings = np.array([file_embeddings[p] for p in paths])
        
        if len(embeddings) == 0:
            return []
            
        # Calculate semantic similarity (Cosine similarity) using pure numpy
        dot_products = np.dot(embeddings, issue_embedding)
        norms_files = np.linalg.norm(embeddings, axis=1)
        norm_issue = np.linalg.norm(issue_embedding)
        
        # Avoid division by zero
        norms_files[norms_files == 0] = 1e-10
        
        semantic_scores = dot_products / (norms_files * norm_issue)
        
        # Normalize semantic scores to [0, 1]
        sem_max = np.max(semantic_scores)
        sem_min = np.min(semantic_scores)
        sem_rng = sem_max - sem_min if sem_max > sem_min else 1.0
        semantic_scores = (semantic_scores - sem_min) / sem_rng
            
        # Combine and format
        for i, path in enumerate(paths):
            pr_score = self._file_pr_scores.get(path, 0.0)
            sem_score = semantic_scores[i]
            
            final_score = (self.alpha * sem_score) + ((1 - self.alpha) * pr_score)
            
            results.append({
                'file': path,
                'score': final_score,
                'semantic': sem_score,
                'structural': pr_score
            })
            
        # Sort by final score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]


    def rank_for_feature(self, issue_embedding: np.ndarray, file_embeddings: Dict[str, np.ndarray], top_k: int = 10) -> List[Dict]:
        """Feature Request Strategy:
        Find files that are semantically similar to the requested feature
        AND have high structural centrality (likely extension points).
        """
        results = []
        paths = list(file_embeddings.keys())
        embeddings = np.array([file_embeddings[p] for p in paths])
        
        if len(embeddings) == 0:
            return []
        
        # Semantic similarity
        dot_products = np.dot(embeddings, issue_embedding)
        norms_files = np.linalg.norm(embeddings, axis=1)
        norm_issue = np.linalg.norm(issue_embedding)
        norms_files[norms_files == 0] = 1e-10
        semantic_scores = dot_products / (norms_files * norm_issue)
        
        # Normalize
        sem_max = np.max(semantic_scores)
        sem_min = np.min(semantic_scores)
        sem_rng = sem_max - sem_min if sem_max > sem_min else 1.0
        semantic_scores = (semantic_scores - sem_min) / sem_rng
        
        # For features, prioritize structural centrality MORE than bugs
        # Features often need to be added to core, well-connected modules
        alpha = 0.5  # Lower alpha = more weight on structure
        
        for i, path in enumerate(paths):
            pr_score = self._file_pr_scores.get(path, 0.0)
            sem_score = semantic_scores[i]
            final_score = (alpha * sem_score) + ((1 - alpha) * pr_score)
            
            results.append({
                'file': path,
                'score': final_score,
                'semantic': sem_score,
                'structural': pr_score
            })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def rank_for_docs(self, issue_embedding: np.ndarray, file_embeddings: Dict[str, np.ndarray], top_k: int = 10) -> List[Dict]:
        """
        Documentation Strategy:
        Prioritize semantic similarity to find code that matches the doc request.
        Documentation issues are usually about explaining existing code.
        """
        results = []
        paths = list(file_embeddings.keys())
        embeddings = np.array([file_embeddings[p] for p in paths])
        
        if len(embeddings) == 0:
            return []
        
        dot_products = np.dot(embeddings, issue_embedding)
        norms_files = np.linalg.norm(embeddings, axis=1)
        norm_issue = np.linalg.norm(issue_embedding)
        norms_files[norms_files == 0] = 1e-10
        semantic_scores = dot_products / (norms_files * norm_issue)
        
        sem_max = np.max(semantic_scores)
        sem_min = np.min(semantic_scores)
        sem_rng = sem_max - sem_min if sem_max > sem_min else 1.0
        semantic_scores = (semantic_scores - sem_min) / sem_rng
        
        # For docs, prioritize semantic similarity HEAVILY
        alpha = 0.9
        
        for i, path in enumerate(paths):
            pr_score = self._file_pr_scores.get(path, 0.0)
            sem_score = semantic_scores[i]
            final_score = (alpha * sem_score) + ((1 - alpha) * pr_score)
            
            results.append({
                'file': path,
                'score': final_score,
                'semantic': sem_score,
                'structural': pr_score
            })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def rank_for_performance(self, issue_embedding: np.ndarray, file_embeddings: Dict[str, np.ndarray], top_k: int = 10) -> List[Dict]:
        """
        Performance Strategy:
        Find files with HIGH structural centrality (bottlenecks, hot paths)
        AND semantic relevance to the performance issue.
        """
        results = []
        paths = list(file_embeddings.keys())
        embeddings = np.array([file_embeddings[p] for p in paths])
        
        if len(embeddings) == 0:
            return []
        
        dot_products = np.dot(embeddings, issue_embedding)
        norms_files = np.linalg.norm(embeddings, axis=1)
        norm_issue = np.linalg.norm(issue_embedding)
        norms_files[norms_files == 0] = 1e-10
        semantic_scores = dot_products / (norms_files * norm_issue)
        
        sem_max = np.max(semantic_scores)
        sem_min = np.min(semantic_scores)
        sem_rng = sem_max - sem_min if sem_max > sem_min else 1.0
        semantic_scores = (semantic_scores - sem_min) / sem_rng
        
        # For performance, prioritize structural centrality (hot paths)
        alpha = 0.4
        
        for i, path in enumerate(paths):
            pr_score = self._file_pr_scores.get(path, 0.0)
            sem_score = semantic_scores[i]
            final_score = (alpha * sem_score) + ((1 - alpha) * pr_score)
            
            results.append({
                'file': path,
                'score': final_score,
                'semantic': sem_score,
                'structural': pr_score
            })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]