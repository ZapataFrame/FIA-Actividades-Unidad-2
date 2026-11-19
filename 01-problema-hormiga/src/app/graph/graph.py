from typing import List, Dict
from src.app.graph.node import Node
from src.app.utils.constants import GRID_ROWS, GRID_COLS, TYPE_OBSTACLE

class Graph:
    def __init__(self):
        self.nodes = set()
        self.edges: Dict[Node, List[Node]] = {}

    def add_node(self, node: Node):
        self.nodes.add(node)
        if node not in self.edges:
            self.edges[node] = []

    def add_edge(self, node1: Node, node2: Node):
        if node1 not in self.nodes or node2 not in self.nodes:
            return
        
        if node2 not in self.edges[node1]:
            self.edges[node1].append(node2)
        if node1 not in self.edges[node2]:
            self.edges[node2].append(node1)

    def get_neighbors(self, node: Node) -> List[Node]:
        if node not in self.edges:
            return []
        
        return [n for n in self.edges[node] if n.type != TYPE_OBSTACLE]

    @staticmethod
    def convert_grid_to_graph(grid_data) -> 'Graph':
        graph = Graph()
        
        rows = len(grid_data)
        cols = len(grid_data[0]) if rows > 0 else 0

        # 1. Add all valid nodes
        for r in range(rows):
            for c in range(cols):
                node = grid_data[r][c]
                if node.type != TYPE_OBSTACLE:
                    graph.add_node(node)

        # 2. Create edges between adjacent non-obstacle nodes
        for r in range(rows):
            for c in range(cols):
                current_node = grid_data[r][c]
                if current_node.type == TYPE_OBSTACLE:
                    continue

                # Check 4 directions: Right and Down (others handled by symmetry)
                for dr, dc in [(0, 1), (1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        neighbor_node = grid_data[nr][nc]
                        if neighbor_node.type != TYPE_OBSTACLE:
                            graph.add_edge(current_node, neighbor_node)
                            
        return graph
