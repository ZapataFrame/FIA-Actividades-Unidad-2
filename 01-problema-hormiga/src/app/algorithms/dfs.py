from typing import List, Dict
from src.app.graph.node import Node
from src.app.graph.graph import Graph

def dfs(graph: Graph, start: Node, goal: Node) -> Dict:
    """
    Depth-First Search implementation.
    Returns a dictionary containing the list of visited nodes and the final path.
    """
    if start == goal:
        return {"visited": [start], "path": [start]}

    visited: List[Node] = []
    stack = [start]
    parent = {start: None}
    visited_set = set()

    while stack:
        current = stack.pop()
        
        if current in visited_set:
            continue
            
        visited.append(current)
        visited_set.add(current)

        if current == goal:
            path = []
            while current:
                path.append(current)
                current = parent[current]
            return {"visited": visited, "path": path[::-1]}

        for neighbor in graph.get_neighbors(current):
            if neighbor not in visited_set:
                parent[neighbor] = current
                stack.append(neighbor)

    return {"visited": visited, "path": []}
