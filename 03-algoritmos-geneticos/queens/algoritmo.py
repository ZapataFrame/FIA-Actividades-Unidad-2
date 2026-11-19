"""N reinas mediante un algoritmo genético de permutaciones, sin DEAP.

Cada índice es una columna y su gen es la fila (de 1 a n). Empieza leyendo
evolucionar(): sus llamadas siguen los pasos del algoritmo genético general.
"""

from dataclasses import dataclass
import random


# Probabilidades entre 0 y 1. Aquí la mutación se sortea POR INDIVIDUO.
NUMERO_REINAS = 8
TAMANO_POBLACION = 80
LIMITE_GENERACIONES = 500
PROBABILIDAD_CRUCE = 0.9
PROBABILIDAD_MUTACION = 0.2
NUMERO_ELITES = 2  # 0 desactiva el elitismo.
SEMILLA = 42


@dataclass(frozen=True)
class Parametros:
    n: int = NUMERO_REINAS
    tamano_poblacion: int = TAMANO_POBLACION
    generaciones: int = LIMITE_GENERACIONES
    prob_cruce: float = PROBABILIDAD_CRUCE
    prob_mutacion: float = PROBABILIDAD_MUTACION
    elites: int = NUMERO_ELITES
    semilla: int = SEMILLA


@dataclass(frozen=True)
class Individuo:
    # Ejemplo: (2, 4, 1, 3) significa reina en (columna 1, fila 2), etc.
    # Es una permutación: todas las filas aparecen exactamente una vez.
    genes: tuple[int, ...]
    colisiones: int  # Número de pares que se atacan, no número de reinas.


@dataclass(frozen=True)
class Generacion:
    numero: int
    poblacion: tuple[Individuo, ...]
    mejor: Individuo
    promedio: float
    mejor_historico: Individuo


def validar_parametros(parametros):
    p = parametros
    for nombre in ("n", "tamano_poblacion", "generaciones", "elites", "semilla"):
        if type(getattr(p, nombre)) is not int:
            raise ValueError(f"{nombre} debe ser un entero.")
    if p.n < 1 or p.tamano_poblacion < 2 or p.generaciones < 0:
        raise ValueError("Usa n ≥ 1, población ≥ 2 y generaciones ≥ 0.")
    if not 0 <= p.prob_cruce <= 1 or not 0 <= p.prob_mutacion <= 1:
        raise ValueError("Las probabilidades deben estar entre 0 y 1.")
    if not 0 <= p.elites < p.tamano_poblacion:
        raise ValueError("Las élites deben estar entre 0 y población − 1.")


def inicializar_poblacion(parametros, azar):
    """Paso 1: cada candidato es un orden aleatorio de las filas 1…n.

    random.sample sin reemplazo impide repetir filas DENTRO del individuo.
    Dos individuos completos sí pueden coincidir: eso no invalida la población.
    """
    filas = range(1, parametros.n + 1)
    return [tuple(azar.sample(filas, parametros.n)) for _ in range(parametros.tamano_poblacion)]


def obtener_colisiones(genes):
    """Devuelve los pares de columnas (índices desde 0) con ataque diagonal.

    Dos reinas comparten diagonal si la distancia entre filas es igual a la
    distancia entre columnas: abs(fila_i − fila_j) == abs(i − j).
    La representación ya garantiza filas y columnas distintas. Recorremos
    solo i<j para contar cada pareja una vez. Coste: O(n²) por individuo.
    """
    return tuple(
        (i, j)
        for i in range(len(genes))
        for j in range(i + 1, len(genes))
        if abs(genes[i] - genes[j]) == j - i
    )


def evaluar(poblacion):
    """Pasos 2 y 7: valida permutaciones y calcula los pares en conflicto."""
    evaluados = []
    for genes in poblacion:
        filas_esperadas = list(range(1, len(genes) + 1))
        son_enteros = all(type(gen) is int for gen in genes)
        if not genes or not son_enteros or sorted(genes) != filas_esperadas:
            raise ValueError("Cada individuo debe ser una permutación de 1 a n.")
        evaluados.append(Individuo(tuple(genes), len(obtener_colisiones(genes))))
    return evaluados


def obtener_mejor(poblacion):
    return min(poblacion, key=lambda individuo: individuo.colisiones)


def seleccionar(poblacion, cantidad, azar):
    """Paso 4: ruleta con reemplazo; menos colisiones implica mayor peso.

    Peso = 1/(1+colisiones): siempre positivo, incluso cuando se encuentra
    una solución con 0 conflictos. El peso no es la función objetivo.
    Cada padre puede salir varias veces; elegir al mejor no está garantizado.
    """
    pesos = [1 / (1 + individuo.colisiones) for individuo in poblacion]
    padres = azar.choices(poblacion, weights=pesos, k=cantidad)
    return [padre.genes for padre in padres]


def cruce_orden(padre, madre, inicio, fin):
    """OX: conserva padre[inicio:fin] y completa en el orden de la madre.

    El tramo es [inicio, fin), como los slices de Python. Se empieza a leer
    la madre desde fin, circularmente, omitiendo los valores ya copiados.
    Los huecos se llenan también desde fin. Así cada fila aparece una vez.
    Un cruce monopunto normal podría duplicar filas y dejar de ser válido.
    """
    n = len(padre)
    hijo = [None] * n
    hijo[inicio:fin] = padre[inicio:fin]
    copiados = set(padre[inicio:fin])
    restantes = [gen for gen in madre[fin:] + madre[:fin] if gen not in copiados]
    huecos = list(range(fin, n)) + list(range(inicio))
    for posicion, gen in zip(huecos, restantes):
        hijo[posicion] = gen
    return tuple(hijo)


def reproducir(padres, parametros, azar):
    """Paso 5: sortea OX por pareja y genera dos hijos complementarios."""
    hijos = []
    for i in range(0, len(padres) - 1, 2):
        padre, madre = padres[i], padres[i + 1]
        if parametros.n > 1 and azar.random() < parametros.prob_cruce:
            # Cortes entre genes: el extremo n es válido para un slice.
            inicio, fin = sorted(azar.sample(range(parametros.n + 1), 2))
            hijos.append(cruce_orden(padre, madre, inicio, fin))
            hijos.append(cruce_orden(madre, padre, inicio, fin))
        else:
            hijos.extend((padre, madre))
    if len(padres) % 2:
        hijos.append(padres[-1])
    return hijos


def mutar(poblacion, prob_mutacion, azar):
    """Paso 6: mutación por intercambio, con un sorteo POR INDIVIDUO.

    Si se activa, intercambia dos posiciones distintas. Las filas conservan
    sus valores, pero cambian de columna. Asignar una fila aleatoria a un gen
    podría repetir filas; el intercambio mantiene la permutación válida.
    """
    mutados = []
    for genes in poblacion:
        nuevos = list(genes)  # Copia: nunca modifica los padres ni las élites.
        if len(nuevos) > 1 and azar.random() < prob_mutacion:
            i, j = azar.sample(range(len(nuevos)), 2)
            nuevos[i], nuevos[j] = nuevos[j], nuevos[i]
        mutados.append(tuple(nuevos))
    return mutados


def criterio_parada(estado, parametros):
    """0 conflictos certifica una solución; el límite impide buscar sin fin."""
    return estado.mejor.colisiones == 0 or estado.numero >= parametros.generaciones


def evolucionar(parametros=Parametros()):
    """Entrega la población inicial (generación 0) y cada generación posterior.

    Se detiene al encontrar una solución o agotar generaciones. El histórico
    solo registra; el elitismo es quien conserva individuos en la población.
    N=1 tiene solución inmediata. N=2 y n=3 no tienen solución: permiten
    observar la búsqueda, que siempre se detendrá por el límite configurado.
    """
    validar_parametros(parametros)
    azar = random.Random(parametros.semilla)
    poblacion = evaluar(inicializar_poblacion(parametros, azar))
    mejor_historico = obtener_mejor(poblacion)
    numero = 0

    while True:
        mejor = obtener_mejor(poblacion)
        mejor_historico = obtener_mejor([mejor_historico, mejor])
        promedio = sum(ind.colisiones for ind in poblacion) / len(poblacion)
        estado = Generacion(numero, tuple(poblacion), mejor, promedio, mejor_historico)
        yield estado
        if criterio_parada(estado, parametros):
            break

        ordenados = sorted(poblacion, key=lambda ind: ind.colisiones)
        elites = [ind.genes for ind in ordenados[:parametros.elites]]
        cantidad_hijos = parametros.tamano_poblacion - len(elites)
        padres = seleccionar(poblacion, cantidad_hijos, azar)
        hijos = reproducir(padres, parametros, azar)
        hijos = mutar(hijos, parametros.prob_mutacion, azar)
        poblacion = evaluar(elites + hijos)
        numero += 1


if __name__ == "__main__":
    for estado in evolucionar():
        print(f"Generación {estado.numero:3}: mejor={estado.mejor.colisiones}, promedio={estado.promedio:.2f}")
    print("Solución encontrada" if estado.mejor.colisiones == 0 else "Límite alcanzado sin solución")
    print("Filas por columna:", estado.mejor.genes)
