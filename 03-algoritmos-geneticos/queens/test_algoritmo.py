"""Comprueba la métrica, los operadores de permutaciones y la parada."""

from dataclasses import replace
from itertools import combinations, permutations
import random
import unittest
from unittest.mock import Mock

from algoritmo import (
    Parametros, cruce_orden, evaluar, evolucionar, inicializar_poblacion,
    mutar, obtener_colisiones, reproducir, seleccionar, validar_parametros,
)


class PruebasNReinas(unittest.TestCase):
    def test_colisiones_pares_sin_duplicarlos(self):
        self.assertEqual(obtener_colisiones((2, 4, 1, 3)), ())
        self.assertEqual(len(obtener_colisiones((1, 2, 3, 4))), 6)
        self.assertEqual(len(obtener_colisiones(tuple(range(1, 9)))), 28)
        self.assertEqual(obtener_colisiones((1,)), ())
        self.assertEqual(obtener_colisiones((1, 2)), ((0, 1),))

    def test_tableros_cuatro_reinas_solo_dos_soluciones(self):
        soluciones = {genes for genes in permutations(range(1, 5)) if not obtener_colisiones(genes)}
        self.assertEqual(soluciones, {(2, 4, 1, 3), (3, 1, 4, 2)})

    def test_evaluar_rechaza_individuos_invalidos(self):
        for genes in ((1, 1, 3), (0, 1, 2), (1, 2, 4), (), (1.0, 2, 3)):
            with self.assertRaises(ValueError):
                evaluar([genes])

    def test_inicializacion_permutaciones(self):
        p = Parametros(n=12, tamano_poblacion=17)
        poblacion = inicializar_poblacion(p, random.Random(42))
        self.assertEqual(len(poblacion), 17)
        self.assertTrue(all(sorted(genes) == list(range(1, 13)) for genes in poblacion))

    def test_ox_ejemplo_del_libro(self):
        padre = (1, 3, 6, 4, 2, 5, 8, 7)
        madre = (2, 7, 8, 3, 1, 5, 4, 6)
        self.assertEqual(cruce_orden(padre, madre, 3, 6), (8, 3, 1, 4, 2, 5, 6, 7))
        self.assertEqual(cruce_orden(madre, padre, 3, 6), (6, 4, 2, 3, 1, 5, 8, 7))

    def test_ox_preserva_todas_las_permutaciones_pequenas(self):
        padres = list(permutations(range(1, 5)))
        # 5760 cruces: todos los padres y cortes posibles para n=4.
        for padre in padres:
            for madre in padres:
                for inicio, fin in combinations(range(5), 2):
                    hijo = cruce_orden(padre, madre, inicio, fin)
                    self.assertEqual(sorted(hijo), [1, 2, 3, 4])
                    self.assertEqual(hijo[inicio:fin], padre[inicio:fin])

    def test_intercambio_preserva_permutacion_y_no_modifica_padres(self):
        poblacion = [(1, 2, 3, 4)]
        self.assertEqual(mutar(poblacion, 0, random.Random(1)), poblacion)
        azar = Mock()
        azar.random.return_value = 0.1
        azar.sample.return_value = [0, 3]
        self.assertEqual(mutar(poblacion, 1, azar), [(4, 2, 3, 1)])
        self.assertEqual(poblacion, [(1, 2, 3, 4)])
        self.assertEqual(mutar([(1,)], 1, azar), [(1,)])

    def test_ruleta_favorece_menos_conflictos(self):
        poblacion = evaluar([(2, 4, 1, 3), (1, 2, 3, 4)])
        azar = Mock()
        azar.choices.return_value = [poblacion[0], poblacion[0]]
        self.assertEqual(seleccionar(poblacion, 2, azar), [(2, 4, 1, 3)] * 2)
        pesos = azar.choices.call_args.kwargs['weights']
        self.assertEqual(pesos, [1, 1 / 7])

    def test_reproduccion_impar_y_cruce_desactivado(self):
        padres = [(1, 2, 3, 4), (4, 3, 2, 1), (2, 4, 1, 3)]
        p = Parametros(n=4, prob_cruce=0)
        self.assertEqual(reproducir(padres, p, random.Random(1)), padres)
        hijos = reproducir(padres, replace(p, prob_cruce=1), random.Random(1))
        self.assertEqual(len(hijos), 3)
        self.assertEqual(hijos[-1], padres[-1])
        self.assertTrue(all(sorted(hijo) == [1, 2, 3, 4] for hijo in hijos))

    def test_ciclo_reproducible_elitismo_y_solucion(self):
        p = Parametros(tamano_poblacion=15, generaciones=100, elites=1)
        historial = list(evolucionar(p))
        self.assertEqual(historial, list(evolucionar(p)))
        self.assertTrue(all(len(g.poblacion) == 15 for g in historial))
        for anterior, actual in zip(historial, historial[1:]):
            self.assertIn(anterior.mejor, actual.poblacion)
            self.assertLessEqual(actual.mejor.colisiones, anterior.mejor.colisiones)
        self.assertTrue(all(g.mejor.colisiones > 0 for g in historial[:-1]))
        if historial[-1].mejor.colisiones == 0:
            self.assertEqual(obtener_colisiones(historial[-1].mejor.genes), ())
        else:
            self.assertEqual(historial[-1].numero, 100)
        defecto = list(evolucionar())[-1]
        self.assertEqual(defecto.mejor.colisiones, 0)

    def test_uno_sin_solucion_y_limite_cero(self):
        self.assertEqual(len(list(evolucionar(Parametros(n=1)))), 1)
        for n in (2, 3):
            for elites in (0, 14):
                historial = list(evolucionar(Parametros(n=n, tamano_poblacion=15, generaciones=5, elites=elites)))
                self.assertEqual(len(historial), 6)
                self.assertGreater(historial[-1].mejor.colisiones, 0)
                self.assertTrue(all(len(g.poblacion) == 15 for g in historial))
        self.assertEqual(len(list(evolucionar(Parametros(generaciones=0)))), 1)

    def test_parametros_invalidos(self):
        for cambio in ({"n": 0}, {"n": 4.5}, {"elites": 80}, {"elites": -1},
                       {"prob_cruce": 2}, {"prob_mutacion": float('nan')}, {"generaciones": -1},
                       {"tamano_poblacion": 1}):
            with self.assertRaises(ValueError):
                validar_parametros(replace(Parametros(), **cambio))


if __name__ == '__main__':
    unittest.main()
