# Programación genética: árboles, error y búsqueda de funciones

Guía de estudio del proyecto `arbol_expresiones`: teoría breve, operadores de
tus apuntes y aplicación al código actual. No requiere DEAP. Los ejemplos usan
la biblioteca del proyecto sin importar la interfaz.

## 1. Qué problema resolvemos

Disponemos de puntos `(x, y)` de un CSV y queremos encontrar una expresión
`f(x)` cuyas predicciones se acerquen a esos valores Y. Buscamos tanto la
**estructura de la expresión** como sus **constantes**: esto es regresión
simbólica mediante programación genética.

| Concepto | En este proyecto |
|---|---|
| Individuo | Un árbol de expresión completo |
| Población | Conjunto de árboles candidatos |
| Terminal | Hoja: `x` o una constante numérica |
| Operación | Nodo interno: suma, producto, seno, etc. |
| Evaluación | Predecir Y en cada X del CSV y calcular el error |
| Selección | Elegir padres favoreciendo mejores candidatos |
| Cruce | Intercambiar ramas entre dos árboles |
| Mutación | Modificar una hoja, operación, orden de hijos o rama |
| Generación | Un estado de la población durante la búsqueda |

En las prácticas anteriores evolucionaban cadenas binarias, vectores reales
o permutaciones. Aquí evoluciona una estructura de tamaño variable. El árbol
actúa como representación genética y como programa ejecutable; no necesitamos
decodificarlo desde una cadena de bits.

## 2. Representación, aridad e identidad

Para `(x + 2) * sin(x)`:

```text
          *
        /   \
       +    sin
      / \    |
     x   2   x
```

La **aridad** es el número de argumentos: `+` tiene dos, `sin` uno y una hoja
cero. Cambiar una suma por un seno sin adaptar sus hijos produce un árbol
incorrecto. Por eso la mutación de operación conserva la aridad.

Las dos apariciones de `x` tienen el mismo valor, pero son **nodos distintos**.
Compartir una instancia entre dos posiciones convertiría la estructura en un
grafo con nodos compartidos. El proyecto lo rechaza para mantener árboles.

La altura se cuenta por niveles: una hoja tiene altura 1. El ejemplo tiene
altura 3. Una mayor altura permite expresiones más complejas, pero también
aumenta las posibilidades de búsqueda y el costo de evaluación.

Código aplicado, desde `arbol_expresiones/`:

```python
from algoritmo import Nodo, ExpressionEvaluator, texto_inorder, validar_arbol
from biblioteca import altura_arbol

# Cada aparición de x se construye por separado.
raiz = Nodo(
    '*',
    Nodo('+', Nodo('x', tipo='variable'), Nodo('2', tipo='numero')),
    Nodo('sin', Nodo('x', tipo='variable'), tipo='funcion'),
)
validar_arbol(raiz, altura_maxima=3)
print(texto_inorder(raiz))
print(altura_arbol(raiz))  # 3
print(ExpressionEvaluator({'x': 1}).evaluate(raiz))
```

Los nodos son inmutables. `clonar()` y `sustituir()` construyen copias para que
una operación genética no modifique a los padres ni a los individuos de élite.
El catálogo `OPERACIONES` centraliza símbolo, tipo y aridad.

### Evaluar no es recorrer para mostrar

Preorder visita raíz–izquierdo–derecho; inorder, izquierdo–raíz–derecho;
postorder, izquierdo–derecho–raíz. La interfaz anima estos recorridos para
estudiar el árbol. El evaluador calcula recursivamente los hijos y aplica la
operación del padre; la animación no interviene en la puntuación genética.

## 3. Cómo se calcula el error

Cada X se sustituye en el mismo árbol. Si `e_i = y_i - f(x_i)`:

| Métrica | Fórmula | Interpretación |
|---|---|---|
| MSE | `promedio(e_i²)` | Error cuadrático medio; unidades de Y al cuadrado |
| RMSE | `sqrt(MSE)` | Error en unidades de Y |
| NMSE | `MSE / Var(Y)` | Error relativo a predecir la media |
| R² | `1 - NMSE` | Mejora respecto de predecir la media |

Aquí `Var(Y)` es la varianza poblacional de los valores observados. Cuando Y
es constante, NMSE y R² no están definidas: usa MSE o RMSE.

El motor **siempre minimiza** una pérdida. Para MSE, RMSE y NMSE usa el valor
directamente; para R² usa `1 - R²`. Por tanto, una tolerancia de `0.01` con
R² significa buscar `R² >= 0.99`, no `R² <= 0.01`.

```python
from algoritmo import ExpressionParser, ExpressionEvaluator
from metricas import calcular_metricas

xs = [1, 2, 3, 4]
ys = [1, 4, 9, 16]
raiz = ExpressionParser('x^2').parse()
predichos = ExpressionEvaluator().predecir(raiz, xs)
print(calcular_metricas(ys, predichos))
# mse=0, nmse=0, rmse=0, r2=1
print(calcular_metricas(ys, [7.5] * len(ys)))
# mse=32.25, nmse=1, rmse≈5.679, r2=0
```

Cambiar entre estas métricas no cambia el orden de calidad de los candidatos
sobre el mismo conjunto completo, cuando Var(Y) es positiva. Sí cambia la
escala de la tolerancia y puede cambiar la presión de selección por ruleta.

### Errores de dominio

El motor evalúa **todos los puntos**. Si una predicción tiene división por
cero, dominio inválido, valor complejo, infinito o desbordamiento, invalida al
individuo completo y asigna pérdida infinita. No sustituye el error por cero
ni elimina la observación difícil. El motivo se conserva para inspeccionarlo.

La división considera cercano a cero un denominador con tolerancia `1e-12`
por defecto. Una expresión puede tener aridad correcta y fallar numéricamente:
`log(x)` es un ejemplo si el CSV contiene X no positivos.

En el muestreo de gráficas se permiten huecos para representar el dominio.
Eso es distinto de la evaluación genética, que exige cubrir todo el CSV.

## 4. Flujo del algoritmo actual

```text
Leer y validar los puntos y parámetros
Generar árboles con alturas variadas
Simplificar y evaluar la población inicial
Para cada generación, incluyendo la 0:
    Aplicar refinamientos opcionales
    Ordenar por pérdida y, si empatan, por cantidad de nodos
    Registrar población, mejor histórico, diversidad y errores
    Si se cumple la tolerancia o el límite: terminar
    Conservar la élite
    Introducir la cantidad configurada de inmigrantes aleatorios
    Completar la población:
        Seleccionar dos padres
        Cruzarlos con cierta probabilidad; si no, copiarlos
        Mutar cada hijo con cierta probabilidad
        Simplificar, evaluar y añadir
Devolver estados para estudiar la evolución
```

La inicialización combina alturas variadas y estilos **full** y **grow**.
Full intenta expandir operaciones hasta el nivel permitido; grow puede terminar
antes en una hoja. En esta implementación, la preferencia por exponentes
enteros puede producir ramas cortas incluso en el modo full.

Los terminales se generan como `x`, constantes sencillas
`-2, -1, 0, 1, 2, 3, 4` o decimales iniciales entre `-5` y `5`.
Ese intervalo es una distribución inicial, **no un límite a los coeficientes
finales**: la mutación y los ajustes pueden salir de él.

## 5. Métodos de selección

Implementados en `seleccion.py`, disponibles en el selector de la interfaz:

| Método | Funcionamiento | Efecto |
|---|---|---|
| Torneo | Sortear candidatos con reposición y escoger el mejor | Aumentar el tamaño suele aumentar la presión selectiva |
| Ruleta | Sortear según pesos que disminuyen al aumentar la pérdida | Favorece errores pequeños sin exigir que siempre ganen |
| Rango | Asignar pesos según la posición de calidad | Depende menos de la magnitud del error |
| Uniforme | Elegir cualquier individuo con igual probabilidad | Sirve como control de comparación; no favorece calidad |

En ruleta se usa `peso = 1 / (1 + perdida / escala)`, donde la escala es el
elemento central de las pérdidas positivas ordenadas. Un error cero no causa
división por cero. En ruleta y rango los inválidos se excluyen mientras existan
válidos; si ninguno es válido, se elige uniformemente para intentar continuar.

El **elitismo** es otra decisión: copia los mejores a la siguiente población.
No es un método de selección de padres. Mucha élite puede reducir exploración.

## 6. Cruce: intercambio de subárboles

Es el cruce que aparece en tus apuntes: escoger un punto de cada padre e
intercambiar las ramas completas que nacen allí.

```text
Padre A: (x + 2) * sin(x)
Padre B: x - cos(x)

Ramas elegidas: sin(x) y cos(x)

Hijo A: (x + 2) * cos(x)
Hijo B: x - sin(x)
```

También se puede elegir la raíz. Se intercambian árboles completos como
argumentos; no se intercambia solamente el símbolo dejando hijos incompatibles.

### Qué pasa con la altura máxima

Si la raíz tiene ruta `()`, el hijo izquierdo `(0,)` y su hijo derecho `(0, 1)`,
la longitud de la ruta indica a qué profundidad se inserta una rama.

```python
from biblioteca import altura_arbol

def cabe_rama(ruta_destino, rama_entrante, altura_maxima):
    return len(ruta_destino) + altura_arbol(rama_entrante) <= altura_maxima
```

El cruce prueba hasta 16 pares de puntos. Si ninguno respeta la altura de ambos
hijos, devuelve copias de los padres. **Actualmente no poda para reparar un
cruce excesivo**. Tus apuntes plantean reparación como alternativa; el código
elige reintentar y conservar padres para no truncar arbitrariamente la fórmula.

```python
import random
from algoritmo import ExpressionParser, texto_inorder, validar_arbol
from genetico import cruzar

azar = random.Random(7)
padre = ExpressionParser('(x+2)*sin(x)').parse()
madre = ExpressionParser('x-cos(x)').parse()
for hijo in cruzar(padre, madre, azar, altura_maxima=4):
    validar_arbol(hijo, altura_maxima=4)
    print(texto_inorder(hijo))
# Los puntos se sortean: no tienen por qué coincidir con el dibujo anterior.
```

Los cruces de bits, aritmético o SBX de otras prácticas corresponden a otras
representaciones. PMX y OX conservan permutaciones. El motor de árboles utiliza
cruce de subárboles, no esos operadores.

## 7. Las cuatro mutaciones de tus apuntes

| Apunte | Nombre en código | Ejemplo conceptual |
|---|---|---|
| Cambiar un valor de una hoja | `terminal` | `x+2` → `x+2.1` |
| Cambiar una operación respetando aridad | `operacion` | `x+2` → `x*2`; `sin(x)` → `cos(x)` |
| Intercambiar hijos de un nodo | `intercambio` | `x-2` → `2-x` |
| Crear o sustituir una rama | `subarbol` | `sin(x)` → `sin(x*x)` |

Son posibilidades ilustrativas, no transformaciones obligatorias.

### Terminal

Selecciona una hoja. Una constante normalmente recibe una perturbación
gaussiana de escala pequeña, mediana o grande; también se puede reemplazar
por otro terminal. Así es posible explorar valores nuevos sin volver a
sortear siempre la fórmula completa.

Si es una constante situada directamente como exponente de `^`, se modifica
como entero: redondeo y desplazamiento de `-2`, `-1`, `1` o `2`. Al generar
potencias se favorecen exponentes `2`, `3`, `4` con probabilidad 0.8. Esto
facilita potencias comunes con X negativos; **no garantiza dominio válido**:
un exponente negativo sigue fallando en X=0. El refinamiento numérico local
es independiente y puede proponer exponentes no enteros; sólo se aceptan si
la evaluación completa es válida y mejora.

### Operación

Escoge otra operación del catálogo habilitado con la misma aridad. No convierte
directamente una operación binaria en unaria. Conservar aridad garantiza forma,
pero el nuevo operador puede causar problemas de dominio al evaluar.

### Intercambio

Permuta los hijos de un nodo binario. Se excluyen `+` y `*`, porque cambiar
su orden no aporta una fórmula matemáticamente distinta. Es relevante en
resta, división o potencia. No equivale a intercambiar ramas de dos padres:
eso sería cruce, no esta mutación.

### Subárbol

El código combina tres posibilidades dentro de este tipo:

- **Inserción:** envolver la rama existente en una operación binaria y añadir
  otra rama, conservando material previo cuando hay espacio.
- **Poda:** sustituir una rama por uno de sus hijos, reduciendo complejidad.
- **Reemplazo:** generar una rama nueva dentro de la altura disponible.

El modo se sortea: se intenta inserción cuando el número aleatorio es menor
que 0.4 y se cumplen sus condiciones; en caso contrario puede entrar la poda
si es menor que 0.6 y el nodo tiene hijos; si no, se reemplaza. Por ello los
porcentajes efectivos dependen también de la estructura y la altura.

### Probabilidad de mutar frente a pesos de los tipos

Primero se decide si un hijo muta con `prob_mutacion`. Sólo entonces se sortea
un tipo según los cuatro pesos; no se aplican los cuatro obligatoriamente.

```python
prob_mutacion = 0.35
pesos_mutacion = (40, 20, 0, 40)
# Si muta: 40% terminal, 20% operación, 0% intercambio, 40% subárbol.
# Probabilidad inicial de elegir terminal por hijo: 0.35 * 0.40 = 0.14.
```

Puede resultar una copia si no hay candidatos compatibles o el cambio no
produce una diferencia efectiva. Además, ante expresiones duplicadas el motor
permite hasta tres reintentos del mismo tipo ya seleccionado. No activa otro
tipo con peso cero ni introduce mutaciones ocultas cuando la probabilidad es
cero. La simplificación y los refinamientos opcionales son pasos separados.

```python
import random
from algoritmo import ExpressionParser, texto_inorder, validar_arbol
from genetico import MUTACIONES, mutar

original = ExpressionParser('(x+2)/cos(x)').parse()
azar = random.Random(21)
for tipo in MUTACIONES:
    resultado = mutar(original, tipo, azar, altura_maxima=5)
    validar_arbol(resultado, altura_maxima=5)
    print(tipo, texto_inorder(resultado))
# Cada llamada parte del original; no modifica al padre.
```

## 8. Por qué una función puede quedarse en el centro

El MSE promedia **errores cuadrados**, no funciones. Si los errores son `+10`
y `-10`, el MSE es 100: no se cancelan.

Si restringimos la predicción a una constante, el mejor valor bajo MSE es
`media(Y)`. Una senoide con frecuencia o fase equivocada puede fallar más que
esa constante. Reducir su amplitud reduce el error, aunque el dibujo parezca
conformista. La búsqueda encuentra una mejora local, pero no la forma buscada.

La regresión lineal `a*x+b` tampoco predice siempre la media: ajusta pendiente
e intercepto. Sólo el modelo restringido a una constante predice ese promedio.

Ejemplo de dificultad estructural:

```text
f(x) = a*cos(b*x^3)+c
```

Aquí hay que descubrir la potencia, la función trigonométrica y las constantes.
Un cambio de `0.01` en `b` produce un cambio de fase de 10 radianes en X=10.
Estar cerca del coeficiente no implica estar cerca de la curva.

La estructura escrita requiere altura 6 contando hojas como nivel 1. Si el
límite es 5, esa representación no cabe; aumentar población no elimina esa
restricción. Incluso admitiéndola, descubrir el coeficiente sigue siendo difícil.

Para Var(Y)>0:

| Resultado | Lectura |
|---|---|
| NMSE≈1, R²≈0 | Apenas mejora o iguala a la media |
| NMSE>1, R²<0 | Peor que la referencia constante |
| NMSE=0.1, R²=0.9 | Reduce 90% del error de referencia |
| NMSE=0.01, R²=0.99 | Reduce 99% |

No conviene premiar oscilaciones por su apariencia. Deben mejorar las
predicciones. La interfaz muestra la referencia de la media y su MSE, junto
con una línea gris discontinua y un diagnóstico del ajuste.

## 9. Qué hace ahora el modo híbrido

La programación genética explora estructuras. Dos refinamientos opcionales
ayudan con los números; activados, la búsqueda es **híbrida**.

### Ajuste lineal de salida

Para una estructura `g(x)` se busca `a*g(x)+b` por mínimos cuadrados:

```text
a = suma((g_i-media(g))*(y_i-media(y))) / suma((g_i-media(g))²)
b = media(y) - a*media(g)
```

Si `g` es constante, se propone la media Y. Se intenta el ajuste sobre hasta
tres candidatos válidos de mejor orden por generación, siempre que estén
habilitados `+` y `*`. Se evalúa la propuesta, se comprueba la altura y sólo se
acepta si mejora el orden `(pérdida, nodos)`. El código normaliza el cálculo
para reducir problemas numéricos y evita acumular envolturas lineales.

Este ajuste encuentra amplitud e intercepto; **no arregla por sí mismo una
frecuencia interna equivocada**. Puede reducir la amplitud por esa razón.

### Refinamiento local de constantes

Sobre el candidato de índice 0 tras la ordenación inicial del refinamiento,
se recorren sus constantes. Se aproxima la derivada de la predicción respecto
de una constante mediante diferencias centrales:

```text
d_i ≈ (f(x_i, c+h) - f(x_i, c-h)) / (2*h)
paso = suma(d_i*(y_i-f_i)) / suma(d_i²)
```

Se prueban factores `1`, `0.5`, `0.25` del paso y se acepta una propuesta que
mejore el orden tras reevaluar todos los puntos. No cambia la estructura y no
garantiza el mínimo global: es un paso local por coordenada.

Para comparar con el modo genético sin estos refinamientos:

```python
from genetico import Parametros

parametros = Parametros(ajuste_lineal=False, refinar_constantes=False)
```

La simplificación sigue funcionando: reduce ramas constantes evaluables y
reglas seguras como `x+0` o `x*1`. No usa `x/x=1` ni elimina indiscriminadamente
`0*exp(x)`, porque ocultaría restricciones de dominio o desbordamientos.

## 10. Ejecución completa sin interfaz

Desde `arbol_expresiones/`, con el entorno del proyecto, este ejemplo genera
observaciones de práctica y aprende desde los puntos. La fórmula usada para
crear los datos no se entrega al motor como árbol inicial.

```python
from algoritmo import OPERACIONES, ExpressionEvaluator
from genetico import Parametros, RegresionSimbolica, OPERACIONES_BASE
from metricas import calcular_metricas

puntos = [(i / 2, (i / 2)**2 + i / 2 + 1) for i in range(-6, 7)]
# Para un archivo propio, sustituye la línea anterior por:
# from datos import leer_csv
# puntos = leer_csv('mis_puntos.csv')

operaciones = OPERACIONES_BASE + tuple(
    operacion for operacion in OPERACIONES if operacion.simbolo == '^'
)
parametros = Parametros(
    poblacion=60,
    generaciones=20,
    altura_maxima=6,
    seleccion='torneo',
    torneo=3,
    prob_cruce=0.85,
    prob_mutacion=0.35,
    pesos_mutacion=(40, 20, 0, 40),
    elitismo=2,
    inmigracion=0.10,
    metrica='nmse',
    objetivo=0.01,
    semilla=42,
    operaciones=operaciones,
    ajuste_lineal=True,
    refinar_constantes=True,
)
motor = RegresionSimbolica(puntos, parametros)
mejor = None
for estado in motor.evolucionar():
    mejor = estado.mejor_historico
    print(estado.numero, mejor.perdida, mejor.expresion)

if mejor is None or not mejor.valido:
    print('No se encontró un individuo evaluable.')
else:
    xs, ys = zip(*puntos)
    predichos = ExpressionEvaluator().predecir(mejor.raiz, xs)
    print('Métricas finales:', calcular_metricas(ys, predichos))
```

`evolucionar()` entrega estados mediante `yield`: permite a la interfaz mostrar
cada generación sin acoplar el algoritmo a Qt. Incluye generación 0 y se detiene
por tolerancia, límite de generaciones o cancelación. El ejemplo no asegura
encontrar la misma expresión textual que creó los datos.

## 11. Parámetros: qué modificar y por qué

| Parámetro | Si aumenta |
|---|---|
| Población | Explora más candidatos; consume más tiempo y memoria |
| Generaciones | Da más oportunidades; no corrige una representación insuficiente |
| Altura máxima | Admite más estructuras y también más complejidad inútil |
| Probabilidad de cruce | Recombinación más frecuente; no garantiza hijos diferentes |
| Probabilidad de mutación | Mayor exploración; puede destruir material útil |
| Tamaño del torneo | Mayor preferencia por ganadores; riesgo de convergencia prematura |
| Elitismo | Conserva más soluciones; deja menos espacio para novedades |
| Inmigración | Introduce más árboles nuevos; reduce espacio de descendientes |

La diversidad registrada es la fracción de expresiones textuales distintas.
Es una aproximación: expresiones distintas pueden ser matemáticamente
equivalentes. El mejor histórico se conserva aparte del promedio poblacional.
Menos nodos desempata pérdidas iguales; actualmente no hay penalización
continua por complejidad añadida al MSE.

La interfaz parte de altura 6 y activa la opción de potencias. La API
`Parametros()` conserva altura 5 y catálogo base sin `^`: al usar la biblioteca
debes declarar explícitamente esas opciones, como hace el ejemplo completo.
La interfaz ofrece además el catálogo científico completo; habilitarlo aumenta
el espacio de búsqueda y la posibilidad de errores de dominio.

No hay topes arbitrarios de población, generaciones o altura en esos parámetros.
Sí se validan probabilidades en `[0,1]`, tamaños coherentes y valores finitos.
La memoria, la recursión de Python y la precisión de los números siguen siendo
limitaciones reales. La semilla permite comparar ejecuciones con los mismos
datos, configuración y entorno.

## 12. Qué está implementado y qué falta evaluar

| Estado | Funcionalidad |
|---|---|
| Implementado | Árboles con identidad independiente, validación y catálogo de aridad |
| Implementado | Cruce de subárboles con reintentos por altura |
| Implementado | Cuatro mutaciones con pesos configurables |
| Implementado | Torneo, ruleta, rango y selección uniforme |
| Implementado | Evaluación completa, élite, inmigración y registro de diversidad |
| Implementado | Ajuste lineal de salida y refinamiento local opcionales |
| Implementado | Referencia de la media, potencias y preferencia por exponentes enteros |
| Propuesto | Ajuste de constantes desde múltiples inicializaciones o búsqueda global |
| Propuesto | Reacción automática al estancamiento con reinicios o inmigración adaptativa |
| Propuesto | Separación automática de entrenamiento y validación en la interfaz |
| Por demostrar | Éxito consistente para funciones difíciles a través de varias semillas |

El motor ya separa operadores y evaluación de la interfaz, pero no basta para
afirmar que recupera cualquier función. Primero debe caber una estructura
adecuada; después debe encontrarla y ajustar sus constantes.

Para estudiar una mejora: fija datos y presupuesto, cambia un aspecto, ejecuta
varias semillas y compara error, tiempo y proporción de ejecuciones exitosas.
Evalúa también puntos reservados distribuidos por el intervalo. Un error bajo
de entrenamiento no prueba que se recuperó la fórmula original ni garantiza
extrapolación. Con pocas muestras pueden existir muchas funciones compatibles.

## 13. Dónde estudiar cada parte del código

| Archivo | Puntos fundamentales |
|---|---|
| [algoritmo.py](arbol_expresiones/algoritmo.py) | `Nodo`, `OPERACIONES`, `validar_arbol`, parser y evaluador |
| [biblioteca.py](arbol_expresiones/biblioteca.py) | Generador reutilizable y `altura_arbol` |
| [genetico.py](arbol_expresiones/genetico.py) | `Parametros`, rutas, copias, generación, cruce, mutación y motor |
| [seleccion.py](arbol_expresiones/seleccion.py) | Métodos de selección de padres |
| [mejoras_geneticas.py](arbol_expresiones/mejoras_geneticas.py) | Simplificación y ajuste de salida |
| [metricas.py](arbol_expresiones/metricas.py) | Cálculo del error |
| [diagnostico.py](arbol_expresiones/diagnostico.py) | Referencias de media y recta |
| [datos.py](arbol_expresiones/datos.py) | CSV y muestreo |
| [interfaz_genetica.py](arbol_expresiones/interfaz_genetica.py) | Parámetros, hilo de trabajo, gráficas e individuos |

Para los controles de la aplicación consulta el
[README del proyecto](arbol_expresiones/README.md). La
[clase sobre error y estancamiento](CLASE-ERROR-Y-REGRESION-SIMBOLICA.md)
amplía el análisis numérico previo; sus cifras corresponden a los CSV examinados
entonces y deben recalcularse si sustituyes los datos.
