import math
import random
import unittest
from algoritmo import Nodo, construir_arbol, evaluar, validar_arbol, ExpresionError
from genetico import Parametros, Individuo, RegresionSimbolica
from seleccion import seleccionar, METODOS
from mejoras_geneticas import simplificar, ajustar_salida
from entradas import EntradaEntera, EntradaReal


class PruebasSeleccion(unittest.TestCase):
    def setUp(self):
        self.poblacion=[Individuo(Nodo(str(i),tipo='numero'),loss,nodos=1)
                        for i,loss in enumerate((0.,1.,10.,math.inf))]

    def test_ruleta_rango_cero_e_invalidos(self):
        for metodo in ('ruleta','rango'):
            azar=random.Random(10)
            ganadores=[seleccionar(self.poblacion,azar,metodo) for _ in range(2000)]
            self.assertTrue(all(g.valido for g in ganadores))
            self.assertGreater(sum(g is self.poblacion[0] for g in ganadores),
                               sum(g is self.poblacion[2] for g in ganadores))
            self.assertIs(seleccionar([self.poblacion[-1]],azar,metodo),self.poblacion[-1])

    def test_uniforme_y_torneo_grande(self):
        azar=random.Random(4)
        self.assertIn(seleccionar(self.poblacion,azar,'uniforme'),self.poblacion)
        self.assertIn(seleccionar(self.poblacion,azar,'torneo',1000),self.poblacion)
        for metodo in METODOS:
            with self.assertRaises(ValueError):
                seleccionar([],azar,metodo)
        with self.assertRaises(InterruptedError):
            seleccionar(self.poblacion,azar,'torneo',10**20,lambda:True)

    def test_evolucion_cada_metodo(self):
        puntos=[(-2,4),(-1,1),(0,0),(1,1),(2,4)]
        for metodo in METODOS:
            p=Parametros(poblacion=12,generaciones=4,seleccion=metodo)
            estados=list(RegresionSimbolica(puntos,p).evolucionar())
            self.assertTrue(estados)
            for e in estados:
                self.assertEqual(len(e.individuos),12)
                self.assertTrue(0<e.diversidad<=1)
                for i in e.individuos:
                    validar_arbol(i.raiz,p.altura_maxima)


class PruebasMejoras(unittest.TestCase):
    def test_ajuste_lineal_y_coeficientes(self):
        puntos=[(x/4,2.7*(x/4)**2-1.3*x/4+.45) for x in range(-8,9)]
        m=RegresionSimbolica(puntos)
        individuo=m.evaluar(construir_arbol('2*(x*x) - 1*x + 1'))
        mejor=m.refinar_coeficientes(individuo,lambda:False)
        self.assertLess(mejor.perdida,individuo.perdida)
        lineal=RegresionSimbolica([(x,2.7*x-.45) for x in (-2,-1,0,1,2)])
        ajustado=lineal.refinar_coeficientes(lineal.evaluar(construir_arbol('2*x+1')),lambda:False)
        self.assertLess(ajustado.perdida,1e-15)

    def test_simplificacion_conserva_dominio(self):
        for texto in ('(2+3)*x','(x+0)/1','1*x'):
            raiz=construir_arbol(texto)
            for x in (-3,0,2):
                self.assertAlmostEqual(evaluar(raiz,{'x':x}),evaluar(simplificar(raiz),{'x':x}))
        for texto in ('x/x','0*log(x)'):
            with self.assertRaises(ExpresionError):
                evaluar(simplificar(construir_arbol(texto)),{'x':0})

    def test_apagar_hibrido_y_no_limitar_parametros(self):
        p=Parametros(poblacion=1000,generaciones=5000,altura_maxima=100,torneo=2000,
                     ajuste_lineal=False,refinar_constantes=False)
        self.assertEqual(p.altura_maxima,100)
        m=RegresionSimbolica([(-1,3),(1,5)],p)
        candidatos=[m.evaluar(construir_arbol('x'))]
        self.assertIs(m.refinar(candidatos,lambda:False),candidatos)
        profundo=Nodo('x',tipo='variable')
        for _ in range(70):
            profundo=Nodo('u-',profundo)
        self.assertTrue(m.evaluar(profundo).valido)

    def test_probabilidad_cero_no_introduce_mutaciones_ocultas(self):
        p=Parametros(poblacion=16,generaciones=2,prob_cruce=0,prob_mutacion=0,
                     inmigracion=0,ajuste_lineal=False,refinar_constantes=False,objetivo=0)
        estados=list(RegresionSimbolica([(-1,7),(0,9),(1,11)],p).evolucionar())
        originales={i.expresion for i in estados[0].individuos}
        self.assertTrue(all(i.expresion in originales for e in estados for i in e.individuos))

    def test_afin(self):
        puntos=[(x,1.8*math.sin(x)+.7) for x in (-2,-1,0,1,2)]
        m=RegresionSimbolica(puntos)
        raiz=ajustar_salida(construir_arbol('sin(x)'),m.xs,m.ys,m.evaluador,5)
        self.assertLess(m.evaluar(raiz).perdida,1e-25)


class PruebasEntradas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def test_entradas_sin_recorte(self):
        entero=EntradaEntera()
        entero.setValue(10**40)
        self.assertEqual(entero.value(),10**40)
        real=EntradaReal()
        real.setText('1e-35')
        self.assertEqual(real.value(),1e-35)
        entero.setText('letras')
        with self.assertRaises(ValueError):
            entero.value()


if __name__=='__main__':
    unittest.main()
