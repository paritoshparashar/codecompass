from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import logging
from codecompass.classifier import IssueClassifier
from codecompass.cache import load_cache, save_cache, clear_cache
from codecompass.viz import GraphVisualizer
from codecompass.explainer import LLMExplainer
from codecompass.repo import RepoIngestionPipeline
from codecompass.parser import ASTCallGraphParser
from codecompass.embedder import TextEmbedder
from codecompass.ranker import CodeRanker

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="CodeCompass API")

# --- Pydantic Schemas ---

class AnalyzeRequest(BaseModel):
    repo_url: str
    issue_text: str

class FileRank(BaseModel):
    file: str
    score: float
    semantic: float
    structural: float

class AnalyzeResponse(BaseModel):
    issue_category: str = "unknown"
    ranked_files: List[FileRank]
    graph_html: str = ""



# --- Startup Initialization ---
logger.info("Initializing CodeCompass Engine...")
embedder = TextEmbedder()
explainer = LLMExplainer()
visualizer = GraphVisualizer()
classifier = IssueClassifier()
logger.info("Engine ready.")

def get_repo_name(url: str) -> str:
    name = url.rstrip('/').split('/')[-1]
    return name[:-4] if name.endswith('.git') else name


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_codebase(request: AnalyzeRequest):
    try:
        repo_name = get_repo_name(request.repo_url)

        issue_category = classifier.classify(request.issue_text)
        logger.info(f"Issue classified as: {issue_category}")
  
        
        # 1. Check Cache First
        graph, file_embeddings = load_cache(repo_name)
        
        if graph is None or file_embeddings is None:
            logger.info("Cache miss. Running full pipeline...")
            # Run Pipeline
            repo = RepoIngestionPipeline(repo_url=request.repo_url)
            files = repo.execute()
            
            parser = ASTCallGraphParser()
            # Pass the base directory for relative path calculation
            graph = parser.build_graph(files, repo._local_path)
            
            file_embeddings = {}
            for f in files:
                # Store embeddings using relative path keys
                rel_path = str(f.relative_to(repo._local_path))
                file_embeddings[rel_path] = embedder.embed_file(f)
                
            # Save to Cache
            save_cache(repo_name, graph, file_embeddings)
        
        # 2. Process Issue (Always runs, even if cache was used)
        issue_embedding = embedder.embed_texts([request.issue_text])[0]
        
        # 3. Rank
        ranker = CodeRanker(graph)
        if issue_category == "bug":
            results = ranker.rank_files(issue_embedding, file_embeddings, top_k=10)
        elif issue_category == "feature":
            results = ranker.rank_for_feature(issue_embedding, file_embeddings, top_k=10)
        elif issue_category == "documentation":
            results = ranker.rank_for_docs(issue_embedding, file_embeddings, top_k=10)
        elif issue_category == "performance":
            results = ranker.rank_for_performance(issue_embedding, file_embeddings, top_k=10)
        else:
            results = ranker.rank_files(issue_embedding, file_embeddings, top_k=10)
        
        
        # 4. Explain & Visualize (Top 3)
        for res in results[:3]:
            file_path = res['file']
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    snippet = "".join(f.readlines()[:50])
            except Exception:
                snippet = "Could not read file."
            res['explanation'] = explainer.generate_explanation(request.issue_text, file_path, snippet)
            
        top_files = [res['file'] for res in results[:3]]
        graph_html = visualizer.generate_html(graph, top_files)
        
        return {
            "issue_category": issue_category,
            "ranked_files": results,
            "graph_html": graph_html
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))