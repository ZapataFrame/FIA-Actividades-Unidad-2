"""
Proyecto 2: algoritmo genético con genes reales.
Se adapta el ciclo, la ruleta y el elitismo del proyecto 1.
"""

from dataclasses import dataclass
import math
import random


# Constantes editables. Las probabilidades están entre 0 y 1, no entre 0 y 100.
TAMANO_POBLACION = 60
NUMERO_GENERACIONES = 100
PROBABILIDAD_CRUCE = 0.7
PROBABILIDAD_MUTACION = 0.05
NUMERO_ELITES = 1  # 0 desactiva el elitismo.
SEMILLA = 42  # La misma semilla y configuración repiten el experimento.
METODO_CRUCE = "sbx"
PROBABILIDAD_INTERCAMBIO = 0.5  # Solo para el cruce discreto uniforme.
ALFA_ARITMETICO = 0.5  # Mezcla fija: 0.5 da el punto medio de cada pareja.
ETA_SBX = 1.0  # Índice de distribución: el ejemplo del libro usa 1.
METODOS_CRUCE = ("un_punto", "uniforme", "aritmetico", "sbx")


def funcion_maximizar(valores):
    x = valores[0]
    return 20 + math.e - 20 * math.exp(-0.2 * abs(x)) - math.exp(math.cos(2 * math.pi * x))


def funcion_minimizar(valores):
    x = valores[0]
    return -abs(x * math.sin(math.sqrt(abs(x))))


def funcion_varias_variables(valores):
    return sum(-x * math.sin(math.sqrt(abs(x))) for x in valores)


def funcion_rastrigin(valores):
    """Mínimo 0 en el vector de ceros; tiene muchos mínimos locales."""
    return 10 * len(valores) + sum(x**2 - 10 * math.cos(2 * math.pi * x) for x in valores)


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
    Problema("Rastrigin · 10n + Σ (xi² − 10 cos(2πxi))", funcion_rastrigin, -5.12, 5.12, False, True),
)

@dataclass(frozen=True)
class Parametros:
    tamano_poblacion: int = TAMANO_POBLACION
    generaciones: int = NUMERO_GENERACIONES
    prob_cruce: float = PROBABILIDAD_CRUCE
    prob_mutacion: float = PROBABILIDAD_MUTACION
    elites: int = NUMERO_ELITES
    semilla: int = SEMILLA
    dimensiones: int = 1
    metodo_cruce: str = METODO_CRUCE
    prob_intercambio: float = PROBABILIDAD_INTERCAMBIO
    alfa_aritmetico: float = ALFA_ARITMETICO
    eta_sbx: float = ETA_SBX


@dataclass(frozen=True)
class Individuo:
    # Un cromosoma contiene n genes reales, por ejemplo (3.24, 2.71, 0.87).
    # No hay bits ni decodificación: el genotipo coincide con el fenotipo.
    genes: tuple[float, ...]
    objetivo: float  # Valor real de la función, no es el peso de la ruleta.

    @property
    def valores(self):
        """Permite reutilizar las gráficas del proyecto 1 sin duplicar datos."""
        return self.genes


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
    if not 0 <= p.prob_cruce <= 1 or not 0 <= p.prob_mutacion <= 1:
        raise ValueError("Las probabilidades deben estar entre 0 y 1.")
    if not 0 <= p.elites < p.tamano_poblacion:
        raise ValueError("Las élites deben estar entre 0 y población − 1.")
    if p.dimensiones < 1 or (not problema.varias_variables and p.dimensiones != 1):
        raise ValueError("Los ejemplos de una variable requieren dimensiones = 1.")
    if p.metodo_cruce not in METODOS_CRUCE:
        raise ValueError(f"El cruce debe ser uno de: {', '.join(METODOS_CRUCE)}.")
    if not 0 <= p.prob_intercambio <= 1 or not 0 <= p.alfa_aritmetico <= 1:
        raise ValueError("La probabilidad de intercambio y alfa deben estar entre 0 y 1.")
    if not math.isfinite(p.eta_sbx) or p.eta_sbx < 0:
        raise ValueError("Eta SBX debe ser un número finito ≥ 0.")


def inicializar_poblacion(problema, parametros, azar):
    """Paso 1: sortea cada gen uniformemente dentro de su intervalo.

    No se calcula una longitud de bits ni un error de discretización. Cada
    variable se almacena directamente como float (precisión finita de Python).
    """
    return [
        tuple(
            azar.uniform(problema.limite_inferior, problema.limite_superior)
            for _ in range(parametros.dimensiones)
        )
        for _ in range(parametros.tamano_poblacion)
    ]


def evaluar(poblacion, problema):
    """Pasos 2 y 7: calcula f directamente sobre el vector de genes reales."""
    evaluados = []
    for genes in poblacion:
        objetivo = problema.funcion(genes)
        if not math.isfinite(objetivo):
            raise ValueError("La función objetivo produjo un valor no finito.")
        evaluados.append(Individuo(genes, objetivo))
    return evaluados


def obtener_mejor(poblacion, problema):
    """Último paso: compara el objetivo original, incluyendo valores negativos."""
    elegir = max if problema.maximizar else min
    return elegir(poblacion, key=lambda individuo: individuo.objetivo)


def calcular_pesos(poblacion, problema):
    """Convierte el objetivo en pesos no negativos para la selección por ruleta.

    Maximización: f − mínimo. Minimización: máximo − f. Así, mejores
    objetivos tienen mayor probabilidad, incluso cuando todos son negativos.
    No usamos cmax*1.05 − f del texto: con cmax negativo puede dar pesos
    negativos. Una pequeña base permite también seleccionar al peor.
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
    return [padre.genes for padre in padres]


def cruce_un_punto(padre, madre, azar):
    """Corta ENTRE genes: no divide los bits internos de un número real.

    (1, 2 | 3) y (4, 5 | 6) producen (1, 2, 6) y (4, 5, 3).
    Con una sola variable no hay corte interior: se copian los padres.
    """
    if len(padre) < 2:
        return padre, madre
    corte = azar.randrange(1, len(padre))
    return padre[:corte] + madre[corte:], madre[:corte] + padre[corte:]


def cruce_uniforme(padre, madre, prob_intercambio, azar):
    """Cada gen se hereda de un padre u otro; no crea valores intermedios.

    El texto conserva los genes cuando el sorteo es menor que P_i. Aquí el
    parámetro se llama prob_intercambio y mide la probabilidad de CAMBIARLOS.
    Se usa un mismo sorteo para ambos hijos, que reciben genes complementarios.
    """
    hijo_a, hijo_b = [], []
    for a, b in zip(padre, madre):
        if azar.random() < prob_intercambio:
            a, b = b, a
        hijo_a.append(a)
        hijo_b.append(b)
    return tuple(hijo_a), tuple(hijo_b)


def cruce_aritmetico(padre, madre, alfa):
    """h1 = alfa*p1 + (1−alfa)*p2; h2 invierte los pesos.

    Alfa es configurable y se mantiene fijo por corrida. En [0, 1] los hijos
    quedan entre sus padres. Con alfa=0.5 ambos hijos son el mismo punto medio.
    Puede reducir la diversidad; la mutación uniforme introduce nuevos valores.
    """
    hijo_a = tuple(alfa * a + (1 - alfa) * b for a, b in zip(padre, madre))
    hijo_b = tuple((1 - alfa) * a + alfa * b for a, b in zip(padre, madre))
    return hijo_a, hijo_b


def cruce_sbx(padre, madre, eta, problema, azar):
    """Cruce binario simulado (SBX): usa reales, aunque su nombre diga binario.

    Se sortea u en [0, 1) y se calcula beta como en el libro. Usamos un beta
    por pareja para todos sus genes. Eta grande concentra beta cerca de 1;
    eta pequeña permite mayor dispersión. Beta>1 puede extrapolar fuera del
    intervalo de los padres e incluso del dominio. Para respetar el problema
    recortamos esos valores al límite más cercano (puede acumular extremos).
    """
    u = azar.random()  # Nunca es 1: evita dividir por cero en la segunda rama.
    exponente = 1 / (eta + 1)
    if u < 0.5:
        beta = (2 * u) ** exponente
    else:
        beta = (1 / (2 * (1 - u))) ** exponente

    def limitar(valor):
        return max(problema.limite_inferior, min(problema.limite_superior, valor))

    hijo_a, hijo_b = [], []
    for a, b in zip(padre, madre):
        medio = 0.5 * (a + b)
        diferencia = 0.5 * beta * (b - a)
        hijo_a.append(limitar(medio - diferencia))
        hijo_b.append(limitar(medio + diferencia))
    return tuple(hijo_a), tuple(hijo_b)


def reproducir(padres, problema, parametros, azar):
    """Paso 5: sortea el cruce por pareja y aplica el método seleccionado."""
    hijos = []
    for i in range(0, len(padres) - 1, 2):
        padre, madre = padres[i], padres[i + 1]
        if azar.random() >= parametros.prob_cruce:
            pareja = padre, madre
        elif parametros.metodo_cruce == "un_punto":
            pareja = cruce_un_punto(padre, madre, azar)
        elif parametros.metodo_cruce == "uniforme":
            pareja = cruce_uniforme(padre, madre, parametros.prob_intercambio, azar)
        elif parametros.metodo_cruce == "aritmetico":
            pareja = cruce_aritmetico(padre, madre, parametros.alfa_aritmetico)
        else:  # Validar parámetros garantiza que el método restante es SBX.
            pareja = cruce_sbx(padre, madre, parametros.eta_sbx, problema, azar)
        hijos.extend(pareja)
    # También admitimos tamaños impares: el último padre pasa sin cruce.
    if len(padres) % 2:
        hijos.append(padres[-1])
    return hijos


def mutar(poblacion, problema, prob_mutacion, azar):
    """Paso 6: sortea CADA gen; si muta, lo reemplaza por un real uniforme.

    0.05 significa 5 % por gen, no que mute exactamente 5 % de individuos.
    La mutación introduce variación que el cruce por sí solo no puede crear.
    No es un pequeño incremento ni un redondeo: puede saltar a cualquier punto
    del intervalo permitido, como indica la mutación uniforme del texto.
    """
    mutados = []
    for genes in poblacion:
        nuevos = []
        for gen in genes:
            if azar.random() < prob_mutacion:
                gen = azar.uniform(problema.limite_inferior, problema.limite_superior)
            nuevos.append(gen)
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
    poblacion = inicializar_poblacion(problema, parametros, azar)
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
        elites = [ind.genes for ind in ordenados[:parametros.elites]]
        cantidad_hijos = parametros.tamano_poblacion - len(elites)
        padres = seleccionar(poblacion, problema, cantidad_hijos, azar)
        hijos = reproducir(padres, problema, parametros, azar)
        hijos = mutar(hijos, problema, parametros.prob_mutacion, azar)
        poblacion = evaluar(elites + hijos, problema)
        numero += 1


if __name__ == "__main__":
    for estado in evolucionar():
        print(f"Generación {estado.numero:3}: mejor={estado.mejor.objetivo:.6f}, promedio={estado.promedio:.6f}")
    print("Mejor de la población final:", estado.mejor)
