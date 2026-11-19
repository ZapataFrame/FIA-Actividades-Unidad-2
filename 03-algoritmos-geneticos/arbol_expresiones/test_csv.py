import csv
import os
import tempfile
import unittest

from PyQt6.QtWidgets import QApplication, QComboBox, QDoubleSpinBox, QLineEdit
from unittest.mock import patch

from interfaz import Ventana


class PruebasCsv(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_generar_csv_con_intervalo_y_paso(self):
        ventana = Ventana()
        ventana.entrada.setText("x^2")
        ventana.construir()
        ventana.csv_desde.setValue(-1)
        ventana.csv_hasta.setValue(1)
        ventana.csv_paso.setValue(0.5)
        with tempfile.TemporaryDirectory() as directorio:
            ruta = os.path.join(directorio, "salida.csv")
            with patch("interfaz.QFileDialog.getSaveFileName", return_value=(ruta, "CSV (*.csv)")):
                ventana.generar_csv()
            with open(ruta, encoding="utf-8", newline="") as archivo:
                filas = list(csv.reader(archivo))
        self.assertEqual(filas[0], ["x", "y"])
        self.assertEqual(len(filas), 6)  # encabezado + cinco puntos
        ventana.close()

    def test_widgets_tienen_paleta_clara(self):
        ventana = Ventana()
        for widget in ventana.findChildren((QLineEdit, QComboBox, QDoubleSpinBox)):
            self.assertEqual(widget.palette().base().color().name(), "#ffffff")
            self.assertEqual(widget.palette().text().color().name(), "#000000")
        ventana.close()


if __name__ == "__main__":
    unittest.main()
