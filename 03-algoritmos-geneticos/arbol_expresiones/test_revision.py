"""Regresiones de estructura, biblioteca, datos y estado de la interfaz."""
import math
import tempfile
import unittest
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QDialog
from algoritmo import (Nodo, ExpresionError, evaluar, construir_arbol,
                       texto_inorder, validar_arbol, ExpressionParser)
from biblioteca import GeneradorExpresiones, Operacion
from datos import muestrear, leer_csv
from metricas import calcular_metricas
from interfaz import Ventana


class RevisionAlgoritmo(unittest.TestCase):
    def test_precedencia_y_serializacion(self):
        for texto, esperado in [('-2^2', -4), ('(-2)^2', 4), ('2^3^2',512),
                                 ('2^-2',.25), ('.5 + 1e-2',.51)]:
            raiz = construir_arbol(texto)
            self.assertAlmostEqual(evaluar(raiz), esperado)
            self.assertAlmostEqual(evaluar(construir_arbol(texto_inorder(raiz))), esperado)
        parser = ExpressionParser('2+3')
        self.assertEqual(evaluar(parser.parse()), evaluar(parser.parse()))

    def test_errores_numericos_y_aridad(self):
        for texto in ['(-1)^.5','1e309','1e308*1e308','sqrt(-1)','1/0']:
            with self.subTest(texto=texto), self.assertRaises(ExpresionError):
                evaluar(construir_arbol(texto))
        with self.assertRaises(ExpresionError):
            validar_arbol(Nodo('+', Nodo('1', tipo='numero')))
        hoja = Nodo('x', tipo='variable')
        with self.assertRaises(ExpresionError):
            validar_arbol(Nodo('+',hoja,hoja))
        with self.assertRaises(ValueError):
            GeneradorExpresiones(operaciones=[])
        with self.assertRaises(ValueError):
            GeneradorExpresiones(operaciones=[Operacion('sin',2,'funcion')])
        with self.assertRaises(ExpresionError):
            GeneradorExpresiones().generar_hasta(lambda _:False, 2)

    def test_datos_y_dominio(self):
        puntos = muestrear(construir_arbol('log(x)'),-1,1,.5)
        self.assertEqual([y is None for _,y in puntos],[True,True,True,False,False])
        self.assertEqual(len(muestrear(construir_arbol('x'),0,.3,.1)),4)
        with tempfile.TemporaryDirectory() as d:
            ruta=Path(d)/'datos.csv'
            ruta.write_text('\nx;y\n1;2\n3;4\n')
            self.assertEqual(leer_csv(ruta),[(1,2),(3,4)])
            ruta.write_text('incorrecto,4\n1,2\n')
            with self.assertRaises(ValueError):
                leer_csv(ruta)
        self.assertTrue(math.isnan(calcular_metricas([2,2],[2,2])['r2']))


class RevisionInterfaz(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def test_estado_actual_y_sin_valores_inventados(self):
        v=Ventana()
        try:
            self.assertFalse(hasattr(v,'variables_entrada'))
            self.assertFalse(v.historial.isVisible())
            v.entrada.setText('x^2')
            v.graficar_funcion()
            self.assertEqual(v.texto_construido,'x^2')
            self.assertEqual(v.grafica.muestras[0][1],100)
            self.assertEqual(v.pestanas.currentIndex(),1)
            self.assertEqual(v.findChildren(QDialog),[])
            v.entrada.setText('x+y')
            v.graficar_funcion()
            self.assertIn('sólo x',v.descripcion.text())
            self.assertEqual(v.grafica.muestras,[])
            v.entrada.setText('x+')
            v.construir()
            self.assertIsNone(v.raiz)
            self.assertFalse(v.play.isEnabled())
        finally:
            v.close()
