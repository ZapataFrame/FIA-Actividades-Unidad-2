"""Regresión para la transcripción de la imagen dirigida con pesos negativos."""
import unittest
from pathlib import Path
from collections import Counter
from math import inf
from graph_data import load_graph
from algorithms import search
import test_ui

class DirectedGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=load_graph(Path(__file__).parent/'graphs/directed-negative.json')

    def test_transcription_counts_directions_and_parallel_arcs(self):
        model=self.model
        arcs=Counter((model.nodes[e.source],model.nodes[e.target],e['weight']) for e in model.graph.es)
        self.assertTrue(model.graph.is_directed())
        self.assertEqual((len(model.nodes),model.graph.ecount()),(30,63))
        self.assertEqual(sum(e['weight']<0 for e in model.graph.es),8)
        samples=[(21,29,3),(11,21,-2),(11,24,-7),(6,7,10),(7,1,20),
                 (15,6,3),(1,0,2),(0,15,8),(2,3,9),(17,2,5),(69,5,3),
                 (16,17,7),(666,12,7),(13,12,9),(13,16,3),(666,13,-777)]
        for a,b,w in samples:
            self.assertEqual(arcs[a,b,w],1)
            self.assertFalse(any(v==a for v,_,_ in model.adjacency[b]),(a,b))
        self.assertEqual(sorted(w for v,w,_ in model.adjacency[12] if v==16),[3,16])

    def test_all_pairs_agree_and_no_negative_cycle(self):
        model=self.model
        nodes=model.nodes
        costs={(u,v):0 if u==v else inf for u in nodes for v in nodes}
        for u in nodes:
            for v,w,_ in model.adjacency[u]: costs[u,v]=min(costs[u,v],w)
        for k in nodes:
            for u in nodes:
                for v in nodes: costs[u,v]=min(costs[u,v],costs[u,k]+costs[k,v])
        self.assertTrue(all(costs[n,n]==0 for n in nodes))
        floyd=search(model,29,13,'Floyd–Warshall')[-1]
        for i,u in enumerate(nodes):
            bellman=search(model,u,13,'Bellman–Ford')[-1]
            self.assertFalse(bellman.negative_nodes)
            for j,v in enumerate(nodes):
                self.assertEqual(floyd.matrix.distances[i][j],costs[u,v],(u,v))
                self.assertEqual(bellman.distances[v],costs[u,v],(u,v))

    def test_expected_routes_and_negative_algorithm_guards(self):
        for algorithm in ('Bellman–Ford','Floyd–Warshall'):
            result=search(self.model,29,13,algorithm)[-1]
            self.assertEqual(result.distances[13],-750)
            self.assertEqual(result.path_nodes,(29,7,14,4,18,666,13))
            self.assertEqual(search(self.model,666,13,algorithm)[-1].distances[13],-777)
            self.assertEqual(search(self.model,13,666,algorithm)[-1].distances[666],inf)
        for algorithm in ('Dijkstra','A*'):
            with self.assertRaises(ValueError): search(self.model,29,13,algorithm)

class DirectedGraphUI(unittest.TestCase):
    setUpClass=classmethod(test_ui.UITests.setUpClass.__func__)
    setUp=test_ui.UITests.setUp
    tearDown=test_ui.UITests.tearDown

    def test_three_graph_choices_and_algorithm_restrictions(self):
        w=self.window
        self.assertEqual(w.graph_choice.count(),3)
        self.assertTrue(w.graph_choice.model().item(2).isEnabled())
        w.graph_choice.setCurrentIndex(2)
        self.assertTrue(w.model.graph.is_directed())
        self.assertEqual(w.algorithm.currentText(),'Bellman–Ford')
        w.source.setCurrentText('29')
        w.target.setCurrentText('13')
        w.navigate(len(w.steps)-1)
        self.assertEqual(w.canvas.step.distances[13],-750)
        for name in ('Dijkstra','A*'):
            index=w.algorithm.findText(name)
            self.assertFalse(w.algorithm.model().item(index).isEnabled())
        w.graph_choice.setCurrentIndex(1)
        self.assertFalse(w.model.graph.is_directed())
        w.graph_choice.setCurrentIndex(0)
        self.assertFalse(w.model.has_negative_weights)
        self.assertTrue(w.algorithm.model().item(0).isEnabled())

if __name__=='__main__': unittest.main()
