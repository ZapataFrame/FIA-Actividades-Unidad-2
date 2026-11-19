# Algoritmo genético sencillo

Python, sin DEAP ni paquetes externos. Usa un entorno virtual normal y Tkinter
para observar cada generación. Se implementan **los tres ejemplos elegidos en
el apéndice C++** de las imágenes; el resto de las funciones propuestas en las
primeras páginas no está incluido en esta versión.

## Ejecutar

Desde el directorio `algoritmos_geneticos`:

```bash
cd proyect_1
python -m venv .venv  # El entorno ya está creado; este paso sirve para recrearlo.
source .venv/bin/activate
python interfaz.py
```

No necesitas `pip install`. Tkinter debe estar disponible en el Python del
sistema (lo está en este equipo). También puedes ejecutar sin activar el venv:
`./.venv/bin/python interfaz.py`.

## Usar la interfaz

1. Elige el problema y configura población, generaciones, precisión, cruce,
   mutación, élites y semilla. En varias variables puedes cambiar su cantidad.
2. Pulsa **Reiniciar** para aplicar los parámetros. Aparece la población inicial,
   llamada generación 0.
3. Pulsa **Siguiente generación** para inspeccionar un paso o **Reproducir** para
   animar la evolución. **Pausar** permite detenerla y examinar los individuos.
4. Compara los bits, los valores reales y `f(x)` en la tabla. La fila del mejor
   individuo está resaltada. Los individuos repetidos siguen ocupando plazas.

La gráfica izquierda muestra la función y los individuos para una variable.
Con varias variables representa **x₁ frente al objetivo completo**: es una
proyección de la población, no la gráfica de una función de una sola variable.
La tabla conserva todas las coordenadas. La gráfica derecha muestra el objetivo
medio, el mejor actual y el mejor histórico desde la generación 0.

Los cambios en los campos se aplican al reiniciar; una corrida en curso conserva
su configuración. La interfaz admite 2–2000 individuos, 0–5000 generaciones,
1–10 variables y precisión ≥ 1e-12 para mantener razonable su uso interactivo.

## Leer el código

- `algoritmo.py`: constantes, problemas y funciones de cada paso. Empieza por
  `evolucionar()` para identificar el pseudocódigo y luego lee sus operadores.
- `interfaz.py`: ventana, controles, tabla y gráficas dibujadas con Canvas.
- `estudio.py`: compara un parámetro a la vez y escribe los resultados en CSV.
- `test_algoritmo.py`: pruebas de los operadores y propiedades del ciclo.

El flujo es: **inicializar → evaluar → [seleccionar → reproducir → mutar →
evaluar] → obtener el mejor**. El criterio de parada es el límite de
generaciones. Una ejecución con 100 generaciones muestra 101 poblaciones,
porque también muestra la inicial.

**Genotipo y fenotipo.** Cada variable tiene una cadena de bits. Si la cadena
vale `d` como entero, se convierte en `a + d*(b-a)/(2**L-1)`. Para `[0, 32]`
y precisión `0.001`, se necesitan 15 bits. La precisión limita la separación
entre puntos representables; **no garantiza un error máximo respecto al óptimo**.

**Evaluación y selección.** El objetivo es el resultado original de la función.
La ruleta utiliza pesos positivos calculados a partir de la población actual:
`f - mínimo + base` para maximizar y `máximo - f + base` para minimizar, con
`base = 0.01*(máximo-mínimo)`. Si todos empatan, la selección es uniforme.
Esto admite funciones negativas y evita pesos negativos de la transformación
`cmax*1.05 - f` del texto. La selección es con reemplazo.

**Cruce y mutación.** El cruce se sortea por pareja. Si se realiza, intercambia
los segmentos tras un corte interior por cada variable. Un cromosoma de un bit
se copia; un padre sobrante de una población impar pasa sin cruce. La mutación
se sortea por bit, también en padres que pasaron sin cruce. `0.01` es 1 % por
bit, no un porcentaje exacto de individuos mutados.

**Elitismo e histórico.** Las élites pasan intactas a la nueva población y no
se cruzan ni mutan. Con al menos una élite el mejor objetivo no empeora. Con
cero élites puede perderse el mejor individuo. El mejor histórico solo registra
el resultado: no se reintroduce por sí mismo. El resultado del pseudocódigo es
el mejor individuo de la **población final**.

## Problemas incluidos

| Ejemplo | Objetivo | Intervalo por variable | Referencia de las imágenes |
|---|---|---|---|
| `20 + e − 20 exp(−0.2\|x\|) − exp(cos(2πx))` | Máximo | `[0, 32]` | ≈22.3136 en x≈31.5005 |
| `−\|x sen(√\|x\|)\|` | Mínimo | `[−250, 250]` | ≈−201.843 en x≈±203.814 |
| `Σ −xi sen(√\|xi\|)` | Mínimo | `[0, 100]` | ≈−n·63.63498 en cada xi≈65.54785 |

Se usa `math.sin` en radianes. Las referencias sirven para comparar, no se
inyectan en la población ni se utilizan para seleccionar o parar. El segundo
ejemplo es simétrico: tanto x positivo como negativo pueden ser soluciones.
El algoritmo es aleatorio y no garantiza encontrar el óptimo global.

Para agregar otra función, define una función que reciba la tupla de valores y
agrégala a `PROBLEMAS` con su intervalo y dirección de optimización. Esta
versión utiliza el mismo intervalo y longitud de bits para todas las variables.

## Estudiar parámetros

```bash
python estudio.py
python -m unittest -v
python algoritmo.py  # Alternativa por consola: una línea por generación.
```

El estudio usa diez semillas para cada variante y mantiene el resto de los
parámetros base. La semilla cambia entre repeticiones, usando el mismo conjunto
de semillas para todas las variantes. Imprime media y desviación típica del
mejor final y la generación media que encontró el mejor observado. Guarda cada
corrida en `resultados_estudio.csv`. Esa generación no acredita haber llegado
al óptimo matemático. Edita `PROBLEMA`, `PARAMETROS_BASE`, `SEMILLAS` o
`VARIANTES` en el script para comparar otros casos.

Ejercicios: compara élites 0 y 1; luego mutación 0 y 0.01; después población 20
y 120. Mantén los demás parámetros y la semilla. Observa si se pierden buenas
soluciones, si aparecen nuevos genotipos y cómo cambia el promedio. Usa varias
semillas antes de concluir que una configuración es mejor.

### Resultados de esta ejecución

Se ejecutaron 200 corridas del problema de maximización, con los valores base
y las semillas 0–9. El CSV incluido contiene sus resultados. Algunas
comparaciones, manteniendo lo demás fijo:

| Parámetro | Valor | Media del mejor final | Desviación típica |
|---|---:|---:|---:|
| Élites | 0 | 22.310206 | 0.006410 |
| Élites | 1 | 22.313676 | <0.000001 |
| Mutación por bit | 0 | 22.311866 | 0.005711 |
| Mutación por bit | 0.01 | 22.313676 | <0.000001 |

En estas corridas el elitismo y la mutación evitaron pérdidas o estancamiento.
Con poblaciones de 20, 60 y 120, las medias del mejor final fueron muy similares,
pero el mejor histórico se encontró, en promedio, en las generaciones 29.3,
24.2 y 17.2 respectivamente. Una generación con más individuos requiere más
evaluaciones, así que menos generaciones no implica menor coste de cálculo.
Estos resultados describen este problema y estas semillas, no una regla
universal ni una demostración del óptimo.

También se verificaron los tres ejemplos con los parámetros base y semilla 42:

| Problema | Mejor objetivo final | Coordenadas aproximadas |
|---|---:|---|
| Máximo | 22.313676 | x = 31.499985 |
| Mínimo | −201.843217 | x = −203.811557 |
| Varias variables (n = 2) | −127.269964 | x₁ = 65.546917, x₂ = 65.547680 |

Pasaron las siete pruebas del algoritmo y la comprobación de la ventana con
los tres ejemplos, paso manual, reproducción, pausa y fin de ejecución.
