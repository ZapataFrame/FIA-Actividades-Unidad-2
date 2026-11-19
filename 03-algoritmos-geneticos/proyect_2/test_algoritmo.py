"""Propiedades del algoritmo real y comprobaciones numéricas de sus cruces."""

from dataclasses import replace
import random
import unittest
from unittest.mock import Mock

from algoritmo import (
    METODOS_CRUCE, PROBLEMAS, Individuo, Parametros, calcular_pesos,
    cruce_aritmetico, cruce_sbx, cruce_un_punto, cruce_uniforme,
    evolucionar, funcion_rastrigin, inicializar_poblacion, mutar,
    reproducir, validar_parametros,
)


class PruebasAlgoritmoReal(unittest.TestCase):
    def test_inicializacion_y_evaluacion_directa(self):
        problema = PROBLEMAS[3]
        parametros = Parametros(dimensiones=10)
        poblacion = inicializar_poblacion(problema, parametros, random.Random(42))
        self.assertEqual(len(poblacion), parametros.tamano_poblacion)
        self.assertTrue(all(len(genes) == 10 for genes in poblacion))
        self.assertTrue(all(-5.12 <= x <= 5.12 for genes in poblacion for x in genes))
        self.assertEqual(funcion_rastrigin((0.0,) * 10), 0)
        self.assertEqual(funcion_rastrigin((1.0, 1.0)), 2)
        inicial = next(evolucionar(problema, parametros))
        for individuo in inicial.poblacion:
            self.assertEqual(individuo.objetivo, problema.funcion(individuo.genes))
            self.assertEqual(individuo.genes, individuo.valores)

    def test_cruce_un_punto_entre_genes(self):
        padre, madre = (1.0, 2.0, 3.0), (4.0, 5.0, 6.0)
        azar = Mock()
        azar.randrange.return_value = 2
        self.assertEqual(cruce_un_punto(padre, madre, azar), ((1.0, 2.0, 6.0), (4.0, 5.0, 3.0)))
        self.assertEqual(cruce_un_punto((1.0,), (4.0,), azar), ((1.0,), (4.0,)))

    def test_cruce_uniforme_complementario(self):
        padre, madre = (1.0, 2.0), (3.0, 4.0)
        self.assertEqual(cruce_uniforme(padre, madre, 0, random.Random(1)), (padre, madre))
        self.assertEqual(cruce_uniforme(padre, madre, 1, random.Random(1)), (madre, padre))
        azar = Mock()
        azar.random.side_effect = [0.2, 0.8]
        self.assertEqual(cruce_uniforme(padre, madre, 0.5, azar), ((3.0, 2.0), (1.0, 4.0)))

    def test_aritmetico_pesos_y_punto_medio(self):
        padre, madre = (2.0, 10.0), (6.0, 2.0)
        self.assertEqual(cruce_aritmetico(padre, madre, 0.25), ((5.0, 4.0), (3.0, 8.0)))
        self.assertEqual(cruce_aritmetico(padre, madre, 0.5), ((4.0, 6.0), (4.0, 6.0)))
        self.assertEqual(cruce_aritmetico(padre, madre, 1), (padre, madre))

    def test_sbx_dos_ramas_y_limites(self):
        azar = Mock()
        problema = PROBLEMAS[0]  # [0, 32]
        # eta=1, u=0.125 => beta=0.5; u=0.875 => beta=2.
        azar.random.return_value = 0.125
        self.assertEqual(cruce_sbx((4.0,), (12.0,), 1, problema, azar), ((6.0,), (10.0,)))
        azar.random.return_value = 0.875
        self.assertEqual(cruce_sbx((4.0,), (12.0,), 1, problema, azar), ((0.0,), (16.0,)))
        self.assertEqual(cruce_sbx((0.0,), (32.0,), 1, problema, azar), ((0.0,), (32.0,)))
        azar.random.return_value = 0
        self.assertEqual(cruce_sbx((4.0,), (12.0,), 1, problema, azar), ((8.0,), (8.0,)))
        azar.random.return_value = 0.9999999999999999
        hijos = cruce_sbx((0.0,), (32.0,), 1, problema, azar)
        self.assertEqual(hijos, ((0.0,), (32.0,)))
        self.assertEqual(cruce_sbx((8.0,), (8.0,), 1, problema, azar), ((8.0,), (8.0,)))

    def test_mutacion_uniforme_todos_los_genes(self):
        poblacion = [(1.0, 2.0), (3.0, 4.0)]
        self.assertEqual(mutar(poblacion, PROBLEMAS[0], 0, random.Random(1)), poblacion)
        azar = Mock()
        azar.random.return_value = 0.2
        azar.uniform.side_effect = [5.0, 6.0, 7.0, 8.0]
        self.assertEqual(mutar(poblacion, PROBLEMAS[0], 1, azar), [(5.0, 6.0), (7.0, 8.0)])
        self.assertEqual(poblacion, [(1.0, 2.0), (3.0, 4.0)])  # Padres intactos.

    def test_reproduccion_sin_cruce_y_padre_impar(self):
        padres = [(1.0, 2.0), (3.0, 4.0), (5.0, 6.0)]
        for metodo in METODOS_CRUCE:
            parametros = Parametros(metodo_cruce=metodo, prob_cruce=0)
            self.assertEqual(reproducir(padres, PROBLEMAS[0], parametros, random.Random(1)), padres)
            parametros = replace(parametros, prob_cruce=1)
            hijos = reproducir(padres, PROBLEMAS[0], parametros, random.Random(1))
            self.assertEqual(len(hijos), len(padres))
            self.assertEqual(hijos[-1], padres[-1])

    def test_ruleta_negativos_y_empates(self):
        poblacion = [Individuo((1.0,), -8), Individuo((2.0,), -3)]
        for maximizar in (True, False):
            problema = replace(PROBLEMAS[0], maximizar=maximizar)
            pesos = calcular_pesos(poblacion, problema)
            self.assertTrue(all(p > 0 for p in pesos))
            self.assertEqual(pesos.index(max(pesos)), 1 if maximizar else 0)
            self.assertEqual(calcular_pesos([poblacion[0]] * 2, problema), [1, 1])

    def test_ciclo_completo_dominios_elitismo_y_semilla(self):
        for problema in PROBLEMAS:
            for metodo in METODOS_CRUCE:
                parametros = Parametros(tamano_poblacion=15, generaciones=20, metodo_cruce=metodo,
                                        dimensiones=3 if problema.varias_variables else 1)
                historial = list(evolucionar(problema, parametros))
                self.assertEqual(historial, list(evolucionar(problema, parametros)))
                self.assertEqual([g.numero for g in historial], list(range(21)))
                for estado in historial:
                    self.assertEqual(len(estado.poblacion), 15)
                    self.assertTrue(all(problema.limite_inferior <= x <= problema.limite_superior
                                        for ind in estado.poblacion for x in ind.genes))
                for anterior, actual in zip(historial, historial[1:]):
                    self.assertIn(anterior.mejor, actual.poblacion)
                    comparar = self.assertGreaterEqual if problema.maximizar else self.assertLessEqual
                    comparar(actual.mejor.objetivo, anterior.mejor.objetivo)

    def test_sin_elites_y_cero_generaciones(self):
        for elites in (0, 14):
            historial = list(evolucionar(parametros=Parametros(tamano_poblacion=15, elites=elites, generaciones=3)))
            self.assertTrue(all(len(g.poblacion) == 15 for g in historial))
        self.assertEqual(len(list(evolucionar(parametros=Parametros(generaciones=0)))), 1)

    def test_validacion(self):
        for cambio in ({"metodo_cruce": "otro"}, {"prob_intercambio": -1}, {"alfa_aritmetico": 2},
                       {"eta_sbx": -1}, {"eta_sbx": float("nan")}, {"prob_mutacion": float("nan")},
                       {"elites": 60}, {"tamano_poblacion": 1}, {"generaciones": -1}, {"dimensiones": 2}):
            with self.assertRaises(ValueError):
                validar_parametros(PROBLEMAS[0], replace(Parametros(), **cambio))


if __name__ == "__main__":
    unittest.main()
