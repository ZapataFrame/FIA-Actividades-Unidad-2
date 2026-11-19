from collections import deque
from typing import List, Dict, Optional, Set
from src.app.graph.node import Node
from src.app.graph.graph import Graph

def bfs(graph: Graph, start: Node, goal: Node) -> Dict:
    """
    Breadth-First Search implementation.
    Returns a dictionary containing the list of visited nodes and the final path.
    """
    if start == goal:
        return {"visited": [start], "path": [start]}

    visited: List[Node] = []
    queue = deque([start])
    parent = {start: None}
    
    visited_set: Set[Node] = {start}

    while queue:
        current = queue.popleft()
        visited.append(current)

        if current == goal:
            # Reconstruct path
            path = []
            while current:
                path.append(current)
                current = parent[current]
            return {"visited": visited, "path": path[::-1]}

        for neighbor in graph.get_neighbors(current):
            if neighbor not in visited_set:
                visited_set.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)

    return {"visited": visited, "path": []}
