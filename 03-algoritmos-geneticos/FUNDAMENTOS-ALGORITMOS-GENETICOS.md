# Algoritmos genéticos: fundamentos y puntos cruciales en Python

Guía breve para repasar lo visto en clase y entender los proyectos 1 y 2.
La teoría se resume primero; después se explica el código que conviene dominar.

## 1. Teoría en pocas palabras

Un algoritmo genético busca buenas soluciones mediante una **población de
candidatos**. Evalúa su calidad, selecciona padres y genera nuevos individuos
con cruce y mutación. Repite el proceso durante varias generaciones.

| Concepto | Significado en estos proyectos |
|---|---|
| Individuo | Una solución candidata: uno o varios valores de x |
| Gen | Una unidad de la representación: un bit o una variable real |
| Cromosoma | La estructura que agrupa los genes |
| Genotipo | La representación almacenada: bits o números reales |
| Fenotipo | Los valores de las variables que se evalúan |
| Función objetivo | La función matemática que queremos maximizar o minimizar |
| Peso de selección | Valor utilizado para dar probabilidad a un individuo en la ruleta |
| Generación | Una población en un momento de la evolución |
| Elitismo | Conservar algunos de los mejores individuos sin modificarlos |

La **selección** favorece buenas soluciones; el **cruce** combina información
de los padres; la **mutación** introduce variación. Se necesita equilibrar la
exploración de nuevas soluciones con el aprovechamiento de las encontradas.
Si la población pierde diversidad, puede estancarse en un óptimo local.

El criterio de parada puede ser un número de generaciones, un objetivo
alcanzado o un periodo sin mejora. Aquí se utiliza el número de generaciones.
**Terminar no demuestra que se haya encontrado el óptimo global.**

```text
Inicializar → Evaluar → [Seleccionar → Cruzar → Mutar → Evaluar] → Mejor final
                              repetir hasta el criterio de parada
```

## 2. Representar una solución correctamente

### Proyecto 1: representación binaria

Cada variable tiene su cadena de bits. Para dos variables, un genotipo podría
ser `("0101", "1100")`. Primero se convierte cada cadena a entero y luego se
mapea al intervalo permitido:

```python
entero = int(cromosoma, 2)
fraccion = entero / (2 ** len(cromosoma) - 1)
x = limite_inferior + fraccion * (limite_superior - limite_inferior)
```

Ejemplo: `"0101"` vale 5; en `[0, 10]`, con cuatro bits,
`x = 0 + 5/15 * 10 ≈ 3.333333`.

La longitud L debe cumplir:

```text
separación = (límite_superior − límite_inferior) / (2^L − 1) ≤ precisión
```

Para `[0, 32]` y precisión `0.001`, se necesitan 15 bits. Esto controla la
separación entre valores representables, **no el error del resultado frente al
óptimo**. El algoritmo todavía debe encontrar una buena combinación de bits.

### Proyecto 2: representación real

El cromosoma es directamente una tupla de valores:

```python
genes = (3.24, 2.71, 0.87)
objetivo = problema.funcion(genes)
```

No hay decodificación: genotipo y fenotipo coinciden. Se utiliza `float`, con
precisión finita; imprimir seis decimales no significa redondear los genes.

**La representación determina cómo deben operar el cruce y la mutación.**
En binario se modifican bits; en real se heredan, mezclan o reemplazan valores.

## 3. Separar objetivo y peso de selección

Evaluar consiste en calcular la función objetivo para cada individuo. Buscar
el mejor significa comparar ese resultado con `max()` o `min()`:

```python
elegir = max if problema.maximizar else min
mejor = elegir(poblacion, key=lambda individuo: individuo.objetivo)
```

En una minimización, `−8` es mejor que `−3`. Sin embargo, los pesos de una
ruleta deben ser no negativos: no se pueden utilizar directamente objetivos
negativos como probabilidades.

Los proyectos calculan los pesos así:

```python
amplitud = maximo - minimo
base = amplitud * 0.01

# Maximizar: un objetivo mayor debe recibir más peso.
pesos = [valor - minimo + base for valor in objetivos]

# Minimizar: un objetivo menor debe recibir más peso.
pesos = [maximo - valor + base for valor in objetivos]
```

Estas son alternativas según el problema. Para minimizar los objetivos
`[−8, −3, −1]`, los pesos son `[7.07, 2.07, 0.07]`. Se favorece a `−8`, pero
todos pueden ser seleccionados. Si todos los objetivos son iguales, se asigna
peso 1 a cada individuo para obtener selección uniforme.

La ruleta se implementa con:

```python
padres = azar.choices(poblacion, weights=pesos, k=cantidad_hijos)
```

`choices()` selecciona **con reemplazo**: un padre puede salir varias veces.
No hace falta normalizar los pesos; Python utiliza sus proporciones. Elegir
padres tampoco significa conservarlos intactos: sus hijos pueden ser peores.

## 4. Entender qué hace cada cruce

La probabilidad de cruce se sortea por pareja:

```python
if azar.random() < parametros.prob_cruce:
    # Aplicar el operador elegido a esta pareja.
    ...
else:
    # Los padres pasan como hijos; todavía pueden mutar.
    ...
```

`azar.random()` produce un número en `[0, 1)`. Una probabilidad de 0.7 significa
70 % por pareja; no obliga a cruzar exactamente el 70 % en una generación.

| Operador | Acción | Punto crucial |
|---|---|---|
| Monopunto binario | Intercambia segmentos de bits | Puede crear otros valores de x incluso con una variable |
| Un punto real | Intercambia segmentos de variables completas | Con una variable no hay corte interior |
| Uniforme real | Decide por posición qué valores intercambiar | Hereda valores existentes; no calcula valores intermedios |
| Aritmético | Mezcla valores de los padres | Con alfa=0.5 ambos hijos son el mismo punto medio |
| SBX | Calcula hijos usando una dispersión aleatoria | Puede extrapolar fuera del dominio |

**Un punto**, para cromosomas reales:

```python
corte = azar.randrange(1, len(padre))
hijo_a = padre[:corte] + madre[corte:]
hijo_b = madre[:corte] + padre[corte:]
```

Antes hay que comprobar que `len(padre) > 1`. El corte se hace entre genes:
`(1, 2 | 3)` y `(4, 5 | 6)` producen `(1, 2, 6)` y `(4, 5, 3)`.

**Aritmético**, para cada par de valores a y b:

```python
hijo_a = alfa * a + (1 - alfa) * b
hijo_b = (1 - alfa) * a + alfa * b
```

Con a=2, b=6 y alfa=0.25, los hijos son 5 y 3. Para alfa entre 0 y 1 permanecen
entre los padres; esto permite crear valores nuevos, pero puede reducir diversidad.

**SBX**, el cálculo que conviene identificar:

```python
u = azar.random()
exponente = 1 / (eta + 1)
if u < 0.5:
    beta = (2 * u) ** exponente
else:
    beta = (1 / (2 * (1 - u))) ** exponente

medio = 0.5 * (a + b)
diferencia = 0.5 * beta * (b - a)
hijo_a = medio - diferencia
hijo_b = medio + diferencia
```

Beta menor que 1 produce hijos entre sus padres; mayor que 1 extrapola.
Eta mayor concentra beta cerca de 1. En el proyecto 2 se usa un beta por pareja
y se recorta cualquier resultado fuera del dominio:

```python
valor = max(limite_inferior, min(limite_superior, valor))
```

El recorte mantiene soluciones válidas, pero puede acumularlas en los extremos.

## 5. Aplicar la mutación en la unidad correcta

**Binaria:** se sortea cada bit; si muta, se invierte.

```python
if azar.random() < prob_mutacion:
    bit = "1" if bit == "0" else "0"
```

**Real uniforme:** se sortea cada gen; si muta, se reemplaza por un valor del dominio.

```python
if azar.random() < prob_mutacion:
    gen = azar.uniform(limite_inferior, limite_superior)
```

La mutación uniforme puede dar un salto grande. No equivale a sumar un pequeño
ruido. Una probabilidad de 0.05 significa 5 % **por gen**. Con diez genes,
la probabilidad de mutar al menos uno es `1 − (1−0.05)^10 ≈ 40.1 %`.

Por eso, usar la misma cifra por bit y por variable real no equivale al mismo
efecto. En el estudio se iguala la probabilidad de alguna mutación por variable,
aunque eso tampoco iguala la magnitud de los cambios.

## 6. Construir la siguiente población sin perder las élites

Este fragmento resume el reemplazo del proyecto 2:

```python
ordenados = sorted(
    poblacion,
    key=lambda ind: ind.objetivo,
    reverse=problema.maximizar,
)
elites = [ind.genes for ind in ordenados[:parametros.elites]]
cantidad_hijos = parametros.tamano_poblacion - len(elites)

padres = seleccionar(poblacion, problema, cantidad_hijos, azar)
hijos = reproducir(padres, problema, parametros, azar)
hijos = mutar(hijos, problema, parametros.prob_mutacion, azar)
poblacion = evaluar(elites + hijos, problema)
```

Se reservan las élites **antes** del cruce y la mutación; luego se agregan
intactas. El tamaño final se mantiene. Si sobra un padre sin pareja, pasa sin
cruce y puede mutar.

Conviene distinguir:

- **Mejor actual:** pertenece a la población de esa generación.
- **Mejor histórico:** el mejor observado durante toda la corrida.
- **Élite:** individuo preservado para que participe en la siguiente población.

Guardar el mejor histórico no lo preserva en la población. Con al menos una
élite, el mejor objetivo actual no empeora; con cero élites puede perderse.

## 7. Detalles de Python que evitan errores

- **`random.Random(semilla)`** crea un generador local reproducible. Pásalo a
  todas las funciones aleatorias. La misma semilla entre los dos proyectos
  no produce necesariamente la misma población: consumen el azar de otra forma.
- **Tuplas y `@dataclass(frozen=True)`** mantienen inmutables los individuos.
  Los operadores construyen hijos nuevos, evitando modificar padres compartidos
  cuando la ruleta selecciona al mismo individuo varias veces.
- **`yield`** en `evolucionar()` entrega una generación y conserva el estado
  para continuar con `next()`. Crear el generador no ejecuta todavía el ciclo.
- **`after()` de Tkinter** programa el siguiente paso y permite procesar botones
  entre generaciones. Un bucle completo dentro del botón bloquearía la ventana.
- **Validación:** probabilidades entre 0 y 1, élites menores que la población,
  dimensiones compatibles y objetivos finitos. Validar evita resultados engañosos.

## 8. Ejemplo ejecutable con el código existente

Los bloques anteriores ilustran fragmentos de funciones. Este bloque sí es
completo: ejecútalo desde la raíz `algoritmos_geneticos` con el Python del venv
del proyecto 2, por ejemplo en el intérprete `proyect_2/.venv/bin/python`.

```python
from proyect_2.algoritmo import PROBLEMAS, Parametros, evolucionar

problema = PROBLEMAS[3]  # Rastrigin: minimizar, óptimo conocido en ceros.
parametros = Parametros(
    tamano_poblacion=60,
    generaciones=100,
    dimensiones=3,
    prob_cruce=0.7,
    prob_mutacion=0.05,
    elites=1,
    metodo_cruce="sbx",
    eta_sbx=1,
    semilla=42,
)

for estado in evolucionar(problema, parametros):
    if estado.numero % 20 == 0:
        print(estado.numero, estado.mejor.objetivo, estado.promedio)

print("Mejor final:", estado.mejor.genes, estado.mejor.objetivo)
```

Para leer la implementación, comienza por `evolucionar()` y sigue sus llamadas:

- [Proyecto 1: algoritmo binario](/home/zapata/Documents/Uni/Fundamentos_IA/Unidad_2/algoritmos_geneticos/proyect_1/algoritmo.py).
- [Proyecto 2: algoritmo real](/home/zapata/Documents/Uni/Fundamentos_IA/Unidad_2/algoritmos_geneticos/proyect_2/algoritmo.py).

## 9. Interpretar resultados y comprobar que entendiste

Observa el mejor **y** el promedio. Un buen individuo con un promedio pobre
puede significar que gran parte de la población sigue lejos de él. Cuenta
también individuos distintos para detectar pérdida de diversidad.

Compara un parámetro a la vez y repite con varias semillas. Más generaciones
o más población aumentan las evaluaciones; menos generaciones no siempre
significa menor tiempo. Para varias variables, la gráfica de x₁ frente a f
solo es una proyección y no permite ver todo el espacio de búsqueda.

Tres comprobaciones rápidas:

1. Minimiza `[−8, −3, −1]`: debe ganar `−8` y recibir mayor peso de ruleta.
2. Cruza 2 y 6 con alfa=0.5: ambos hijos deben valer 4. Explica por qué esto
   puede reducir diversidad.
3. Desactiva elitismo y mutación en la interfaz: observa si se pierde el mejor
   actual o se estanca la población. El histórico puede mantenerse aunque el
   mejor actual empeore; el comportamiento concreto depende de la semilla.
