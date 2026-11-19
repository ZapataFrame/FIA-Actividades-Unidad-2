import pytest
from src.app.graph.node import Node
from src.app.graph.graph import Graph
from src.app.utils.constants import TYPE_OBSTACLE

def test_graph_add_node():
    g = Graph()
    n = Node(0, 0)
    g.add_node(n)
    assert n in g.nodes

def test_graph_edges():
    g = Graph()
    n1 = Node(0, 0)
    n2 = Node(0, 1)
    g.add_node(n1)
    g.add_node(n2)
    g.add_edge(n1, n2)
    assert n2 in g.edges[n1]
    assert n1 in g.edges[n2]

def test_get_neighbors_obstacle():
    g = Graph()
    n1 = Node(0, 0)
    n2 = Node(0, 1, node_type=TYPE_OBSTACLE)
    g.add_node(n1)
    g.add_node(n2)
    g.add_edge(n1, n2)
    
    neighbors = g.get_neighbors(n1)
    assert n2 not in neighbors

def test_convert_grid_to_graph():
    # 2x2 grid
    # [empty, empty]
    # [empty, obstacle]
    grid = [
        [Node(0,0), Node(1,0)],
        [Node(0,1), Node(1,1, node_type=TYPE_OBSTACLE)]
    ]
    
    graph = Graph.convert_grid_to_graph(grid)
    assert len(graph.nodes) == 3
    assert len(graph.edges[grid[0][0]]) == 2 # connected to (1,0) and (0,1)
    assert grid[1][1] not in graph.nodes
