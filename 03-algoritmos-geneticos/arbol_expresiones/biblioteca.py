"""Biblioteca reutilizable para crear expresiones matemáticas válidas.

La generación trabaja con nodos, no concatenando texto al azar. Así respeta la
aridad de cada operación y nunca produce expresiones incompletas como ``sin +``.
"""

import random

from algoritmo import (Nodo, Operacion, OPERACIONES, FUNCIONES, CONSTANTES,
                       ExpresionError, texto_inorder)


class BibliotecaOperaciones:
    """Catálogo compartido con el intérprete y la programación genética."""

    BINARIAS = tuple(o for o in OPERACIONES if o.aridad == 2)
    UNARIAS = tuple(o for o in OPERACIONES if o.aridad == 1)

    @classmethod
    def todas(cls):
        return cls.BINARIAS + cls.UNARIAS


class GeneradorExpresiones:
    """Genera expresiones aleatorias con altura mínima y máxima configurables.

    La altura mínima por defecto es 3 (o la máxima si esta es menor), para que
    el resultado no sea una sola hoja o una operación aislada.
    """

    def __init__(self, altura_maxima=4, variables=("x", "y"), semilla=None,
                 operaciones=None, altura_minima=None):
        if type(altura_maxima) is not int or altura_maxima < 1:
            raise ValueError("La altura máxima debe ser un entero positivo.")
        if not variables:
            raise ValueError("Debe existir al menos una variable.")
        altura_minima = min(3, altura_maxima) if altura_minima is None else altura_minima
        if type(altura_minima) is not int or not 1 <= altura_minima <= altura_maxima:
            raise ValueError("La altura mínima debe estar entre 1 y la máxima.")
        self.altura_maxima = altura_maxima
        self.altura_minima = altura_minima
        self.variables = tuple(variables)
        if any(not isinstance(v,str) or not v.isascii() or not v.isidentifier()
               or v in FUNCIONES or v in CONSTANTES for v in self.variables):
            raise ValueError("Variables inválidas o reservadas.")
        self.azar = random.Random(semilla)
        self.operaciones = tuple(BibliotecaOperaciones.todas() if operaciones is None else operaciones)
        if not self.operaciones:
            raise ValueError("Debe existir al menos una operación.")
        if any(operacion not in OPERACIONES for operacion in self.operaciones):
            raise ValueError("Cada operación debe tener aridad 1 o 2.")

    def generar_arbol(self):
        return self._generar_nodo(self.altura_maxima, self.altura_minima)

    def generar(self):
        """Devuelve texto listo para introducir en ``ExpressionParser``."""
        return texto_inorder(self.generar_arbol())

    def generar_hasta(self, validar, intentos=100):
        """Genera texto hasta que ``validar(texto)`` devuelva ``True``.

        Es útil para funciones aleatorias con dominios restringidos: el
        generador mantiene su catálogo matemático, mientras la aplicación
        decide si una expresión concreta puede evaluarse con sus variables.
        """
        if intentos < 1:
            raise ValueError("Los intentos deben ser positivos.")
        for _ in range(intentos):
            texto = self.generar()
            if validar(texto):
                return texto
        raise ExpresionError("No se encontró una expresión válida en los intentos permitidos.")

    def _generar_nodo(self, altura_disponible, altura_minima):
        if altura_disponible <= 1:
            return self._hoja()

        # Las hojas siguen teniendo probabilidad de aparecer en niveles altos,
        # evitando que todas las expresiones tengan exactamente la misma forma.
        # Mientras queden niveles obligatorios, el nodo debe tener hijos.
        # Después se permite una hoja aleatoria para variar la longitud.
        if altura_minima <= 1 and self.azar.random() < 0.15:
            return self._hoja()
        operacion = self.azar.choice(self.operaciones)
        hijos = [self._generar_nodo(altura_disponible - 1, max(1, altura_minima - 1))
                 for _ in range(operacion.aridad)]
        if operacion.tipo == "funcion":
            return Nodo(operacion.simbolo, hijos[0], tipo="funcion")
        if operacion.aridad == 1:
            return Nodo(operacion.simbolo, hijos[0], tipo="operador")
        return Nodo(operacion.simbolo, hijos[0], hijos[1], tipo="operador")

    def _hoja(self):
        if self.azar.random() < 0.65:
            return Nodo(self.azar.choice(self.variables), tipo="variable")
        return Nodo(str(self.azar.randint(1, 9)), tipo="numero")


def altura_arbol(nodo):
    """Calcula la altura usando 1 para una hoja y 0 para árbol vacío."""
    if nodo is None:
        return 0
    return 1 + max(altura_arbol(nodo.izquierdo), altura_arbol(nodo.derecho))
