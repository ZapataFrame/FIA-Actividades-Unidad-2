import unittest

from algoritmo import ExpresionError, ExpressionEvaluator, construir_arbol, evaluar
from biblioteca import GeneradorExpresiones, altura_arbol


class PruebasRegresion(unittest.TestCase):
    def test_nodos_repetidos_no_se_fusionan(self):
        raiz = construir_arbol("x + x")
        self.assertIsNot(raiz.izquierdo, raiz.derecho)

    def test_dominio_de_logaritmo_se_informa(self):
        with self.assertRaises(ExpresionError):
            evaluar(construir_arbol("log(tan(y))"), {"y": 2})

    def test_variables_deben_ser_finitas(self):
        with self.assertRaises(ExpresionError):
            ExpressionEvaluator({"x": float("inf")})

    def test_generador_crea_expresiones_largas_y_parseables(self):
        for semilla in range(25):
            generador = GeneradorExpresiones(5, semilla=semilla)
            texto = generador.generar()
            raiz = construir_arbol(texto)
            self.assertGreaterEqual(altura_arbol(raiz), 3)
            self.assertLessEqual(altura_arbol(raiz), 5)


if __name__ == "__main__":
    unittest.main()
