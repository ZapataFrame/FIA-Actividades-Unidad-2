import math
import unittest

from metricas import calcular_metricas


class PruebasMetricas(unittest.TestCase):
    def test_ajuste_perfecto(self):
        self.assertEqual(calcular_metricas([1, 2, 3], [1, 2, 3]),
                         {"mse": 0.0, "nmse": 0.0, "rmse": 0.0, "r2": 1.0})

    def test_error_y_tamanos(self):
        metricas = calcular_metricas([1, 2], [2, 4])
        self.assertAlmostEqual(metricas["mse"], 2.5)
        self.assertAlmostEqual(metricas["rmse"], math.sqrt(2.5))
        with self.assertRaises(ValueError):
            calcular_metricas([], [])
        with self.assertRaises(ValueError):
            calcular_metricas([1], [1, 2])


if __name__ == "__main__":
    unittest.main()
