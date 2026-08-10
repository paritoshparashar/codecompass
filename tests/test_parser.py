from codecompass.repo import RepoIngestionPipeline
from codecompass.parser import ASTCallGraphParser
import networkx as nx

if __name__ == "__main__":
    # Use a standard Python repo
    URL = "https://github.com/pallets/click"
    
    print("--- Phase 1: Repo Ingestion ---")
    repo_pipeline = RepoIngestionPipeline(repo_url=URL)
    files = repo_pipeline.execute()
    
    print("\n--- Phase 2: AST Parsing ---")
    parser = ASTCallGraphParser()
    graph = parser.build_graph(files)
    
    print("\n--- Graph Statistics ---")
    print(f"Total Nodes: {graph.number_of_nodes()}")
    print(f"Total Edges: {graph.number_of_edges()}")
    
    # Print the top 5 most central functions by PageRank to verify the graph works
    print("\nTop 5 Nodes by PageRank:")
    pagerank = nx.pagerank(graph)
    sorted_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
    
    for node_id, score in sorted_nodes[:5]:
        node_data = graph.nodes[node_id]
        print(f" - {node_data.get('name')} (Score: {score:.4f})")