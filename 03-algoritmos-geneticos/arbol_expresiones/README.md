# Árbol de expresiones

Intérprete didáctico en Python y PyQt6. Construye un árbol, anima sus recorridos,
grafica funciones de una variable y compara observaciones CSV con la función.

## Ejecutar y probar

```bash
cd arbol_expresiones
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python interfaz.py
```

Si el entorno ya existe, basta ejecutar la última instrucción. Pruebas sin pantalla:

```bash
QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORMTHEME= .venv/bin/python -m unittest -v
```

## Flujo de la interfaz

1. Escribe una expresión o pulsa **Generar expresión**. **Altura máx.** limita
   únicamente la generación (una hoja tiene altura 1).
2. En **Árbol y recorridos**, selecciona preorder, inorder o postorder y usa
   Anterior, Reproducir, Siguiente o la línea de tiempo. **Ver pasos** despliega
   el historial; se puede seleccionar cualquier paso para regresar a él.
3. En **Gráfica y datos**, configura límites X/Y y pulsa **Actualizar gráfica**.
   Hay cuadrícula, marcas numéricas y ejes cartesianos. La curva se recorta al
   rango indicado. La gráfica permanece integrada en esa pestaña.
4. **Cargar CSV** superpone observaciones rojas sobre la curva azul, ajusta la
   vista a los datos y muestra las métricas. **Quitar datos** elimina la comparación.
5. **Exportar puntos CSV** utiliza el intervalo X y **Paso CSV**. El extremo
   final se incluye sólo cuando coincide con el paso. Se informa cuántas muestras
   se omitieron por dominio inválido. Se permiten hasta 100,000 muestras.

No hay captura de valores de variables ni asignaciones automáticas. `x` es la
variable independiente; sus valores proceden del intervalo o de cada punto del
CSV. Una expresión con `y` u otras variables se puede construir y recorrer como
árbol simbólico, pero para graficarla en este plano se requiere una función de
`x`. Una expresión constante muestra directamente su resultado numérico.

## Lenguaje y fundamentos

Ejemplos: `(x + 2) * sin(x)`, `x^2`, `sqrt(abs(x))`, `log(x)`.

- Operadores binarios: `+`, `-`, `*`, `/`, `^`.
- Signos unarios: `+`, `-`.
- Funciones unarias: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sqrt`,
  `exp`, `log`, `ln`, `log10`, `abs`, `floor`, `ceil`.
- Constantes: `pi`, `e`. Los ángulos usan radianes; `log` y `ln` son naturales.
- Números: enteros, decimales (también `.5`) y notación científica (`1e-3`).
- Escribe multiplicación explícita: `2*x`, no `2x`. No se admiten ecuaciones
  con igualdad ni funciones con varios argumentos.

El parser respeta precedencia y asociatividad: `2^3^2 = 2^(3^2)`, `-2^2 = -4`
y `(-2)^2 = 4`. La serialización conserva paréntesis para reconstruir el mismo
árbol, incluidos los signos unarios. No se utiliza `eval()`.

Cada aparición es un nodo independiente: `x+x` contiene dos hojas distintas.
La **aridad** determina cuántos hijos exige una operación. Los recorridos son:

| Recorrido | Orden |
|---|---|
| preorder | raíz, izquierdo, derecho |
| inorder | izquierdo, raíz, derecho |
| postorder | izquierdo, derecho, raíz |

Se rechazan árboles con hijos faltantes, ciclos, nodos compartidos y alturas
excesivas. El parser limita el texto a 511 tokens y los árboles a 64 niveles.
La altura solicitada de generación no tiene un máximo artificial. El parser de
texto conserva sus límites de gramática; los árboles genéticos se transfieren
directamente al editor, sin volver a pasar por esa conversión textual.
Su altura mínima predeterminada es `min(3, altura_maxima)`.

## Biblioteca y organización

| Archivo | Responsabilidad |
|---|---|
| `algoritmo.py` | Nodo, catálogo único de operaciones, parser, evaluador, validación y recorridos |
| `biblioteca.py` | Generación aleatoria con aridad y altura; catálogo derivado del intérprete |
| `datos.py` | Muestreo, lectura y escritura CSV sin depender de Qt |
| `metricas.py` | Métricas numéricas sin interfaz |
| `interfaz.py` | Ventana, dibujo y controles |

```python
from algoritmo import ExpressionParser, ExpressionEvaluator
from biblioteca import GeneradorExpresiones
from datos import muestrear, guardar_csv

raiz = ExpressionParser("x^2 + 1").parse()
print(ExpressionEvaluator({"x": 3}).evaluate(raiz))  # 10
puntos = muestrear(raiz, -2, 2, 0.5)
guardar_csv("puntos.csv", puntos)

# Reproducible; no depende de Qt.
generador = GeneradorExpresiones(altura_maxima=4, variables=("x",), semilla=7)
print(generador.generar())
```

La API del evaluador sí acepta diccionarios de variables para futuras
integraciones. `generar_hasta(validar, intentos)` sólo devuelve una expresión
que cumpla el predicado; al agotarse los intentos lanza `ExpresionError`.
Una expresión sintácticamente válida no necesariamente pertenece al dominio
real en todo el intervalo. La interfaz genera candidatos y exige suficientes
muestras válidas, sin prometer validez en todos los números reales.

## CSV y métricas

CSV de exactamente dos columnas, con encabezado opcional `x,y` y separador
coma o punto y coma. Se admiten BOM y filas vacías. Se rechazan números no
finitos y filas inválidas en lugar de ignorarlas silenciosamente.

```csv
x,y
-1,1
0,0
1,1
```

Con `n` observaciones y errores `e = y_observado - y_predicho`:

| Métrica | Definición |
|---|---|
| MSE | suma(e²) / n |
| RMSE | raíz(MSE) |
| NMSE | MSE / varianza poblacional observada |
| R² | 1 − suma(e²) / suma((y − media)²) |

NMSE y R² se muestran como **no definidas** si la varianza observada es cero.
R² puede ser negativo. Sólo se comparan pares con predicción real válida y
se informa el número comparado respecto del total; los puntos originales se
mantienen visibles para que las exclusiones sean evidentes.

## Límites y verificación

El evaluador rechaza complejos, infinitos, desbordamientos y errores de dominio.
La división usa tolerancia absoluta `1e-12`; se puede cambiar desde la API.
No se reemplazan errores por cero. La gráfica deja huecos y evita unir saltos
muy grandes, pero es un muestreo finito: no demuestra continuidad ni encuentra
todas las singularidades. Las instantáneas completas del recorrido consumen
O(N²) de memoria; son apropiadas para árboles pequeños de estudio.

El tema utiliza Fusion, paleta explícita y estilos claros. Sólo el título usa
peso destacado; inputs y listas desplegables tienen fondo blanco y texto negro.
Las pruebas cubren precedencia, serialización, identidad, aridad, dominios,
altura, CSV, métricas y actualización del estado de la interfaz.

## Regresión simbólica con programación genética

La pestaña **Evolución genética** busca un árbol que ajuste los puntos del CSV.
No requiere conocer la función que generó esos puntos ni introducir valores de
variables. `x` viene de cada observación y `y` es su valor objetivo.

1. Pulsa **Importar CSV para evolución**. Puedes probar `ejemplos/parabola.csv`
   (13 observaciones de `x²+x+1`). Se necesitan al menos dos X distintos.
2. Configura población, generaciones, altura máxima (6 inicialmente en la interfaz), probabilidades de cruce y
   mutación, elitismo, selección de padres, torneo, semilla, métrica y tolerancia objetivo.
3. Pulsa **Iniciar evolución**. La generación 0 es la población inicial; después
   se realizan como máximo las generaciones solicitadas. **Detener** cancela
   cooperativamente, conservando los estados ya completados.
4. **Ajuste de la función** muestra la mejor función histórica sobre los puntos
   y sus cuatro métricas. **Evolución del error** muestra la mejor pérdida
   histórica y la media de los individuos válidos en escala logarítmica.
5. **Individuos** permite elegir una generación y consultar su población,
   ordenada por pérdida. Selecciona una fila para ver el árbol. Desmarca
   **Seguir última generación** para navegar el historial durante la ejecución.
6. **Abrir individuo en el editor** o **Abrir mejor función en el editor** lleva
   el árbol a la vista original: allí puedes animarlo, graficarlo y exportar CSV.

Los parámetros se fijan al iniciar; para cambiarlos detén la ejecución y vuelve
a iniciarla. La semilla reproduce la misma secuencia de individuos con los mismos
datos, configuración y entorno numérico. Los campos de parámetros no recortan
los valores a máximos arbitrarios: aceptan enteros de Python y reales, incluida
notación científica como `1e-12`. Se mantienen las condiciones del algoritmo:
población ≥ 2, generaciones ≥ 0, altura ≥ 1, élite menor que población y
probabilidades en [0,1]. El torneo se realiza con reposición y puede superar el
tamaño poblacional. La memoria, la recursión de Python y la precisión numérica
siguen siendo recursos finitos. El historial permanece en memoria y se reinicia
al importar otro CSV o iniciar una ejecución nueva.

### Evaluación y selección

Cada árbol se evalúa contra **todos** los puntos. Un error de dominio,
desbordamiento, complejo o infinito invalida al individuo completo: su pérdida
es infinita y el motivo aparece al seleccionarlo. No se favorecen funciones que
fallen en muestras difíciles. La media del gráfico utiliza sólo individuos
válidos; cada generación informa cuántos hay. Una generación sin individuos
válidos presenta un hueco en esa curva.

| Objetivo elegido | Pérdida minimizada | Parada |
|---|---|---|
| MSE | MSE | MSE ≤ tolerancia |
| RMSE | RMSE | RMSE ≤ tolerancia |
| NMSE | NMSE | NMSE ≤ tolerancia |
| R² | 1 − R² | 1 − R² ≤ tolerancia |

NMSE y R² no se permiten como objetivo cuando Y es constante: selecciona MSE o
RMSE. El selector **Selección de padres** ofrece:

| Método | Comportamiento |
|---|---|
| Torneo | Sortea con reposición y conserva el de menor pérdida; el tamaño controla presión selectiva |
| Ruleta | Peso `1/(1 + pérdida/escala)`; escala = mediana de pérdidas positivas; cero es válido |
| Rango | Peso por posición, preferencia al mejor; menos sensible a pérdidas de magnitudes muy distintas |
| Aleatoria uniforme | Todos los individuos tienen la misma probabilidad; útil como control experimental |

Ruleta y rango excluyen inválidos cuando existen soluciones válidas; si todos
son inválidos se elige uniformemente. El campo Torneo sólo está activo para ese
método. Los mejores pasan intactos mediante **elitismo**. En empates se prefiere
el árbol con menos nodos; no se añade una penalización oculta a las métricas.
El mejor histórico se conserva para consulta incluso con elitismo cero.

### Cruce y mutaciones

El **cruce de subárboles** elige un punto en cada padre y sustituye las ramas.
La raíz también puede seleccionarse. Si el intercambio supera la altura máxima,
se buscan otros cortes; si no se encuentra uno válido, se copian los padres.
No se cortan operadores dejando hijos ausentes. Las copias conservan identidad
independiente por nodo y no alteran a padres ni élite.

**Prob. cruce** se aplica por pareja; **Prob. mutación** por hijo. Cuando un hijo
muta se elige un tipo según los pesos de la configuración desplegable:

| Mutación | Qué cambia |
|---|---|
| Terminal | Cambia terminales o perturba una constante existente con pasos gaussianos pequeños, medianos y grandes |
| Operación | Sustituye un operador por otro de la misma aridad |
| Intercambio de hijos | Permuta ramas de operaciones no conmutativas; evita desperdiciar intentos en `+` y `*` |
| Subárbol nuevo | Sustituye, inserta o poda una rama; puede incluir la raíz y conserva aridad/altura |

Los pesos predeterminados son 30,30,10,30. Son relativos y se normalizan entre
sí (25,25,25,25 también es válido). Un peso cero desactiva ese tipo. Si no hay
un nodo compatible, se conserva una copia. Los reintentos para evitar clones
utilizan el mismo tipo sorteado: con probabilidad cero no se introduce una
mutación oculta. Un cambio de estructura no asegura mejorar el resultado.

El catálogo base usa `+`, `-`, `*`, `/`, `sin`, `cos`. La interfaz permite añadir
`^` por separado y lo activa inicialmente; favorece exponentes enteros 2, 3 y 4
para no invalidar automáticamente los X negativos. El catálogo científico
completo se activa en la configuración desplegable. Las constantes iniciales
mezclan enteros sencillos y decimales en `[-5,5]`; las mutaciones y los ajustes
pueden producir constantes fuera de ese intervalo. La población inicial mezcla
alturas y árboles completos/de crecimiento variable (ramped half-and-half).
No se usa DEAP.

### Mejoras de la búsqueda y modo híbrido

Se preserva diversidad mediante inmigración aleatoria (fracción predeterminada
0.1), reintentos acotados de mutaciones duplicadas y simplificación de ramas
constantes. La simplificación conserva dominios: no transforma `x/x` en `1` ni
`0*log(x)` en `0`. La interfaz muestra la proporción de expresiones únicas. Una
caché por generación evita recalcular la aptitud de clones exactos.

Al desplegar Configuración avanzada se ocultan temporalmente las gráficas para
evitar comprimirlas; Iniciar evolución cierra esa configuración automáticamente.
Dos opciones, activadas por defecto, hacen la búsqueda **híbrida**:

- **Ajuste lineal de salida:** calcula `a*f(x)+b` por mínimos cuadrados para
  hasta tres candidatos por generación, respetando la altura máxima y el catálogo.
- **Refinamiento local de constantes:** un paso por coordenada en las constantes
  del mejor candidato, mediante derivadas centrales numéricas y retroceso del
  paso si hace falta. Sólo acepta una reducción de la pérdida completa.

Estas opciones ayudan a ajustar coeficientes sin depender exclusivamente de
acertar un decimal por azar. Se pueden desmarcar ambas para comparar con
programación genética pura. La búsqueda sigue necesitando encontrar la
estructura: los ajustes no garantizan recuperar una fórmula ni eliminar el
estancamiento. La inicialización y las propuestas son aleatorias; ninguna
función de los ejemplos se introduce como plantilla en la población.

### Reutilizar el motor sin interfaz

```python
from datos import leer_csv
from genetico import Parametros, RegresionSimbolica

puntos = leer_csv("ejemplos/parabola.csv")
config = Parametros(poblacion=60, generaciones=50, semilla=42)
motor = RegresionSimbolica(puntos, config)
for estado in motor.evolucionar():
    print(estado.numero, estado.mejor_historico.perdida)
mejor = estado.mejor_historico
print(mejor.expresion)
print(dict(mejor.metricas))
```

`genetico.py` contiene los operadores, parámetros y estados inmutables del
motor. `interfaz_genetica.py` contiene el panel y el trabajador Qt. Reutilizan
`Nodo`, el catálogo único de `algoritmo.py`, `ExpressionEvaluator.predecir`, la
lectura/muestreo de `datos.py` y las métricas de `metricas.py`. El motor entrega
una instantánea por generación y acepta una función de cancelación; no importa
Qt. Las expresiones y generaciones pueden inspeccionarse sin abrir ventanas.

El coste crece con población × generaciones × puntos × nodos. Las gráficas de
ajuste usan muestras adicionales sólo para dibujar: la aptitud siempre se calcula
con todas las observaciones originales. Las métricas mostradas corresponden a
los datos de ajuste, no a un conjunto de validación independiente. La búsqueda
es estocástica: puede estancarse y diferentes árboles pueden ajustar los mismos
datos; un error pequeño no demuestra que se recuperó la fórmula original.

### Comparación reproducible de versiones

La comparación guardada en el commit `eae97ce` es anterior al diagnóstico de
oscilaciones y a los nuevos exponentes enteros. `estudio_busqueda.py` compara
el motor original guardado en el commit `2076471`,
el motor actual sin refinamientos y el actual híbrido. Usa 25 puntos en [-3,3],
población 80, hasta 60 generaciones, altura 5 y semillas 7, 21 y 42. Los tiempos,
expresiones y todos los resultados están en `resultados/comparacion_busqueda.csv`.
Los métodos híbridos realizan trabajo local adicional: se registran tiempos,
no se afirma que el presupuesto de evaluaciones sea idéntico.

MSE mediano de las tres semillas:

| Función de prueba | Original | Actual sin refinamiento | Actual híbrido |
|---|---:|---:|---:|
| x²+x+1 | 7.56e-4 | 0 | 0 |
| 2.7x²−1.3x+0.45 | 0.199 | 0.169 | 7.86e-7 |
| 1.8sin(x)+0.7 | 0.00182 | 0.00225 | 0 |
| x³−2x+0.5 | 5.04 | 1.97 | 0.0546 |

El cero indica error numérico cero en esas observaciones, no una prueba
simbólica de equivalencia. La mejora es agregada, no por semilla: por ejemplo,
la cúbica con semilla 42 empeoró respecto del original. La variante puramente
genética también empeora la mediana trigonométrica. No se ocultan estos casos.

```bash
.venv/bin/python estudio_busqueda.py
```

Las pruebas incluyen los cuatro selectores, control de probabilidades, entradas
sin recorte, refinamiento, preservación de dominios, altura, aridad, identidad,
elitismo, semilla, parada y cancelación. El motor se divide en `genetico.py`,
`seleccion.py` y `mejoras_geneticas.py`; las entradas numéricas están en
`entradas.py`, sin acoplar el motor a Qt.


### Interpretar una curva cercana a la media

Consulta [la clase de error y regresión simbólica](../CLASE-ERROR-Y-REGRESION-SIMBOLICA.md).
La carga CSV muestra el MSE del predictor constante y la gráfica lo dibuja como
referencia gris. La explicación del ajuste indica cuándo apenas se supera esa
referencia. No modifica la función de pérdida ni inserta fórmulas conocidas.
`diagnostico.py` calcula esa referencia, una recta por mínimos cuadrados y cruces
de la media para facilitar la interpretación.
