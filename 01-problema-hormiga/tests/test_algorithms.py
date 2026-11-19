import pytest
from src.app.graph.node import Node
from src.app.graph.graph import Graph
from src.app.algorithms.bfs import bfs
from src.app.algorithms.dfs import dfs

def create_simple_graph():
    # 3x3 grid without obstacles
    # (0,0) - (1,0) - (2,0)
    #   |       |       |
    # (0,1) - (1,1) - (2,1)
    #   |       |       |
    # (0,2) - (1,2) - (2,2)
    nodes = [[Node(c, r) for c in range(3)] for r in range(3)]
    g = Graph()
    for r in range(3):
        for c in range(3):
            g.add_node(nodes[r][c])
    
    for r in range(3):
        for c in range(3):
            if r + 1 < 3: g.add_edge(nodes[r][c], nodes[r+1][c])
            if c + 1 < 3: g.add_edge(nodes[r][c], nodes[r][c+1])
    return g, nodes

def test_bfs_path():
    g, nodes = create_simple_graph()
    start = nodes[0][0]
    goal = nodes[2][2]
    result = bfs(g, start, goal)
    assert len(result["path"]) == 5 # (0,0) -> (1,0) -> (2,0) -> (2,1) -> (2,2) or similar
    assert result["path"][0] == start
    assert result["path"][-1] == goal

def test_dfs_path():
    g, nodes = create_simple_graph()
    start = nodes[0][0]
    goal = nodes[2][2]
    result = dfs(g, start, goal)
    assert len(result["path"]) > 0
    assert result["path"][0] == start
    assert result["path"][-1] == goal

def test_no_path():
    g = Graph()
    n1 = Node(0,0)
    n2 = Node(1,1)
    g.add_node(n1)
    g.add_node(n2)
    # No edge between them
    result = bfs(g, n1, n2)
    assert result["path"] == []
