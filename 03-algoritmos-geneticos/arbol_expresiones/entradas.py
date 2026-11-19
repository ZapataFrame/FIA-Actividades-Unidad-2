"""Entradas numéricas sin recorte silencioso a los máximos de QSpinBox.

La validación matemática corresponde a Parametros. Se aceptan enteros de
Python y reales finitos en notación decimal o científica, sin topes de negocio.
"""
from PyQt6.QtWidgets import QLineEdit


class EntradaEntera(QLineEdit):
    def __init__(self, valor=0):
        super().__init__(str(valor))

    def value(self):
        try:
            return int(self.text().strip())
        except ValueError as error:
            raise ValueError('Se esperaba un entero: '+repr(self.text())) from error

    def setValue(self,valor):
        self.setText(str(valor))


class EntradaReal(QLineEdit):
    def __init__(self,valor=0.):
        super().__init__(str(valor))

    def value(self):
        try:
            return float(self.text().strip())
        except ValueError as error:
            raise ValueError('Se esperaba un número real: '+repr(self.text())) from error

    def setValue(self,valor):
        self.setText(str(valor))
