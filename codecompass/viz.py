import networkx as nx
from pyvis.network import Network
import logging

logger = logging.getLogger(__name__)

class GraphVisualizer:
    """
    Generates an interactive PyVis HTML network graph from the NetworkX DiGraph.
    Highlights the top-ranked files in red for easy visual identification.
    """

    def __init__(self):
        pass

    def generate_html(self, graph: nx.DiGraph, top_files: list[str]) -> str:
        """
        Generates an interactive PyVis HTML string.
        """
        # Initialize PyVis network
        net = Network(height="600px", width="100%", directed=True, notebook=False)
        net.barnes_hut(gravity=-20000, central_gravity=0.3, spring_length=200, spring_strength=0.05, damping=0.09)

        # 1. Identify nodes belonging to the top files
        top_nodes = set()
        for file_path in top_files:
            for node in graph.nodes():
                if node.startswith(file_path + "::"):
                    top_nodes.add(node)
                    
        # 2. Get immediate neighbors for context (callers and callees)
        context_nodes = set()
        for node in list(top_nodes):
            context_nodes.update(graph.successors(node))
            context_nodes.update(graph.predecessors(node))
            
        # 3. Combine and limit to 150 nodes to prevent browser/UI lag
        all_nodes = top_nodes.union(context_nodes)
        if len(all_nodes) > 150:
            context_nodes = set(list(context_nodes)[:150 - len(top_nodes)])
            all_nodes = top_nodes.union(context_nodes)

        subgraph = graph.subgraph(all_nodes).copy()

        # 4. Add nodes and edges to PyVis
        for node, attrs in subgraph.nodes(data=True):
            file_path = node.split("::")[0]
            func_name = attrs.get('name', node.split("::")[-1])
            
            is_top = file_path in top_files
            # Red for top 3 files, Blue for context
            color = "#ff4b4b" if is_top else "#97c2fc" 
            size = 35 if is_top else 15
            
            title = f"File: {file_path.split('/')[-1]}\nFunction: {func_name}"
            net.add_node(node, label=func_name, title=title, color=color, size=size, font={'size': 10})
            
        for source, target, attrs in subgraph.edges(data=True):
            net.add_edge(source, target, weight=attrs.get('weight', 1), color={'color': '#848484', 'opacity': 0.5})

        # Return the HTML string directly (avoids disk I/O)
        return net.generate_html()