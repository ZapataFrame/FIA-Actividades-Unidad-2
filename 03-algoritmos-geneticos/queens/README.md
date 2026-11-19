# Proyecto 3: n reinas mediante algoritmos genéticos

Proyecto didáctico de optimización combinatoria en Python, sin DEAP ni paquetes
externos. El algoritmo está en `algoritmo.py` y la interfaz Tkinter en
`interfaz.py`. Incluye comentarios sobre la representación y los operadores.

## Ejecutar

Desde el directorio `algoritmos_geneticos`:

```bash
cd proyect_3
source .venv/bin/activate
python interfaz.py
```

El venv normal ya está creado. Para recrearlo: `python -m venv .venv`.
No se necesita `pip install`: se utiliza Tkinter del Python del sistema,
disponible en este equipo. También puedes usar `./.venv/bin/python interfaz.py`.

## 1. Fundamento teórico breve

El problema consiste en colocar **n reinas en un tablero n×n sin que ninguna
ataque a otra**. Una reina ataca por su fila, columna y diagonales.
En optimización combinatoria se buscan configuraciones discretas; aquí se
busca una permutación de las filas que elimine los ataques diagonales.

El algoritmo genético mantiene una población de tableros, evalúa sus conflictos,
selecciona padres y genera nuevos tableros mediante cruce y mutación.
Se detiene cuando encuentra cero conflictos o llega al límite de generaciones.
Es una búsqueda aleatoria: una corrida puede agotar el límite sin resolverlo.

### Representación: columna fija y fila variable

Tu interpretación de utilizar un vector de posiciones es correcta. La
precisión importante del libro es que **la columna está dada por la posición
del gen y su valor indica la fila**, en lugar de guardar un identificador
arbitrario de cualquiera de las n² casillas.

```text
Columna:        1  2  3  4
Vector de filas (2, 4, 1, 3)
Reinas:        (1,2), (2,4), (3,1), (4,3)
                columna, fila
```

El vector es una **permutación de 1 a n**: no repite filas. Cada columna tiene
exactamente una reina y cada fila también. Por construcción se eliminan los
ataques de fila y columna; queda evaluar los de diagonal. El espacio de búsqueda
tiene n! permutaciones, pero solo algunas representan soluciones sin ataques.

En Python, los índices son 0…n−1 y los valores de los genes son 1…n. La interfaz
muestra columnas y filas desde 1, con la fila 1 en la parte superior.

### Métrica: pares de reinas que se atacan

Dos reinas en columnas i y j comparten diagonal si:

```python
abs(genes[i] - genes[j]) == abs(i - j)
```

Se recorren solo parejas con `i < j` para contar cada ataque una vez:

```python
for i in range(n):
    for j in range(i + 1, n):
        if abs(genes[i] - genes[j]) == j - i:
            # Esta pareja aporta una colisión.
            ...
```

**Se minimiza el número de pares**, no el número de reinas marcadas en rojo.
Una misma reina puede participar en varias parejas. Con n=4, el vector
`(1, 2, 3, 4)` coloca todas las reinas en la misma diagonal: hay 6 parejas
en conflicto, aunque solo hay 4 reinas. `(2, 4, 1, 3)` tiene 0 conflictos.
El máximo posible es `n*(n−1)/2`; el objetivo es cero.

## 2. Pasos del programa

Empieza leyendo `evolucionar()` y sigue sus llamadas:

| Paso | Función | Qué hace |
|---|---|---|
| Inicializar | `inicializar_poblacion()` | Genera permutaciones aleatorias con `random.sample()` |
| Evaluar | `evaluar()` | Valida las permutaciones y cuenta pares diagonales |
| Seleccionar | `seleccionar()` | Elige padres por ruleta con reemplazo |
| Cruzar | `reproducir()` y `cruce_orden()` | Genera hijos mediante cruce por orden, OX |
| Mutar | `mutar()` | Intercambia dos posiciones de un individuo |
| Reevaluar | `evaluar()` | Calcula los conflictos de la nueva población |
| Parar | `criterio_parada()` | Detecta una solución o el límite de generaciones |
| Obtener resultado | `obtener_mejor()` | Elige el individuo con menos conflictos |

### Selección por ruleta

Cada individuo recibe peso `1/(1+colisiones)`. Un tablero con cero conflictos
tiene peso 1; con un conflicto, 0.5; con tres, 0.25. Así se favorecen tableros
con menos ataques sin dividir por cero. El objetivo sigue siendo el número
de conflictos; el peso solo determina las probabilidades de selección.

Se utiliza `random.choices(..., weights=pesos, k=cantidad)`: cada padre puede
salir varias veces y todos tienen alguna posibilidad. Dos tableros iguales
en la población son válidos; lo que no puede repetirse es una fila dentro
del mismo tablero.

### Cruce por orden (OX)

Se elige OX de las capturas porque mantiene las permutaciones:

1. Elegir dos cortes entre genes: un tramo `[inicio:fin]`.
2. Copiar ese tramo del primer padre al hijo en las mismas posiciones.
3. Recorrer el segundo padre desde `fin`, volviendo al principio cuando sea
   necesario, y omitir los valores ya copiados.
4. Llenar los huecos en ese orden, también comenzando desde `fin`.
5. Repetir intercambiando los papeles de los padres para obtener el otro hijo.

Ejemplo del libro, con índices de corte 3 y 6:

```text
Padre:  (1, 3, 6 | 4, 2, 5 | 8, 7)
Madre:  (2, 7, 8 | 3, 1, 5 | 4, 6)
Hijo 1: (8, 3, 1 | 4, 2, 5 | 6, 7)
Hijo 2: (6, 4, 2 | 3, 1, 5 | 8, 7)
```

Un cruce monopunto clásico puede duplicar filas. Por ejemplo, cruzar
`(1,2 | 3,4)` con `(3,4 | 1,2)` produciría `(1,2,1,2)`, que no es una
permutación. OX conserva la validez sin una reparación posterior.
La probabilidad de cruce se sortea por pareja; un padre sobrante de una
cantidad impar pasa sin cruce y todavía puede mutar.

### Mutación por intercambio

Se sortea si un individuo muta. Si ocurre, se eligen dos columnas distintas
y se intercambian sus filas:

```text
(2, 4, 1, 3) → intercambiar columnas 1 y 3 → (1, 4, 2, 3)
```

Puede mejorar o empeorar los conflictos, pero mantiene todas las filas sin
repetición. Asignar una fila aleatoria directamente a un gen podría romper
esta propiedad. A diferencia de los proyectos anteriores, la probabilidad
se aplica **por individuo**, con un intercambio por cada individuo que muta.

### Elitismo y estado de cada generación

Se reservan los mejores antes del cruce y la mutación, se generan los hijos
restantes y se agregan las élites intactas. La población conserva su tamaño.
Con al menos una élite, el mínimo de conflictos no empeora entre generaciones.
`elites=0` permite estudiar la búsqueda sin esa protección.

El mejor histórico es un registro del mejor observado. Guardarlo no lo
reintroduce en la población. El resultado final es el mejor de la población
actual al detenerse. Los individuos son inmutables y los operadores crean
copias: seleccionar varias veces a un padre no permite modificarlo por accidente.

## 3. Parámetros editables

Se pueden cambiar desde la interfaz o las constantes de `algoritmo.py`.

| Parámetro | Valor inicial | Significado |
|---|---:|---|
| `n` | 8 | Número de reinas y lado del tablero |
| `tamano_poblacion` | 80 | Individuos por generación |
| `generaciones` | 500 | Máximo de generaciones posteriores a la inicial |
| `prob_cruce` | 0.9 | Probabilidad de aplicar OX a una pareja |
| `prob_mutacion` | 0.2 | Probabilidad de un intercambio por individuo |
| `elites` | 2 | Individuos preservados sin modificarlos |
| `semilla` | 42 | Permite repetir la misma corrida |
| Pausa de interfaz | 150 ms | Tiempo entre pasos automáticos |

La interfaz admite n=1…32, población 2…1000 y límite 0…5000 para mantener
legibles el tablero y la tabla. Las élites deben ser menores que la población.
La evaluación de un individuo cuesta O(n²); una generación evalúa la población
completa, incluidas las élites.

N=1 tiene solución inmediata. N=2 y n=3 no tienen solución: se permite ejecutar
estos casos para ilustrar una búsqueda que llega al límite. Para n≥4 existen
soluciones, pero el algoritmo genético no garantiza encontrarlas en una corrida.
También puede encontrar una solución en la población inicial, generación 0.

## 4. Usar la interfaz

1. Configura los parámetros y pulsa **Reiniciar**. Los cambios no alteran una
   corrida ya iniciada hasta que la reinicies.
2. Pulsa **Siguiente generación** para avanzar manualmente, o **Reproducir**
   para animar. **Pausar** permite examinar la población.
3. Selecciona cualquier fila de la tabla para ver su tablero. Por defecto,
   cada generación selecciona el mejor individuo actual.
4. En el tablero, las reinas rojas participan en ataques diagonales y las
   líneas rojas indican las parejas; las azules no participan en ataques.
   La letra R representa una reina.
5. La gráfica muestra el promedio, el mejor actual y el mejor histórico de
   pares en conflicto. Menor es mejor; la media puede subir aunque la élite
   mantenga un buen individuo.

La ventana usa `after()` para avanzar sin bloquear los botones. El algoritmo
usa `yield` para entregar una instantánea por generación y conserva su estado
hasta que la interfaz pide la siguiente. El mensaje final diferencia una
solución comprobada de un límite alcanzado sin solución.

## 5. Ejecución por consola y comprobaciones

```bash
python algoritmo.py
python -m unittest -v
```

También puedes ejecutar este ejemplo desde `proyect_3`:

```python
from algoritmo import Parametros, evolucionar, obtener_colisiones

parametros = Parametros(n=8, tamano_poblacion=80, semilla=42)
for estado in evolucionar(parametros):
    print(estado.numero, estado.mejor.colisiones)

print("Filas por columna:", estado.mejor.genes)
print("Pares en conflicto:", obtener_colisiones(estado.mejor.genes))
```

Con los parámetros iniciales y semilla 42 se encontró en la **generación 7**:

```text
(7, 5, 3, 1, 6, 8, 2, 4) → 0 pares en conflicto
```

Se comprobaron doce pruebas del algoritmo, incluido el ejemplo OX del libro
y 5760 cruces que cubren todos los padres y cortes de permutaciones de n=4.
Se verificó la interfaz con selección de individuos, avance manual, reproducción,
pausa, parada y validación de parámetros en los casos n=1, 2, 3 y 8.
También se ejecutaron diez semillas (0…9) por caso:

| N | Corridas con solución | Generación de parada observada |
|---|---|---|
| 1 | 10/10 | 0 |
| 2 | 0/10 | 500, por límite |
| 3 | 0/10 | 500, por límite |
| 4 | 10/10 | 0 |
| 8 | 10/10 | Entre 1 y 9 |
| 12 | 10/10 | Entre 9 y 143 |

Estos son resultados de las semillas probadas, no una garantía para otras
corridas. Una solución se verifica directamente contando sus pares de ataque;
un fracaso de la búsqueda no demuestra que el problema carezca de solución.

## 6. Ejercicios cortos de estudio

1. Cuenta los pares en conflicto de `(1,2,3,4)`. Deben ser 6. Explica por qué
   contar solo reinas en rojo daría una métrica diferente.
2. Sigue el ejemplo OX y comprueba que ambos hijos contienen los números 1…8
   exactamente una vez. Verifica dónde se copió el tramo y cómo se llenó el resto.
3. Prueba n=8 con élites 0 y 2 manteniendo los demás parámetros y la semilla.
   Observa si el mejor actual se pierde. Repite con varias semillas.
4. Compara mutación 0 y 0.2. Observa conflictos e individuos distintos para
   detectar estancamiento. El comportamiento depende también del cruce y la selección.
