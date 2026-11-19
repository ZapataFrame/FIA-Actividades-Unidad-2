# Proyecto 2: optimización con genes reales

Algoritmo genético sencillo en Python, sin DEAP ni paquetes externos. Adapta el
ciclo, la selección por ruleta, el elitismo y la interfaz del proyecto 1.
Cada paso se mantiene en una función dentro de `algoritmo.py`.

## Ejecutar

Desde el directorio `algoritmos_geneticos`:

```bash
cd proyect_2
source .venv/bin/activate
python interfaz.py
```

El venv ya está creado. Para recrearlo utiliza `python -m venv .venv`.
No necesitas instalar paquetes con pip; se utiliza Tkinter del Python del
sistema, disponible en este equipo. Alternativa: `./.venv/bin/python interfaz.py`.

Elige una función y un cruce, modifica los parámetros y pulsa **Reiniciar**.
**Siguiente generación** permite estudiar un paso; **Reproducir** y **Pausar**
controlan la animación. Los cambios se aplican al reiniciar la corrida.
Los parámetros exclusivos de otros cruces aparecen deshabilitados.

La tabla muestra el vector de genes de cada individuo y su objetivo original.
Con una variable, la gráfica izquierda muestra la función y la población.
Con varias, muestra **x₁ frente al objetivo completo**: una proyección de los
individuos, no una curva de una función unidimensional. Las demás coordenadas
están en la tabla, con desplazamiento horizontal para vectores largos.
La gráfica derecha muestra el promedio, el mejor actual y el mejor histórico.

La generación 0 es la población inicial. Con 100 generaciones se muestran
101 poblaciones. La interfaz admite población 2–2000, generaciones 0–5000 y
1–10 variables. Los problemas unidimensionales requieren una variable;
Rastrigin propone diez al seleccionarlo, como el ejemplo del libro.

## Diferencias respecto al proyecto 1

| Paso | Proyecto 1 | Proyecto 2 |
|---|---|---|
| Representación | Bits por variable | Vector de números reales |
| Inicialización | Bits aleatorios | Valores uniformes en el intervalo |
| Evaluación | Decodificar y evaluar | Evaluar directamente los genes |
| Cruce | Monopunto entre bits | Monopunto, uniforme, aritmético o SBX |
| Mutación | Invertir un bit | Reemplazar un gen por un real aleatorio |
| Precisión | Control de discretización | Sin rejilla binaria; utiliza `float` |

Por ejemplo, `(3.24, 2.71, 0.87)` es un cromosoma de tres genes. El genotipo
y el fenotipo coinciden. No se redondean los genes durante la evolución;
los seis decimales de la tabla solo son un formato de presentación.

La selección por ruleta conserva los pesos positivos del proyecto 1:
`f − mínimo + base` para maximizar y `máximo − f + base` para minimizar.
`base = 0.01*(máximo−mínimo)` permite seleccionar también al peor. Si todos
empatan, la ruleta es uniforme. Los padres se sortean con reemplazo y pueden
repetirse. Las gráficas muestran `f`, no los pesos de la ruleta.

## Cruces

La probabilidad de cruce se sortea **por pareja**. Los parámetros de cada
operador son diferentes de esta probabilidad:

- **Un punto:** intercambia segmentos de genes completos tras un corte
  interior. `(1, 2 | 3)` y `(4, 5 | 6)` producen `(1, 2, 6)` y `(4, 5, 3)`.
  Con una sola variable copia los padres porque no existe un corte interior.
- **Uniforme:** para cada gen sortea si se intercambian los valores de los
  padres. `prob_intercambio=0.5` da 50 % de probabilidad de intercambiar cada
  posición. Los dos hijos reciben valores complementarios. El pseudocódigo
  del libro llama P_i a la probabilidad de conservarlos; aquí el nombre
  describe la probabilidad de intercambiarlos. Solo hereda valores existentes.
- **Aritmético:** `h1 = alfa*p1 + (1−alfa)*p2` y
  `h2 = (1−alfa)*p1 + alfa*p2`. Alfa se mantiene fijo por corrida y pertenece
  a `[0, 1]`. Con 0.5 los hijos son iguales al punto medio. Puede crear valores
  nuevos, pero reduce diversidad y permanece entre sus padres.
- **SBX:** utiliza `u` aleatorio en `[0, 1)` y
  `beta = (2u)^(1/(eta+1))` si `u<0.5`, o
  `beta = (1/(2(1−u)))^(1/(eta+1))` en la otra rama.
  Los hijos son `0.5*(p1+p2 − beta*(p2−p1))` y
  `0.5*(p1+p2 + beta*(p2−p1))`. Se utiliza un mismo beta por pareja,
  como en el pseudocódigo. Eta=1 reproduce el índice del ejemplo. Eta mayor
  concentra beta cerca de 1; eta menor permite mayor dispersión.

SBX puede extrapolar fuera del dominio. Esta implementación **recorta al
límite más cercano** para mantener individuos válidos. Es una decisión
explícita y sencilla; puede acumular individuos en los extremos. No utiliza
la variante SBX acotada con una distribución diferente. Si sobra un padre
en una población impar pasa sin cruce, pero puede mutar.

## Mutación, elitismo y parada

La mutación uniforme sortea cada gen. Si se activa, lo sustituye por un real
uniforme en el intervalo del problema. `prob_mutacion=0.05` significa 5 % por
gen, no por individuo y no una cantidad exacta de mutaciones. Tampoco es un
incremento pequeño: puede saltar a cualquier valor del dominio.

Las élites pasan intactas y no se cruzan ni mutan. `elites=0` desactiva el
mecanismo. El mejor histórico solo registra resultados: no modifica la
población. El resultado final es el mejor individuo de la última población.
El criterio de parada es el límite de generaciones; no se garantiza encontrar
el óptimo global. La misma configuración y semilla repiten los resultados.

## Funciones incluidas

| Función | Objetivo | Intervalo por variable | Referencia |
|---|---|---|---|
| `20 + e − 20 exp(−0.2\|x\|) − exp(cos(2πx))` | Máximo | `[0,32]` | ≈22.3136 cerca de 31.5005 |
| `−\|x sen(√\|x\|)\|` | Mínimo | `[−250,250]` | ≈−201.843 cerca de ±203.814 |
| `Σ −xi sen(√\|xi\|)` | Mínimo | `[0,100]` | ≈−n·63.63498, cada xi≈65.54785 |
| Rastrigin: `10n + Σ (xi² − 10 cos(2πxi))` | Mínimo | `[−5.12,5.12]` | 0 en el vector de ceros |

Se conservan los tres ejemplos implementados en el proyecto 1 y se añade
Rastrigin de las nuevas imágenes. Todas las variables comparten intervalo.
Las referencias no se introducen en la población ni se usan para parar.
Las funciones trigonométricas usan radianes.

## Archivos y experimentos

- `algoritmo.py`: constantes editables, problemas, operadores y `evolucionar()`.
- `interfaz.py`: ventana, tabla y gráficas; adapta la interfaz anterior.
- `estudio.py`: varía parámetros y compara la representación binaria con la real.
- `test_algoritmo.py`: pruebas de los cuatro cruces y del ciclo completo.

```bash
python algoritmo.py         # Ejecución por consola.
python -m unittest -v       # Pruebas del proyecto 2.
python estudio.py           # Regenera los dos CSV junto al script.
```

La interfaz y el algoritmo funcionan de forma independiente del proyecto 1.
La comparación de `estudio.py` importa su algoritmo binario desde la carpeta
hermana `proyect_1`, sin modificarlo. Mantén ambas carpetas juntas para ella.

El estudio usa Rastrigin con tres variables, población 60, 100 generaciones,
cruce 0.7, mutación 0.05 por gen, una élite, SBX eta=1 y semillas 0–9.
Cada comparación cambia un parámetro y mantiene los demás. `SEMILLAS`,
`PARAMETROS_BASE`, `PROBLEMA` y `VARIANTES` se pueden editar. Para estudiar
alfa o el intercambio uniforme, elige primero su método como base y luego
varía únicamente su parámetro correspondiente.

## Resultados obtenidos

Se ejecutaron **240 corridas** del estudio. El detalle está en
`resultados_estudio.csv`. Al minimizar Rastrigin, menor es mejor:

| Cruce | Media del mejor final | Desviación típica |
|---|---:|---:|
| Un punto | 0.493203 | 0.435377 |
| Uniforme | 0.504896 | 0.402747 |
| Aritmético, alfa=0.5 | 0.092300 | 0.102135 |
| SBX, eta=1 | 0.071258 | 0.147159 |

Con SBX, sin elitismo la media fue 5.125369; con una élite, 0.071258.
Sin mutación fue 2.786116; con mutación 0.05, 0.071258. Aumentar a
200 generaciones dio 0.001414. Estos resultados muestran el efecto de los
parámetros en este experimento; no establecen una configuración universal.
La generación registrada para el mejor histórico no acredita haber alcanzado
el óptimo matemático.

Se ejecutaron además **80 corridas** comparativas, diez por problema y
representación, con tres variables en los problemas multidimensionales:

| Problema | Media binaria | Media real |
|---|---:|---:|
| Máximo | 22.313676 | 22.313672 |
| Mínimo | −201.837166 | −201.843218 |
| Suma de varias variables | −189.118114 | −190.902135 |
| Rastrigin | 2.048657 | 0.071258 |

La comparación mantiene objetivos, dominios, dimensiones, población,
generaciones, elitismo, probabilidad de cruce y conjunto de semillas.
La representación binaria usa precisión 0.001 y cruce monopunto; la real usa
SBX. Para igualar la probabilidad de alguna mutación por variable se calcula
`p_bit = 1 − (1−p_gen)^(1/L)`. Esto no iguala la magnitud de los cambios ni
la población inicial: las mismas semillas alimentan procesos distintos.
Por tanto, se comparan algoritmos completos, no solo representaciones aisladas.

`comparacion_representaciones.csv` incluye objetivos, tiempos y número de
evaluaciones. Cada corrida evalúa 6060 individuos, incluidas las élites
reevaluadas. En esta ejecución la versión real tardó menos para los cuatro
problemas; los tiempos dependen del equipo, la carga y el orden de ejecución.
El caso de maximización muestra que la representación real no siempre produce
un mejor objetivo que la binaria.

Pasaron **11 pruebas** y se verificó la ventana con los cuatro problemas y
los cuatro cruces, avance manual, reproducción, pausa, parada y validación.

Ejercicios: compara un punto y SBX con una sola variable; observa cómo
aritmético con alfa=0.5 crea hijos iguales; cambia eta de 1 a 20; compara
mutación 0 y 0.05. Mantén los demás parámetros y repite con varias semillas.
