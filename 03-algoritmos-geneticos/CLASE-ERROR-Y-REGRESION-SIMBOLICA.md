# Por qué una función puede quedarse cerca de la media

La métrica del proyecto se calcula punto a punto y es correcta para los casos
verificados. Encontrar una fórmula difícil es otro problema: intervienen la
representación, las operaciones disponibles y la búsqueda sobre los árboles.

## 1. Regresión lineal: la media no es toda la predicción

La regresión lineal simple usa `ŷ = a*x + b`. Calcula una pendiente y un
intercepto para minimizar la suma de errores cuadrados. Con intercepto, la
recta pasa por `(media(x), media(y))`, pero no predice la media en todos los X.

Si obligamos al modelo a ser constante, `ŷ=c`, el mejor valor bajo MSE sí es
`c=media(y)`. Se obtiene derivando la suma de `(y_i-c)^2` respecto de c e
igualando a cero. Este predictor constante es una referencia, no una solución
que explique la relación entre X e Y.

Ejemplo:

| X | Y observado | Media: 7.5 | Recta: 5x−5 | Curva: x² |
|---:|---:|---:|---:|---:|
| 1 | 1 | 7.5 | 0 | 1 |
| 2 | 4 | 7.5 | 5 | 4 |
| 3 | 9 | 7.5 | 10 | 9 |
| 4 | 16 | 7.5 | 15 | 16 |
| **MSE** | | **32.25** | **1** | **0** |

Un modelo con más capacidad puede reducir el error si la búsqueda encuentra
la estructura correcta. El cálculo del error no proporciona esa estructura.

## 2. Qué promedia el MSE

Para cada X del CSV se calcula la predicción del árbol, después su diferencia
respecto del Y observado, y finalmente se eleva al cuadrado:

```text
error_i = y_i − f(x_i)
MSE     = suma(error_i²) / n
```

Se promedian los errores cuadrados; no las funciones ni las predicciones para
inventar una curva intermedia. Errores +10 y −10 tienen promedio cero, pero su
MSE es 100. El cuadrado evita esa cancelación.

Si una curva oscila con fase incorrecta, muchos de sus máximos pueden coincidir
con mínimos de los datos. Su error puede ser mayor que el de una línea central.
El optimizador reduce la amplitud porque eso mejora el criterio en esa estructura
equivocada. No es una preferencia universal por líneas planas: la función que
coincide con todos los Y tiene MSE cero y vence a esa referencia.

## 3. Las cuatro métricas están relacionadas

Para el mismo conjunto de observaciones, con varianza poblacional no nula:

```text
Var(Y) = promedio((y_i − media(Y))²)
RMSE   = sqrt(MSE)
NMSE   = MSE / Var(Y)
R²     = 1 − NMSE
```

- MSE usa unidades de Y al cuadrado.
- RMSE vuelve a las unidades de Y.
- NMSE mide el error respecto de predecir siempre la media.
- R² mide cuánto error de esa referencia se ha reducido.

| NMSE | R² | Lectura |
|---:|---:|---|
| 1 | 0 | No mejora a la media |
| 0.9 | 0.1 | Sólo reduce 10% del error de referencia |
| 0.1 | 0.9 | Reduce 90% |
| 0.01 | 0.99 | Reduce 99% |
| 0 | 1 | Coincide en todas las observaciones |
| >1 | <0 | Es peor que predecir la media |

Con Y constante, NMSE y R² no están definidas; usa MSE o RMSE.
Cambiar entre estas métricas no aporta nueva información sobre la forma. Con
el mismo conjunto completo, su orden de calidad es el mismo. Torneo y rango
conservan ese orden; ruleta puede cambiar presión selectiva al transformar
magnitudes. La tolerancia de parada también debe interpretarse en cada escala.

## 4. Diagnóstico concreto de los CSV del proyecto

Se revisaron ambos archivos, sin asumir cuál estabas utilizando:

| Archivo | Puntos | Media Y | MSE de predecir la media |
|---|---:|---:|---:|
| `arbol_expresiones/funcion.csv` | 2001 | 7.1796841548 | 60.0234783837 |
| `arbol_expresiones/funcion_02.csv` | 101 | 9.5190920147 | 46.4241662452 |

En los dos se verificó numéricamente:

```text
11*cos(7.23*x^3)+6.87
MSE = 0, RMSE = 0, NMSE = 0, R² = 1
```

Esto demuestra que existe una expresión de nuestro lenguaje que reproduce los
CSV. Es una hipótesis comprobada sobre las muestras; no demuestra unicidad de
la función fuera de ellas, ni que una ejecución genética haya descubierto por
sí sola esta fórmula. No se introduce esa expresión como individuo inicial ni
se guardan sus coeficientes en el motor.

Esta señal tiene frecuencia variable: su fase es `7.23*x³`, no `7.23*x`.
Una senoide común de frecuencia fija no tiene la misma forma.

### Capacidad del árbol

```text
11*cos(7.23*x^3)+6.87       necesita altura 6
11*cos(7.23*x*x*x)+6.87     necesita altura 7
```

Una hoja cuenta como altura 1. La representación anterior con altura máxima
5 no admite esos árboles. El catálogo base tampoco incluía `^`, de modo que
la alternativa multiplicativa necesitaba todavía más niveles. Aumentar
población no elimina esa restricción estructural.

### Sensibilidad de la frecuencia

En X=10, cambiar k en 0.01 dentro de `cos(k*x³)` cambia la fase en 10 radianes.
No es una perturbación pequeña de la curva. Manteniendo amplitud 11 e
intercepto 6.87, en el CSV de 2001 puntos se obtuvo:

| k | MSE |
|---:|---:|
| 7.22 | 79.7145 |
| 7.229 | 8.27770 |
| 7.23 | 0 |
| 7.231 | 8.81075 |
| Predecir media | 60.0235 |

La frecuencia 7.22 ya se parece en sus coeficientes, pero es peor que la media.
Si ajustamos sólo amplitud e intercepto para una frecuencia fija:

| Modelo ajustado | MSE aproximado |
|---|---:|
| 0.8078*cos(x³)+7.1170 | 59.6822 |
| 3.7834*cos(7.22*x³)+7.0548 | 52.5610 |
| 11*cos(7.23*x³)+6.87 | 0 |

Aquí aparece el comportamiento que describes: con la frecuencia equivocada,
el ajuste lineal de salida reduce la amplitud para no equivocarse demasiado.
Ajustar amplitud no sustituye encontrar la frecuencia. El paisaje de error es
multimodal y la búsqueda local puede quedar atrapada.

Los puntos son finitos. Una señal que oscila muy rápido entre muestras tampoco
se reconstruye de forma única por mirar un dibujo: valida las predicciones en
los X del CSV y observa intervalos pequeños para comparar fases.

## 5. Cambios aplicados

- La interfaz muestra el predictor constante, su MSE y cuánto lo supera el
  mejor individuo. Si R² es cercano a cero, lo indica expresamente.
- Una línea gris discontinua identifica esa referencia en la gráfica.
- La interfaz arranca con altura 6 y permite añadir `^` al catálogo base sin
  activar todas las funciones científicas y sus restricciones de dominio.
- Los terminales sencillos incluyen 3 y 4. Al generar potencias se favorecen
  exponentes enteros; la mutación de un exponente terminal conserva esa
  condición. Así `x³` es alcanzable sin acertar exactamente 3 por azar continuo.
- El cálculo del MSE se conserva; no se aumenta artificialmente la puntuación
  de curvas que sólo parezcan más vistosas.

El diagnóstico está en `diagnostico.py`. La fórmula compatible aparece sólo en
esta explicación y su prueba de comprobación, no en la inicialización genética.

## 6. Cómo experimentar con parámetros

Para explorar este caso, una configuración de partida razonable es:

| Parámetro | Punto de partida |
|---|---|
| Operaciones | Base + potencias; no todo el catálogo de inicio |
| Altura | 7; prueba 8 sólo si no cabe la estructura requerida |
| Población | 300 |
| Generaciones | 300 |
| Selección | Torneo, tamaño 2 o 3 |
| Élite | 2 o 3 |
| Cruce | 0.85 |
| Mutación | 0.35 a 0.5 |
| Inmigración | 0.15 |
| Pesos terminal/operación/intercambio/subárbol | 40 / 20 / 0 / 40 |
| Métrica y tolerancia | NMSE, 0.01 (equivale a R² ≥ 0.99) |
| Refinamientos | Activos; amplitud/intercepto y constantes se ajustan localmente |
| Semillas | 7, 21, 42, comparando resultados |

Son hipótesis de búsqueda, no parámetros probados para garantizar recuperar
la función. El coste aumenta mucho con 2001 observaciones; revisa la evolución
y usa Detener si deja de progresar. `funcion_02.csv` permite una exploración
más rápida, pero el resultado debe comprobarse después contra el CSV denso:
menos puntos también permiten más soluciones espurias.

Si varias semillas mantienen NMSE cerca de 1, el problema continúa siendo de
estructura o exploración de frecuencia. No basta con cambiar MSE por RMSE ni
incrementar generaciones sin límite. Para garantizar la recuperación dentro de
una familia periódica haría falta declarar esa familia y realizar una búsqueda
global de su frecuencia; eso sería un método especializado adicional.

## 7. Criterio para decir que una búsqueda funcionó

Comprueba estas tres cosas por separado:

1. **Representación:** las operaciones y altura admiten el tipo de expresión.
2. **Optimización:** mejora de forma clara a la media y sigue reduciendo NMSE.
3. **Validación:** coincide en datos no usados para ajustar y reproduce bien la
   fase al mirar zonas pequeñas del intervalo.

Un error de entrenamiento pequeño no prueba que se recuperó la fórmula original.
Un R² cercano a cero tampoco se debe presentar como una solución satisfactoria.
