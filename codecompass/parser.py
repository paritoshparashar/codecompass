import ast
import networkx as nx
from pathlib import Path
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

class ASTCallGraphParser:
    """
    Parses Python files using the AST module to build a NetworkX Directed Graph.
    Nodes are functions, async functions, and classes. 
    Edges represent function calls, resolved via a heuristic registry for cross-file calls.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        # Maps simple function names to a list of their fully qualified node IDs
        # Used for resolving cross-file calls heuristically
        self._func_registry: Dict[str, List[str]] = {}

    def _get_node_id(self, file_path: str, name: str) -> str:
        """Generates a unique node ID based on file and name."""
        return f"{file_path}::{name}"

    def _parse_file(self, file_path: Path, base_dir: Path) -> Tuple[int, int]:
        """
        Parses a single Python file and adds its functions and calls to the graph.
        Returns (nodes_added, edges_added).
        """
        nodes_added = 0
        edges_added = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            tree = ast.parse(code, filename=str(file_path))
        except Exception as e:
            logger.warning(f"Failed to parse {file_path.name}: {e}")
            return 0, 0

        try:
            str_path = str(file_path.relative_to(base_dir))
        except ValueError:
            str_path = str(file_path) # Fallback

        # First pass: Collect all function/class definitions and add them as nodes
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                node_id = self._get_node_id(str_path, node.name)
                self.graph.add_node(
                    node_id, 
                    name=node.name, 
                    file=str_path, 
                    type=type(node).__name__
                )
                
                if node.name not in self._func_registry:
                    self._func_registry[node.name] = []
                self._func_registry[node.name].append(node_id)
                nodes_added += 1

        # Second pass: Collect calls and map them to the nearest enclosing function
        class CallVisitor(ast.NodeVisitor):
            def __init__(self, parser: 'ASTCallGraphParser'):
                self.parser = parser
                self.current_scope = None

            def visit_FunctionDef(self, node):
                node_id = self.parser._get_node_id(str_path, node.name)
                old_scope = self.current_scope
                self.current_scope = node_id
                self.generic_visit(node)
                self.current_scope = old_scope
                
            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_ClassDef(self, node):
                node_id = self.parser._get_node_id(str_path, node.name)
                old_scope = self.current_scope
                self.current_scope = node_id
                self.generic_visit(node)
                self.current_scope = old_scope

            def visit_Call(self, node):
                nonlocal edges_added
                
                if self.current_scope is not None:
                    # Try to extract the function name being called
                    func_name = None
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr
                    
                    if func_name:
                        target_node_id = None
                        
                        # 1. Check if it's defined in the same file (highest priority)
                        local_node_id = self.parser._get_node_id(str_path, func_name)
                        if self.parser.graph.has_node(local_node_id):
                            target_node_id = local_node_id
                        # 2. Check registry for other files (heuristic cross-file resolution)
                        elif func_name in self.parser._func_registry:
                            target_node_id = self.parser._func_registry[func_name][0]

                        if target_node_id and target_node_id != self.current_scope:
                            if self.parser.graph.has_edge(self.current_scope, target_node_id):
                                self.parser.graph[self.current_scope][target_node_id]['weight'] += 1
                            else:
                                self.parser.graph.add_edge(self.current_scope, target_node_id, weight=1)
                            edges_added += 1
                
                self.generic_visit(node)

        visitor = CallVisitor(self)
        visitor.visit(tree)
        
        return nodes_added, edges_added

    def build_graph(self, files: List[Path], base_dir: Path) -> nx.DiGraph:
        """
        Pipeline Step: Iterates through all files, parses them, and builds the complete call graph.
        """
        logger.info(f"Starting AST parsing for {len(files)} files...")
        
        total_nodes = 0
        total_edges = 0
        
        for f in files:
            n, e = self._parse_file(f, base_dir)
            total_nodes += n
            total_edges += e
            
        logger.info(f"Graph construction complete. Nodes: {self.graph.number_of_nodes()}, Edges: {self.graph.number_of_edges()}")
        return self.graph