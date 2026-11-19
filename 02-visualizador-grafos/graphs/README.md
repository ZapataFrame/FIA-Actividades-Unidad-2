# Variante ponderada

La variante con valores negativos está incluida en `negative.json` y se carga
al iniciar como **Valores negativos**. Procede de la [segunda imagen](../assets/grafo-negativo.png),
con el nodo **666** en lugar de 66. Conserva los 30 nodos, las 63 aristas y
las posiciones del original; cambia únicamente estos ocho pesos:

| Arista | Peso |
| --- | ---: |
| 21–11 | −2 |
| 24–11 | −7 |
| 6–9 | −7 |
| 9–10 | −3 |
| 3–69 | −6 |
| 5–20 | −2 |
| 23–16 | −11 |
| 666–13 | −777 |

Se interpreta como no dirigido, siguiendo el original y la imagen sin flechas.
El grafo conectado tiene ciclos negativos: Bellman–Ford y Floyd–Warshall
marcan las distancias afectadas como `−∞`, sin ruta mínima finita.
Para cargar otra variante, importa un JSON desde la interfaz.

El JSON debe contener:

- `directed`: `true` para arcos con flechas; `false` para aristas no dirigidas.
- `nodes`: una lista de objetos con `id` entero y coordenadas finitas `x`, `y`.
- `edges`: una lista de triples `[origen, destino, peso]`. Los extremos deben
  existir en `nodes`; el peso debe ser un número finito, positivo, cero o negativo.

Los nodos no se repiten. Las aristas paralelas sí están permitidas. Para conservar
el grafo original, utiliza sus posiciones y etiquetas, incluido **666**, y cambia
únicamente los pesos que indique la nueva imagen. Indica explícitamente si también
cambian las direcciones.

Dijkstra y A* rechazan pesos negativos. Bellman–Ford calcula distancias y detecta
ciclos negativos alcanzables; los nodos afectados quedan con costo `−∞`. Un ciclo
negativo que no puede llegar al destino no invalida una ruta finita a ese destino.
En un grafo no dirigido, recorrer una arista negativa y volver por ella forma un
ciclo de costo negativo.

BFS y DFS siguen siendo recorridos; el voraz local no garantiza el mínimo. Fuerza
bruta compara **caminos simples**: con ciclos negativos, eso no representa el
problema de costo mínimo permitiendo recorridos repetidos. Su límite de pasos
sigue produciendo resultados provisionales.

## Versión dirigida

`directed-negative.json` corresponde a la [imagen con flechas](../assets/grafo-dirigido-negativo.png) y se carga como **Dirigido · pesos negativos**. Conserva 30 nodos, 63 arcos y los ocho pesos negativos, pero transcribe cada orientación por separado. No sustituye `negative.json`, que conserva la versión anterior no dirigida.

Algunas orientaciones relevantes: `21 → 29`, `11 → 21`, `11 → 24`, `6 → 7`, `15 → 6`, `0 → 15`, `1 → 0`, `2 → 3`, `17 → 2`, `69 → 5`, `16 → 17`, `666 → 12` y `13 → 12`. Las dos conexiones paralelas son `12 → 16 = 16` y `12 → 16 = 3`; se conserva `666 → 13 = −777`.

Esta versión no contiene ciclos negativos. De 29 a 13 la ruta mínima es **29 → 7 → 14 → 4 → 18 → 666 → 13**, de costo **−750**. Los pares inalcanzables conservan `∞`. Dijkstra y A* se deshabilitan por los pesos negativos; Bellman–Ford y Floyd–Warshall sí están disponibles.
