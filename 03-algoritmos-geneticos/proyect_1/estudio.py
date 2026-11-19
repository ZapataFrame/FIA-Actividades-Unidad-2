"""Compara un parámetro a la vez y guarda resultados reproducibles en CSV."""

import csv
from dataclasses import replace
from pathlib import Path
from statistics import mean, stdev

from algoritmo import PROBLEMAS, Parametros, evolucionar


# Edita estas variables para estudiar otro problema o ampliar las repeticiones.
PROBLEMA = PROBLEMAS[0]
PARAMETROS_BASE = Parametros()
SEMILLAS = range(10)  # Varias semillas evitan concluir a partir de una sola corrida.
VARIANTES = {
    "tamano_poblacion": [20, 60, 120],
    "generaciones": [30, 100, 200],
    "precision": [0.1, 0.01, 0.001],
    "prob_cruce": [0.0, 0.4, 0.7, 1.0],
    "prob_mutacion": [0.0, 0.001, 0.01, 0.05],
    "elites": [0, 1, 2],
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


if __name__ == "__main__":
    print("Se mantienen los parámetros base y se cambia uno por comparación.")
    print("Parámetro             Valor   Media final   Desv. típica   Gen. mejor observado")
    for parametro, valor, promedio, desviacion, generacion in realizar_estudio():
        print(f"{parametro:20} {valor:7g} {promedio:13.8f} {desviacion:13.6g} {generacion:20.1f}")
    print("Resultados individuales en resultados_estudio.csv, junto a este script.")
