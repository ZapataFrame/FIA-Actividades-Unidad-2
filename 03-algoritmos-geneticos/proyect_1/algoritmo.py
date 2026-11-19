"""Algoritmo genético binario
"""

from dataclasses import dataclass
import math
import random


# Constantes editables. Las probabilidades están entre 0 y 1, no entre 0 y 100.
TAMANO_POBLACION = 60
NUMERO_GENERACIONES = 100
PRECISION = 0.001
PROBABILIDAD_CRUCE = 0.7
PROBABILIDAD_MUTACION = 0.01
NUMERO_ELITES = 1  # 0 desactiva el elitismo.
SEMILLA = 42  # La misma semilla y configuración repiten el experimento.


def funcion_maximizar(valores):
    x = valores[0]
    return 20 + math.e - 20 * math.exp(-0.2 * abs(x)) - math.exp(math.cos(2 * math.pi * x))


def funcion_minimizar(valores):
    x = valores[0]
    return -abs(x * math.sin(math.sqrt(abs(x))))


def funcion_varias_variables(valores):
    return sum(-x * math.sin(math.sqrt(abs(x))) for x in valores)


@dataclass(frozen=True)
class Problema:
    nombre: str
    funcion: object
    limite_inferior: float
    limite_superior: float
    maximizar: bool
    varias_variables: bool = False

PROBLEMAS = (
    Problema("Máximo · 20 + e − 20 exp(−0.2|x|) − exp(cos(2πx))", funcion_maximizar, 0, 32, True),
    Problema("Mínimo · −|x sen(√|x|)|", funcion_minimizar, -250, 250, False),
    Problema("Varias variables · Σ −xi sen(√|xi|)", funcion_varias_variables, 0, 100, False, True),
)

@dataclass(frozen=True)
class Parametros:
    tamano_poblacion: int = TAMANO_POBLACION
    generaciones: int = NUMERO_GENERACIONES
    precision: float = PRECISION
    prob_cruce: float = PROBABILIDAD_CRUCE
    prob_mutacion: float = PROBABILIDAD_MUTACION
    elites: int = NUMERO_ELITES
    semilla: int = SEMILLA
    dimensiones: int = 1


@dataclass(frozen=True)
class Individuo:
    cromosomas: tuple[str, ...] # Genotipo: un cromosoma binario por variable, por ejemplo ("0101", "1100").
    valores: tuple[float, ...]  # Fenotipo: valores reales decodificados.
    objetivo: float  # Valor real de la función, no es el peso de la ruleta.


@dataclass(frozen=True)
class Generacion:
    numero: int
    poblacion: tuple[Individuo, ...]
    mejor: Individuo
    promedio: float
    mejor_historico: Individuo


def validar_parametros(problema, parametros):
    p = parametros
    if p.tamano_poblacion < 2 or p.generaciones < 0:
        raise ValueError("La población debe ser ≥ 2 y las generaciones ≥ 0.")
    if not math.isfinite(p.precision) or p.precision <= 0:
        raise ValueError("La precisión debe ser un número positivo y finito.")
    if not 0 <= p.prob_cruce <= 1 or not 0 <= p.prob_mutacion <= 1:
        raise ValueError("Las probabilidades deben estar entre 0 y 1.")
    if not 0 <= p.elites < p.tamano_poblacion:
        raise ValueError("Las élites deben estar entre 0 y población − 1.")
    if p.dimensiones < 1 or (not problema.varias_variables and p.dimensiones != 1):
        raise ValueError("Los ejemplos de una variable requieren dimensiones = 1.")


def calcular_bits(problema, precision):
    """Encuentra L tal que la separación (b−a)/(2**L−1) ≤ precisión."""
    ancho = problema.limite_superior - problema.limite_inferior
    # log2(ancho) − log2(precisión) evita desbordar ancho/precisión.
    bits = max(1, math.ceil(math.log2(ancho) - math.log2(precision)))
    while ancho / (2**bits - 1) > precision:
        bits += 1
    return bits


def decodificar(cromosoma, problema):
    """Mapea 000…0 al límite inferior y 111…1 al superior."""
    entero = int(cromosoma, 2)
    fraccion = entero / (2 ** len(cromosoma) - 1)
    return problema.limite_inferior + fraccion * (problema.limite_superior - problema.limite_inferior)


def inicializar_poblacion(parametros, bits, azar):
    """Paso 1: genera bits independientes al azar para cada variable."""
    return [
        tuple(
            "".join(str(azar.randrange(2)) for _ in range(bits))
            for _ in range(parametros.dimensiones)
        )
        for _ in range(parametros.tamano_poblacion)
    ]


def evaluar(poblacion, problema):
    """Pasos 2 y 7: transforma genotipos en fenotipos y calcula f(x)."""
    evaluados = []
    for cromosomas in poblacion:
        valores = tuple(decodificar(c, problema) for c in cromosomas)
        objetivo = problema.funcion(valores)
        if not math.isfinite(objetivo):
            raise ValueError("La función objetivo produjo un valor no finito.")
        evaluados.append(Individuo(cromosomas, valores, objetivo))
    return evaluados


def obtener_mejor(poblacion, problema):
    """Último paso: compara el objetivo original, incluyendo valores negativos."""
    elegir = max if problema.maximizar else min
    return elegir(poblacion, key=lambda individuo: individuo.objetivo)


def calcular_pesos(poblacion, problema):
    """Convierte el objetivo en pesos no negativos para la selección por ruleta.

    Maximización: f − mínimo. Minimización: máximo − f. Así, mejores
    objetivos tienen mayor probabilidad, incluso cuando todos son negativos.
    Una pequeña base permite también seleccionar al peor.
    Si todos son iguales, todos reciben peso 1 (selección uniforme).
    Estos pesos son relativos a ESTA población; las gráficas muestran f.
    """
    objetivos = [ind.objetivo for ind in poblacion]
    minimo, maximo = min(objetivos), max(objetivos)
    amplitud = maximo - minimo
    if amplitud == 0:
        return [1.0] * len(poblacion)
    base = amplitud * 0.01
    if problema.maximizar:
        return [valor - minimo + base for valor in objetivos]
    return [maximo - valor + base for valor in objetivos]


def seleccionar(poblacion, problema, cantidad, azar):
    """Paso 4: sortea padres con reemplazo usando una ruleta ponderada.

    Un individuo puede ser elegido varias veces: cada sorteo es independiente.
    Seleccionar no garantiza que siempre gane el mejor.
    """
    pesos = calcular_pesos(poblacion, problema)
    padres = azar.choices(poblacion, weights=pesos, k=cantidad)
    return [padre.cromosomas for padre in padres]


def reproducir(padres, prob_cruce, azar):
    """Paso 5: cruce monopunto por variable, con probabilidad por pareja."""
    hijos = []
    for i in range(0, len(padres) - 1, 2):
        padre, madre = padres[i], padres[i + 1]
        hijo_a, hijo_b = [], []
        cruzar = azar.random() < prob_cruce
        for cromosoma_a, cromosoma_b in zip(padre, madre):
            if cruzar and len(cromosoma_a) > 1:
                # El corte interior evita intercambiar cromosomas completos.
                # Ejemplo: 01|11 y 10|00 producen 0100 y 1011.
                corte = azar.randrange(1, len(cromosoma_a))
                hijo_a.append(cromosoma_a[:corte] + cromosoma_b[corte:])
                hijo_b.append(cromosoma_b[:corte] + cromosoma_a[corte:])
            else:
                hijo_a.append(cromosoma_a)
                hijo_b.append(cromosoma_b)
        hijos.extend((tuple(hijo_a), tuple(hijo_b)))
    # También admitimos tamaños impares: el último padre pasa sin cruce.
    if len(padres) % 2:
        hijos.append(padres[-1])
    return hijos


def mutar(poblacion, prob_mutacion, azar):
    """Paso 6: sortea CADA bit; si muta, invierte 0↔1.

    0.01 significa 1 % por bit, no que mute exactamente 1 % de individuos.
    La mutación introduce variación que el cruce por sí solo no puede crear.
    """
    mutados = []
    for cromosomas in poblacion:
        nuevos = []
        for cromosoma in cromosomas:
            bits = []
            for bit in cromosoma:
                if azar.random() < prob_mutacion:
                    bit = "1" if bit == "0" else "0"
                bits.append(bit)
            nuevos.append("".join(bits))
        mutados.append(tuple(nuevos))
    return mutados


def criterio_parada(generacion, parametros):
    return generacion >= parametros.generaciones


def evolucionar(problema=PROBLEMAS[0], parametros=Parametros()):
    """Produce una instantánea por generación, empezando por la generación 0.

    Un generador permite a la interfaz pedir un paso sin bloquear la ventana.
    El mejor histórico es informativo; solo el elitismo lo conserva en la
    población. Sin elitismo, el mejor individuo puede perderse.
    """
    validar_parametros(problema, parametros)
    azar = random.Random(parametros.semilla)
    bits = calcular_bits(problema, parametros.precision)
    poblacion = inicializar_poblacion(parametros, bits, azar)
    poblacion = evaluar(poblacion, problema)
    numero = 0
    mejor_historico = obtener_mejor(poblacion, problema)

    while True:
        mejor = obtener_mejor(poblacion, problema)
        mejor_historico = obtener_mejor([mejor_historico, mejor], problema)
        promedio = sum(ind.objetivo for ind in poblacion) / len(poblacion)
        yield Generacion(numero, tuple(poblacion), mejor, promedio, mejor_historico)
        if criterio_parada(numero, parametros):
            break

        # Elitismo: reserva los mejores antes del cruce y la mutación.
        # Se agregan intactos al final: no se mutan accidentalmente.
        ordenados = sorted(poblacion, key=lambda ind: ind.objetivo, reverse=problema.maximizar)
        elites = [ind.cromosomas for ind in ordenados[:parametros.elites]]
        cantidad_hijos = parametros.tamano_poblacion - len(elites)
        padres = seleccionar(poblacion, problema, cantidad_hijos, azar)
        hijos = reproducir(padres, parametros.prob_cruce, azar)
        hijos = mutar(hijos, parametros.prob_mutacion, azar)
        poblacion = evaluar(elites + hijos, problema)
        numero += 1


if __name__ == "__main__":
    for estado in evolucionar():
        print(f"Generación {estado.numero:3}: mejor={estado.mejor.objetivo:.6f}, promedio={estado.promedio:.6f}")
    print("Mejor de la población final:", estado.mejor)
