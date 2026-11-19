"""Lectura, muestreo y exportación de puntos; no depende de Qt."""

import csv
import math

from algoritmo import ExpressionEvaluator, ExpresionError, variables_en_arbol


def validar_funcion(raiz):
    otras = variables_en_arbol(raiz) - {"x"}
    if otras:
        raise ExpresionError("Para graficar usa sólo x. Variables sin valor: " + ", ".join(sorted(otras)))


def muestrear(raiz, desde, hasta, paso, tolerancia=1e-12):
    """Incluye el inicio y el final sólo si coincide con el paso.

    Usa índices enteros para evitar acumular error sumando el paso. Los huecos
    de dominio se conservan como None para no unirlos al dibujar una curva.
    """
    validar_funcion(raiz)
    if not all(math.isfinite(v) for v in (desde, hasta, paso)) or hasta <= desde or paso <= 0:
        raise ValueError("Usa un intervalo creciente y un paso positivo finito.")
    razon = (hasta - desde) / paso
    if not math.isfinite(razon) or razon > 99999:
        raise ValueError("Máximo 100,000 muestras. Aumenta el paso.")
    cantidad = math.floor(razon + 1e-10) + 1
    evaluador = ExpressionEvaluator(tolerancia=tolerancia)
    puntos = []
    for i in range(cantidad):
        x = desde + i * paso
        evaluador.variables["x"] = x
        try:
            y = evaluador.evaluate(raiz)
        except ExpresionError:
            y = None
        puntos.append((x, y))
    return puntos


def leer_csv(ruta):
    """Dos columnas x,y; encabezado opcional, coma o punto y coma."""
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        muestra = archivo.read(4096)
        archivo.seek(0)
        try:
            dialecto = csv.Sniffer().sniff(muestra, delimiters=",;")
        except csv.Error:
            dialecto = csv.excel
        puntos = []
        primera = True
        for numero, fila in enumerate(csv.reader(archivo, dialecto), 1):
            if not fila or all(not c.strip() for c in fila):
                continue
            if primera and [c.strip().lower() for c in fila] == ["x", "y"]:
                primera = False
                continue
            primera = False
            if len(fila) != 2:
                raise ValueError(f"Fila {numero}: se requieren exactamente dos columnas X,Y.")
            try:
                x, y = map(float, fila)
            except ValueError as error:
                raise ValueError(f"Fila {numero}: valores no numéricos.") from error
            if not math.isfinite(x) or not math.isfinite(y):
                raise ValueError(f"Fila {numero}: valores no finitos.")
            puntos.append((x, y))
        if not puntos:
            raise ValueError("El CSV no contiene puntos.")
        return puntos


def guardar_csv(ruta, puntos):
    validos = [(x, y) for x, y in puntos if y is not None]
    if not validos:
        raise ValueError("No hay puntos válidos para guardar.")
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["x", "y"])
        escritor.writerows(validos)
    return len(validos)
