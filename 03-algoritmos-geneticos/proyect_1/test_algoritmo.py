"""Pruebas de propiedades: operadores, ruleta, tamaño y elitismo."""

from dataclasses import replace
import random
import unittest

from algoritmo import (
    PROBLEMAS, Parametros, calcular_bits, calcular_pesos, decodificar,
    evaluar, evolucionar, mutar, reproducir, validar_parametros,
)


class PruebasAlgoritmo(unittest.TestCase):
    def test_precision_y_extremos(self):
        for problema in PROBLEMAS:
            for precision in (0.001, 0.1, 1000):
                bits = calcular_bits(problema, precision)
                self.assertLessEqual((problema.limite_superior - problema.limite_inferior) / (2**bits - 1), precision)
                self.assertEqual(decodificar("0" * bits, problema), problema.limite_inferior)
                self.assertEqual(decodificar("1" * bits, problema), problema.limite_superior)

    def test_pesos_con_objetivos_negativos_y_empates(self):
        # Una función artificial permite controlar exactamente la ordenación.
        for maximizar in (True, False):
            problema = replace(PROBLEMAS[0], funcion=lambda valores: valores[0] - 10,
                               limite_inferior=0, limite_superior=3, maximizar=maximizar)
            poblacion = evaluar([("00",), ("01",), ("11",)], problema)
            pesos = calcular_pesos(poblacion, problema)
            self.assertTrue(all(peso > 0 for peso in pesos))
            self.assertEqual(pesos.index(max(pesos)), 2 if maximizar else 0)
            self.assertEqual(calcular_pesos([poblacion[0]] * 3, problema), [1, 1, 1])

    def test_mutacion_cero_y_uno_todas_las_variables(self):
        poblacion = [("0101", "1100"), ("0000", "1111")]
        self.assertEqual(mutar(poblacion, 0, random.Random(1)), poblacion)
        self.assertEqual(mutar(poblacion, 1, random.Random(1)), [("1010", "0011"), ("1111", "0000")])

    def test_cruce_y_padre_impar(self):
        padres = [("0000", "0000"), ("1111", "1111"), ("1010", "1010")]
        self.assertEqual(reproducir(padres, 0, random.Random(1)), padres)
        hijos = reproducir(padres, 1, random.Random(1))
        self.assertEqual(hijos[-1], padres[-1])
        for variable in range(2):
            self.assertIn("0", hijos[0][variable])
            self.assertIn("1", hijos[0][variable])
            self.assertEqual(hijos[1][variable], "".join("1" if b == "0" else "0" for b in hijos[0][variable]))

    def test_ciclo_completo_reproducible_y_elitismo(self):
        for problema in PROBLEMAS:
            parametros = Parametros(tamano_poblacion=15, generaciones=25,
                                    dimensiones=3 if problema.varias_variables else 1)
            historial = list(evolucionar(problema, parametros))
            self.assertEqual(historial, list(evolucionar(problema, parametros)))
            self.assertEqual([g.numero for g in historial], list(range(26)))
            for anterior, actual in zip(historial, historial[1:]):
                self.assertEqual(len(actual.poblacion), 15)
                self.assertIn(anterior.mejor.cromosomas, [ind.cromosomas for ind in actual.poblacion])
                comparar = self.assertGreaterEqual if problema.maximizar else self.assertLessEqual
                comparar(actual.mejor.objetivo, anterior.mejor.objetivo)

    def test_sin_elites_y_solo_generacion_inicial(self):
        for elites in (0, 14):
            historial = list(evolucionar(parametros=Parametros(tamano_poblacion=15, elites=elites, generaciones=3)))
            self.assertTrue(all(len(g.poblacion) == 15 for g in historial))
        self.assertEqual(len(list(evolucionar(parametros=Parametros(generaciones=0)))), 1)

    def test_parametros_invalidos(self):
        for cambio in ({"precision": 0}, {"precision": float("nan")}, {"prob_mutacion": 2},
                       {"elites": 60}, {"tamano_poblacion": 1}, {"dimensiones": 2}, {"generaciones": -1}):
            with self.assertRaises(ValueError):
                validar_parametros(PROBLEMAS[0], replace(Parametros(), **cambio))


if __name__ == "__main__":
    unittest.main()
