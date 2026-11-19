"""Estudia parámetros reales y compara las dos representaciones en CSV."""

import csv
from dataclasses import replace
from pathlib import Path
from statistics import mean, stdev
import sys
from time import perf_counter

from algoritmo import METODOS_CRUCE, PROBLEMAS, Parametros, evolucionar


# Edita estas variables para estudiar otro problema o ampliar las repeticiones.
PROBLEMA = PROBLEMAS[3]  # Rastrigin permite observar los mínimos locales.
PARAMETROS_BASE = Parametros(dimensiones=3)
SEMILLAS = range(10)  # Varias semillas evitan concluir a partir de una sola corrida.
VARIANTES = {
    "tamano_poblacion": [20, 60, 120],
    "generaciones": [30, 100, 200],
    "prob_cruce": [0.0, 0.4, 0.7, 1.0],
    "prob_mutacion": [0.0, 0.01, 0.05, 0.1],
    "elites": [0, 1, 2],
    "metodo_cruce": METODOS_CRUCE,
    "eta_sbx": [1, 5, 20],
}


def realizar_estudio(destino=None):
    if destino is None:
        destino = Path(__file__).parent / "resultados_estudio.csv"
    resumenes = []
    with Path(destino).open("w", newline="", encoding="utf-8") as archivo:
        columnas = ["problema", "parametro", "valor", "semilla", "mejor_final", "mejor_historico", "generacion_mejor_historico"]
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        for parametro, variantes in VARIANTES.items():
            for valor in variantes:
                mejores = []
                generaciones = []
                for semilla in SEMILLAS:
                    configuracion = replace(PARAMETROS_BASE, **{parametro: valor, "semilla": semilla})
                    historial = list(evolucionar(PROBLEMA, configuracion))
                    final = historial[-1]
                    # Primera generación que encontró el mejor resultado observado.
                    # Esto NO significa que se alcanzó el óptimo matemático.
                    encontrada = next(g.numero for g in historial if g.mejor.objetivo == final.mejor_historico.objetivo)
                    escritor.writerow(dict(zip(columnas, [PROBLEMA.nombre, parametro, valor, semilla,
                                                          final.mejor.objetivo, final.mejor_historico.objetivo, encontrada])))
                    mejores.append(final.mejor.objetivo)
                    generaciones.append(encontrada)
                resumenes.append((parametro, valor, mean(mejores), stdev(mejores) if len(mejores) > 1 else 0,
                                  mean(generaciones)))
    return resumenes


def comparar_representaciones(destino=None):
    """Reutiliza el algoritmo binario del proyecto 1 sin modificarlo.

    Conserva función, intervalos, dimensiones, población, generaciones,
    probabilidad de cruce, elitismo y conjunto de semillas. El operador de
    cruce cambia: monopunto binario frente a SBX real. La comparación evalúa
    estos DOS algoritmos completos, no solo el efecto de la representación.

    Igualamos la probabilidad de mutar al menos una vez por variable:
    p_gen = 1 − (1 − p_bit)**L. Esto NO iguala la magnitud de los cambios.
    Las mismas semillas tampoco generan las mismas poblaciones iniciales.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from proyect_1 import algoritmo as binario

    if destino is None:
        destino = Path(__file__).parent / "comparacion_representaciones.csv"
    resumenes = []
    columnas = ["problema", "representacion", "dimensiones", "semilla", "bits_por_variable",
                "prob_mutacion", "mejor_final", "segundos", "evaluaciones"]
    with Path(destino).open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        for problema in PROBLEMAS:
            dimensiones = 3 if problema.varias_variables else 1
            reales = replace(PARAMETROS_BASE, dimensiones=dimensiones)
            bits = binario.calcular_bits(problema, 0.001)
            prob_bit = 1 - (1 - reales.prob_mutacion) ** (1 / bits)
            binarios = binario.Parametros(tamano_poblacion=reales.tamano_poblacion,
                                         generaciones=reales.generaciones, precision=0.001,
                                         prob_cruce=reales.prob_cruce, prob_mutacion=prob_bit,
                                         elites=reales.elites, dimensiones=dimensiones)
            for nombre, algoritmo, parametros in [("binaria", binario.evolucionar, binarios),
                                                  ("real", evolucionar, reales)]:
                mejores, tiempos = [], []
                for semilla in SEMILLAS:
                    inicio = perf_counter()
                    # Solo conservamos el estado final, no todo el historial.
                    for final in algoritmo(problema, replace(parametros, semilla=semilla)):
                        pass
                    segundos = perf_counter() - inicio
                    evaluaciones = parametros.tamano_poblacion * (parametros.generaciones + 1)
                    escritor.writerow(dict(zip(columnas, [problema.nombre, nombre, dimensiones, semilla,
                                                          bits if nombre == "binaria" else "",
                                                          parametros.prob_mutacion, final.mejor.objetivo,
                                                          segundos, evaluaciones])))
                    mejores.append(final.mejor.objetivo)
                    tiempos.append(segundos)
                desviacion = stdev(mejores) if len(mejores) > 1 else 0
                resumenes.append((problema.nombre, nombre, mean(mejores), desviacion, mean(tiempos)))
    return resumenes


if __name__ == "__main__":
    print("Se mantienen los parámetros base y se cambia uno por comparación.")
    print("Parámetro             Valor   Media final   Desv. típica   Gen. mejor observado")
    for parametro, valor, promedio, desviacion, generacion in realizar_estudio():
        print(f"{parametro:20} {str(valor):12} {promedio:13.8f} {desviacion:13.6g} {generacion:20.1f}")
    print("Resultados individuales en resultados_estudio.csv, junto a este script.")
    print("\nComparación binaria / real (media ± desviación del mejor final):")
    for problema, representacion, promedio, desviacion, segundos in comparar_representaciones():
        print(f"{problema}\n  {representacion:8}: {promedio:.8f} ± {desviacion:.6g}; {segundos:.4f} s de media")
    print("Resultados individuales en comparacion_representaciones.csv.")
