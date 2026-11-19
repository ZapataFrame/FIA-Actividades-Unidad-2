"""Pruebas de operadores, evaluación completa, evolución y ejecución Qt."""
import math
import random
import tempfile
import time
import unittest
from pathlib import Path

from algoritmo import construir_arbol, validar_arbol, texto_inorder
from biblioteca import altura_arbol
from genetico import (Parametros, RegresionSimbolica, MUTACIONES, clonar,
                      ubicaciones, cruzar, mutar, generar_arbol)


class PruebasProgramacionGenetica(unittest.TestCase):
    def test_evaluacion_completa_y_metricas(self):
        motor=RegresionSimbolica([(-1,1),(0,0),(1,1)],Parametros(poblacion=4,torneo=2))
        perfecto=motor.evaluar(construir_arbol('x*x'))
        self.assertEqual(perfecto.perdida,0)
        self.assertEqual(dict(perfecto.metricas)['r2'],1)
        invalido=motor.evaluar(construir_arbol('1/x'))
        self.assertFalse(invalido.valido)
        self.assertIn('División',invalido.error)
        self.assertEqual(invalido.metricas,())

    def test_operadores_respetan_altura_aridad_y_identidad(self):
        azar=random.Random(12)
        for _ in range(40):
            a=generar_arbol(azar,5,forzar=True)
            b=generar_arbol(azar,5,forzar=True)
            textos=texto_inorder(a),texto_inorder(b)
            hijos=cruzar(a,b,azar,5)
            for hijo in hijos:
                validar_arbol(hijo,5)
                ids={id(n) for _,n in ubicaciones(hijo)}
                self.assertTrue(ids.isdisjoint({id(n) for _,n in ubicaciones(a)}))
                self.assertTrue(ids.isdisjoint({id(n) for _,n in ubicaciones(b)}))
                for tipo in MUTACIONES:
                    mutado=mutar(hijo,tipo,azar,5)
                    validar_arbol(mutado,5)
                    self.assertLessEqual(altura_arbol(mutado),5)
            self.assertEqual(textos,(texto_inorder(a),texto_inorder(b)))

    def test_reproducibilidad_elitismo_y_mejora(self):
        puntos=[(x/2,(x/2)**2+x/2+1) for x in range(-6,7)]
        p=Parametros(poblacion=60,generaciones=50,semilla=42)
        a=list(RegresionSimbolica(puntos,p).evolucionar())
        b=list(RegresionSimbolica(puntos,p).evolucionar())
        self.assertEqual([e.mejor.expresion for e in a],[e.mejor.expresion for e in b])
        for antes,despues in zip(a,a[1:]):
            self.assertLessEqual(despues.mejor.perdida,antes.mejor.perdida)
        self.assertLess(a[-1].mejor_historico.perdida,a[0].mejor.perdida)
        self.assertTrue(all(len(e.individuos)==p.poblacion for e in a))

    def test_parametros_parada_y_cancelacion(self):
        for cambios in ({'prob_cruce':1.5},{'elitismo':80},{'pesos_mutacion':(0,0,0,0)}, {'altura_maxima':0}):
            with self.assertRaises(ValueError):
                Parametros(**cambios)
        puntos=[(-1,-1),(0,0),(1,1)]
        p=Parametros(poblacion=6,generaciones=0,torneo=2)
        estados=list(RegresionSimbolica(puntos,p).evolucionar())
        self.assertEqual(len(estados),1)
        cancelado=[False]
        g=RegresionSimbolica(puntos,Parametros(objetivo=0)).evolucionar(lambda:cancelado[0])
        next(g)
        cancelado[0]=True
        self.assertEqual(list(g),[])
        for metrica in ('nmse','r2'):
            with self.assertRaises(ValueError):
                RegresionSimbolica([(-1,1),(1,1)],Parametros(metrica=metrica))
        for metrica in ('mse','nmse','rmse','r2'):
            motor=RegresionSimbolica(puntos,Parametros(metrica=metrica))
            self.assertEqual(motor.evaluar(construir_arbol('x')).perdida,0)


class PruebasPanelGenetico(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def esperar(self,panel,segundos=8):
        limite=time.monotonic()+segundos
        while panel.en_ejecucion and time.monotonic()<limite:
            self.app.processEvents()
            time.sleep(.005)
        self.app.processEvents()
        self.assertFalse(panel.en_ejecucion)

    def test_csv_evolucion_individuos_y_editor(self):
        from interfaz import Ventana
        ventana=Ventana()
        panel=ventana.genetico
        try:
            with tempfile.TemporaryDirectory() as d:
                ruta=Path(d)/'parabola.csv'
                ruta.write_text('x,y\n-2,5\n-1,2\n0,1\n1,2\n2,5\n')
                panel.cargar_csv(str(ruta))
                panel.poblacion.setValue(12)
                panel.generaciones.setValue(3)
                panel.ejecutar()
                self.esperar(panel)
                self.assertTrue(panel.estados)
                self.assertEqual(panel.tabla.rowCount(),12)
                self.assertIsNotNone(panel.seleccionado)
                panel.aplicar_individuo()
                self.assertIsNotNone(ventana.raiz)
                self.assertEqual(len(ventana.puntos_csv),5)
                self.assertEqual(ventana.pestanas.currentIndex(),0)
                panel.generaciones.setValue(200)
                panel.objetivo.setValue(0)
                panel.ejecutar()
                panel.cancelar()
                self.esperar(panel)
                self.assertIn('Detenida',panel.estado.text())
        finally:
            if panel.en_ejecucion:
                panel.cancelar()
                self.esperar(panel)
            ventana.close()


if __name__=='__main__':
    unittest.main()
