# Especificaciones de AntGraphLab

## 1. Descripción

AntGraphLab es una aplicación de escritorio para construir escenarios visuales y observar cómo distintos algoritmos de búsqueda recorren un grafo.

El escenario representa una hormiga que debe:

```text
Hormiga
   ↓
Encontrar alimento
   ↓
Recoger alimento
   ↓
Regresar al hormiguero
```

La hormiga deberá evitar obstáculos y encontrar una ruta válida de acuerdo con el algoritmo seleccionado.

---

## 2. Objetivos

El proyecto debe permitir:

- construir mapas visualmente;
- representar el mapa mediante grafos;
- ejecutar algoritmos de búsqueda;
- visualizar el proceso de exploración;
- mostrar la ruta final encontrada;
- comparar posteriormente diferentes estrategias.

---

## 3. Interfaz

La aplicación será desarrollada utilizando:

```text
Python + PyQt6
```

La ventana principal deberá contar como mínimo con:

- tablero;
- selector de elementos;
- selector de algoritmo;
- botón para iniciar;
- opción para reiniciar el escenario.

Opcionalmente podrán incluirse:

- pausa;
- avance paso a paso;
- velocidad de animación.

---

## 4. Constructor de mapas

El usuario podrá construir un escenario utilizando drag & drop o herramientas equivalentes.

Elementos iniciales:

```text
🐜 Hormiga
🍎 Alimento
🏠 Hormiguero
🪨 Obstáculo
```

El sistema debe permitir modificar fácilmente la distribución del escenario.

---

## 5. Representación del mapa

El tablero podrá utilizar visualmente una cuadrícula.

Internamente deberá poder interpretarse como un grafo.

Cada posición válida podrá representar un nodo.

Las conexiones entre nodos representan los movimientos disponibles para la hormiga.

Los obstáculos deben impedir el desplazamiento.

---

## 6. Algoritmos

La primera versión debe considerar:

### BFS

Búsqueda en anchura.

Debe permitir explorar el escenario por niveles y encontrar una ruta mínima cuando todas las conexiones tengan el mismo costo.

### DFS

Búsqueda en profundidad.

Debe permitir demostrar visualmente una estrategia diferente de exploración.

---

## 7. Algoritmos futuros

La arquitectura debe permitir integrar posteriormente algoritmos como:

- Dijkstra;
- A*;
- Greedy Best First Search;
- algoritmos relacionados con colonias de hormigas.

Estos algoritmos no forman parte obligatoria de la primera versión.

---

## 8. Visualización

Mientras un algoritmo se ejecuta, la interfaz deberá mostrar visualmente:

```text
Nodo sin visitar
Nodo visitado
Nodo actual
Ruta encontrada
```

La exploración debe producir una animación progresiva.

Cuando la búsqueda finalice, la ruta seleccionada debe quedar resaltada.

---

## 9. Simulación

La ejecución deberá dividirse conceptualmente en dos búsquedas:

```text
Hormiga → Alimento
```

y posteriormente:

```text
Alimento → Hormiguero
```

Una simulación será exitosa cuando ambas rutas puedan completarse.

Si no existe una ruta válida, la interfaz deberá indicarlo.

---

## 10. Estadísticas

Opcionalmente, una simulación podrá mostrar:

- algoritmo utilizado;
- nodos visitados;
- longitud de la ruta;
- tiempo de ejecución.

Estas métricas podrán utilizarse posteriormente para comparar algoritmos.

---

## 11. Mapas

Inicialmente el usuario podrá crear escenarios dentro de la aplicación.

Como funcionalidad futura se podrá implementar:

```text
Guardar mapa
Cargar mapa
```

Los mapas guardados podrán almacenarse dentro de:

```text
maps/saved/
```

---

## 12. Diseño visual

La aplicación utilizará un estilo pastel.

Acento principal:

```text
Rosa pastel
#E8A0BF
```

La interfaz debe ser:

- limpia;
- sencilla;
- amigable;
- visualmente consistente.

---

## 13. Restricciones

La primera versión debe evitar complejidad innecesaria.

No son requisitos iniciales:

- inteligencia artificial generativa;
- integración obligatoria con Ollama;
- múltiples agentes autónomos;
- Cython;
- algoritmos avanzados;
- almacenamiento en base de datos.

Estas funcionalidades podrán explorarse posteriormente.

---

## 14. Criterio mínimo de funcionamiento

Una primera versión funcional deberá permitir:

1. abrir AntGraphLab;
2. construir un mapa sencillo;
3. colocar una hormiga;
4. colocar alimento;
5. colocar un hormiguero;
6. colocar obstáculos;
7. seleccionar BFS o DFS;
8. ejecutar la búsqueda;
9. visualizar los nodos explorados;
10. visualizar la ruta resultante.
