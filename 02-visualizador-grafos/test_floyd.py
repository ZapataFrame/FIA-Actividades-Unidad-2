import unittest
from math import inf
from unittest.mock import patch
from PyQt6.QtCore import QRectF
from graph_data import build_graph
from algorithms import search
from rendering import render_slide, matrix_geometry, MATRIX_PIVOT, MATRIX_COLUMN, MATRIX_CHANGED, floyd_geometry
import test_ui


class FloydTests(unittest.TestCase):
    def test_example_first_iterations_by_column(self):
        model=build_graph([(0,1,6),(0,3,5),(0,6,8),(1,2,7),(1,3,1),
                           (2,3,4),(2,4,11),(2,5,2),(3,4,6),(3,7,3),
                           (4,5,2),(4,6,10),(5,7,4),(6,7,2)],
                          {i:(i,0) for i in range(8)})
        steps=search(model,0,7,'Floyd–Warshall')
        self.assertEqual(len(steps),10)
        first=steps[1].matrix
        self.assertEqual(first.distances[1][6],14)
        self.assertEqual(first.distances[3][6],13)
        self.assertEqual(first.routes[1][6],0)
        second=steps[2].matrix
        self.assertEqual(second.distances[0][2],13)
        self.assertEqual(second.distances[2][6],21)
        self.assertEqual(second.routes[0][2],1)
        third=steps[3].matrix
        self.assertEqual(third.distances[0][4],24)
        self.assertEqual(third.distances[0][5],15)
        self.assertEqual(third.distances[3][5],6)
        self.assertEqual(third.distances[6][5],23)
        for step in steps[1:-1]:
            m=step.matrix
            for c in m.changes:
                self.assertEqual(c.left+c.right,c.new)
                self.assertLess(c.new,c.old)
                self.assertEqual(m.distances[c.row][c.column],c.new)
                self.assertEqual(m.routes[c.row][c.column],m.nodes[m.pivot])
            self.assertEqual(step.current,m.nodes[m.pivot])
            self.assertEqual([c.column for c in m.changes],sorted(c.column for c in m.changes))
        self.assertEqual(steps[0].matrix.distances[1][6],inf)
        self.assertIsNone(steps[0].matrix.routes[1][6])

    def test_all_900_distances_and_path(self):
        model=build_graph()
        steps=search(model,666,13,'Floyd–Warshall')
        final=steps[-1]
        self.assertEqual(len(steps),32)
        for i,source in enumerate(model.nodes):
            for j,target in enumerate(model.nodes):
                self.assertEqual(final.matrix.distances[i][j],search(model,source,target)[-1].distances[target])
        self.assertEqual(final.distances[13],13)
        self.assertEqual(final.path_nodes,(666,12,16,13))
        self.assertEqual(sum(model.graph.es[e]['weight'] for e in final.path_edges),13)
        i,j=model.nodes.index(12),model.nodes.index(16)
        self.assertEqual(steps[0].matrix.distances[i][j],3)
        with self.assertRaises(TypeError): final.matrix.distances[0][0]=1

    def test_negative_edges_cycles_disconnected_and_identity(self):
        model=build_graph([(0,1,4),(1,2,-3),(0,2,5)],{i:(i,0) for i in range(4)},True)
        final=search(model,0,2,'Floyd–Warshall')[-1]
        self.assertEqual(final.distances[2],1)
        self.assertEqual(final.path_nodes,(0,1,2))
        self.assertEqual(final.matrix.distances[3][0],inf)
        self.assertIsNone(final.matrix.routes[3][0])
        self.assertEqual(search(model,3,3,'Floyd–Warshall')[-1].path_nodes,(3,))
        model=build_graph([(0,1,1),(1,2,-2),(2,1,1),(2,3,3)],{i:(i,0) for i in range(5)},True)
        final=search(model,0,3,'Floyd–Warshall')[-1]
        self.assertEqual(final.distances[3],-inf)
        self.assertEqual(final.path_nodes,())
        self.assertEqual(final.matrix.distances[4][4],0)
        self.assertEqual(final.matrix.distances[4][3],inf)


class FloydUI(unittest.TestCase):
    setUpClass = classmethod(test_ui.UITests.setUpClass.__func__)
    setUp = test_ui.UITests.setUp
    tearDown = test_ui.UITests.tearDown
    def test_three_panels_in_one_row_in_ui_and_export(self):
        w=self.window
        w.algorithm.setCurrentText('Floyd–Warshall')
        w.navigate(2)
        self.app.processEvents()
        self.assertFalse(w.table.isVisible())
        self.assertEqual(set(w.canvas.points),set(w.model.nodes))
        ui_graph, ui_matrices = floyd_geometry(QRectF(w.canvas.rect()).adjusted(8,8,-8,-8))
        self.assertTrue(all(ui_graph.contains(point) for point in w.canvas.points.values()))
        ui_grids,_ = matrix_geometry(ui_matrices,len(w.model.nodes))
        self.assertLess(ui_grids[0].right(),ui_grids[1].left())
        self.assertAlmostEqual(ui_graph.top(),ui_grids[0].top())
        self.assertAlmostEqual(ui_graph.height(),ui_grids[0].height())
        self.assertGreater(ui_grids[0].left(),ui_graph.right())
        self.assertIn('k=',w.stats.text())
        with patch('rendering.draw_graph', wraps=__import__('rendering').draw_graph) as draw:
            image=render_slide(w.model,w.steps[w.index],29,13,'Floyd–Warshall','Original',w.index,len(w.steps))
        draw.assert_called_once()
        self.assertEqual((image.width(),image.height()),(5600,2100))
        self.assertEqual(MATRIX_COLUMN,MATRIX_PIVOT)
        self.assertNotEqual(MATRIX_CHANGED,MATRIX_PIVOT)
        # Comprueba el relleno real lejos del texto, en ambas matrices.
        m=w.steps[w.index].matrix
        changed=next(c for c in m.changes if c.row!=m.pivot and c.column!=m.pivot)
        graph_rect, matrix_rect = floyd_geometry(QRectF(32,122,2736,780))
        grids,cell=matrix_geometry(matrix_rect,len(m.nodes))
        for grid in grids:
            x=round(2*(grid.left()+(changed.column+1)*cell+3))
            y=round(2*(grid.top()+(changed.row+1)*cell+3))
            self.assertEqual(image.pixelColor(x,y).name(),MATRIX_CHANGED)
        for grid in grids:
            self.assertTrue(matrix_rect.contains(grid))
            self.assertGreater(grid.left(),graph_rect.right())
        self.assertGreater(cell,17)
        self.assertLess(grids[0].right(),grids[1].left())
        self.assertAlmostEqual(grids[0].top(),grids[1].top())
        self.assertAlmostEqual(graph_rect.height(),grids[0].height())
        self.assertAlmostEqual(graph_rect.top(),grids[0].top())
        self.assertEqual(w.canvas.minimumHeight(),650)
        self.assertGreater(w.canvas_scroll.horizontalScrollBar().maximum(),0)
        self.assertTrue(image.save(str(self.root/'floyd.png')))
        w.algorithm.setCurrentText('Dijkstra')
        self.app.processEvents()
        self.assertTrue(w.table.isVisible())
        self.assertEqual(w.canvas.minimumHeight(),420)
        self.assertIsNone(w.steps[0].matrix)

if __name__=='__main__': unittest.main()
