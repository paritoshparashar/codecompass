from codecompass.repo import RepoIngestionPipeline
from codecompass.parser import ASTCallGraphParser
from codecompass.embedder import TextEmbedder
from codecompass.ranker import CodeRanker

def main():
    URL = "https://github.com/pallets/click"
    
    # 1. Ingest
    repo = RepoIngestionPipeline(repo_url=URL)
    files = repo.execute()
    
    # 2. Parse Graph
    parser = ASTCallGraphParser()
    graph = parser.build_graph(files)
    
    # 3. Embed
    embedder = TextEmbedder()
    file_embeddings = {}
    for f in files:
        file_embeddings[str(f)] = embedder.embed_file(f)
        
    # 4. Rank
    ranker = CodeRanker(graph)
    
    # Simulate an issue text
    issue_text = "How do I add a default value to an argument?"
    issue_embedding = embedder.embed_texts([issue_text])[0]
    
    print("\n--- Ranking Results ---")
    top_files = ranker.rank_files(issue_embedding, file_embeddings, top_k=5)
    
    for r in top_files:
        # Just print the file name, not the whole path
        print(f"File: {r['file'].split('/')[-1]}")
        print(f"  Score: {r['score']:.4f} (Semantic: {r['semantic']:.4f}, Structural: {r['structural']:.4f})")

if __name__ == "__main__":
    main()