import math
from pathlib import Path
import random
import unittest

from algoritmo import construir_arbol, ExpressionEvaluator, OPERACIONES
from biblioteca import altura_arbol
from datos import leer_csv
from diagnostico import diagnosticar
from genetico import generar_arbol, mutar
from metricas import calcular_metricas


class PruebasDiagnostico(unittest.TestCase):
    def test_media_y_recta_no_son_lo_mismo(self):
        d=diagnosticar([(1,1),(2,4),(3,9),(4,16)])
        self.assertEqual(d.media_y,7.5)
        self.assertEqual(d.mse_media,32.25)
        self.assertEqual(d.pendiente_recta,5)
        self.assertEqual(d.intercepto_recta,-5)
        self.assertEqual(d.mse_recta,1)
        self.assertIn('cercano a la media',d.explicar_ajuste(32.25))
        self.assertIn('peor',d.explicar_ajuste(40))

    def test_metricas_preservan_el_mismo_orden(self):
        ys=[1,4,9,16]
        d=diagnosticar(list(enumerate(ys)))
        m=calcular_metricas(ys,[7.5]*4)
        self.assertEqual(m['nmse'],1)
        self.assertEqual(m['r2'],0)
        self.assertAlmostEqual(m['rmse']**2,m['mse'])
        self.assertAlmostEqual(m['r2'],1-m['nmse'])
        self.assertIn('no están definidos',diagnosticar([(0,2),(1,2)]).explicar_ajuste(0))

    def test_candidato_compatible_con_csv_existentes(self):
        # Verifica una hipótesis explícita del diagnóstico; NO se usa en el motor.
        raiz=construir_arbol('11*cos(7.23*x^3)+6.87')
        self.assertEqual(altura_arbol(raiz),6)
        for archivo in ('funcion.csv','funcion_02.csv'):
            puntos=leer_csv(Path(__file__).parent/archivo)
            xs,ys=zip(*puntos)
            self.assertEqual(calcular_metricas(ys,ExpressionEvaluator().predecir(raiz,xs))['mse'],0)

    def test_potencias_enteras_se_pueden_generar_y_mutar(self):
        ops=tuple(o for o in OPERACIONES if o.simbolo=='^')
        azar=random.Random(42)
        enteras=0
        for _ in range(100):
            raiz=generar_arbol(azar,3,ops,forzar=True)
            if raiz.derecho.tipo=='numero' and float(raiz.derecho.valor).is_integer():
                enteras+=1
        self.assertGreater(enteras,70)
        raiz=construir_arbol('x^3')
        for _ in range(30):
            hijo=mutar(raiz,'terminal',azar,6,ops)
            self.assertTrue(float(hijo.derecho.valor).is_integer())


if __name__=='__main__':
    unittest.main()
