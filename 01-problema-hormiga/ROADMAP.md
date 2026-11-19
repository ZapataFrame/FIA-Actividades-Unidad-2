# Roadmap — AntGraphLab

Actualizado: 2026-10-04. Base auditada: commit `6259b09`.
Estado detallado y próxima tarea: [docs/STATE.md](docs/STATE.md).

**Fase activa: QA visual / Fase 9 (Mapas).** Fases 1–8 implementadas y
verificadas headless; pendiente QA con ventana real. Estado detallado y
próxima tarea: [docs/STATE.md](docs/STATE.md).

Leyenda: `[x]` comprobado; `[ ]` pendiente, parcial o bloqueado. Verificación
de lógica con pytest: 7 pruebas pasan (`.venv/bin/python -m pytest -q`).
QA visual pendiente; integración comprobada headless (offscreen).

El desarrollo de AntGraphLab se dividirá en etapas pequeñas para mantener el proyecto funcional durante todo el proceso.

---

# Fase 1 — Base del proyecto

### Objetivo

Crear una aplicación mínima ejecutable.

### Tareas

- [x] Crear estructura de directorios. — Verificada en `src/app/`, `src/assets/` y `tests/`.
- [x] Configurar entorno virtual. — `.venv/` existe; Python 3.14.7 verificado.
- [x] Crear `requirements.txt`. — Existe; solo fija PyQt6 6.6.1. Falta declarar herramientas de prueba.
- [x] Instalar PyQt6. — Verificado: importación exitosa y ventana abre correctamente.
- [x] Crear `main.py`. — Punto de entrada presente; apertura verificada en sesión previa.
- [x] Crear ventana principal. — Verificado: MainWindow se importa, crea y cierra correctamente.
- [x] Integrar estilo rosa pastel. — QSS cargado correctamente desde `src/assets/styles/pink.qss`.
- [x] Crear pruebas básicas. — Suite pytest funcional: 7 pasan. pytest declarado en `requirements.txt`.

### Resultado

```text
AntGraphLab abre correctamente
y muestra una ventana principal.
```

---

# Fase 2 — Tablero

### Objetivo

Crear el área visual donde se construirán los escenarios.

Nota: desde 2026-10-04 el tablero dibuja `terrain.png` y las imágenes
`ant.png`, `food.png`, `hormiguero-2.png`, `obstacle.png`; los colores se
mantienen como superposición semitransparente de estado (visitado, actual, ruta).

### Tareas

- [x] Crear cuadrícula. — `GridWidget` verificado headless: 600×600, 20×20.
- [x] Representar las celdas como nodos. — Controlado: cuadrícula lógica 20×20.
- [x] Detectar posición de cada celda. — Clic en celda (5,3) selecciona ese nodo.
- [x] Crear sistema de obstáculos. — `QDropEvent` marca `obstacle`; el grafo
  los excluye (prueba 2×2 pasa).
- [x] Implementar selección de elementos. — Paleta→`QDrag`→`dropEvent` verificado
  con `QDropEvent` simulado; falta QA con gesto real.
- [x] Implementar drag & drop. — `dragEnterEvent`/`dropEvent` verificados
  headless; sin QA visual del gesto real.

### Elementos

- [x] Hormiga. — Tipo y colocación verificados (drop y asignación directa).
- [x] Alimento. — Tipo y colocación verificados.
- [x] Hormiguero. — Tipo y colocación verificados.
- [x] Obstáculo. — Tipo, colocación y exclusión del grafo verificados.

### Resultado

El usuario puede construir visualmente un escenario.

---

# Fase 3 — Modelo de grafos

### Objetivo

Separar el tablero visual de su representación lógica.

### Tareas

- [x] Crear estructura `Graph`. — Pruebas directas de nodos y aristas pasan.
- [x] Crear estructura `Node`. — Utilizada por las comprobaciones de lógica.
- [x] Detectar vecinos. — Pruebas directas de adyacencia pasan.
- [x] Ignorar obstáculos. — `test_get_neighbors_obstacle` pasa por invocación directa.
- [x] Convertir tablero a grafo. — Dimensiona según `grid_data`; prueba 2×2 pasa y 20×20 sigue funcionando.
- [x] Crear pruebas del grafo. — 4 pruebas de grafo; suite completa: 7 pasan con pytest.

### Resultado

```text
Tablero visual
      ↓
     Grafo
```

---

# Fase 4 — Algoritmos

### Objetivo

Implementar los primeros algoritmos de búsqueda.

### BFS

- [x] Implementar BFS. — Camino mínimo en 3×3 y 20×20 comprobado por ejecución directa.
- [x] Registrar nodos visitados. — `visited` sin duplicados, verificado en controlador headless.
- [x] Reconstruir ruta. — Extremos comprobados en pruebas directas; inicio=destino también comprobado para BFS y DFS.
- [x] Crear pruebas. — Cobertura parcial; ahora ejecutables con pytest (7 pasan), falta completar casos por algoritmo.

### DFS

- [x] Implementar DFS. — Camino entre extremos en 3×3 comprobado por ejecución directa.
- [x] Registrar nodos visitados. — `visited` sin duplicados, verificado en controlador headless.
- [x] Reconstruir ruta. — Extremos comprobados en pruebas directas; inicio=destino también comprobado para BFS y DFS.
- [x] Crear pruebas. — Cobertura parcial; ahora ejecutables con pytest (7 pasan), falta completar casos por algoritmo.

### Resultado

Los algoritmos funcionan independientemente de la interfaz.

---

# Fase 5 — Visualización

### Objetivo

Mostrar cómo trabaja cada algoritmo.

### Tareas

- [x] Colorear nodos visitados. — Implementado con color propio e integrado al controlador.
- [x] Resaltar nodo actual. — Implementado con color propio.
- [x] Animar exploración. — QTimer+controlador verificados headless.
- [x] Resaltar ruta final. — Implementado con color propio.
- [x] Permitir reiniciar visualización. — `clear_simulation` implementado y verificado.
- [x] Evitar bloqueos de interfaz. — Animación por QTimer; búsqueda síncrona rápida en 20×20.

### Resultado

El usuario puede observar paso a paso cómo se explora el mapa.

---

# Fase 6 — Comportamiento de la hormiga

### Objetivo

Completar la simulación principal.

### Flujo

```text
🐜 Hormiga
    ↓
buscar
    ↓
🍎 Alimento
    ↓
buscar
    ↓
🏠 Hormiguero
```

### Tareas

- [x] Buscar ruta hacia el alimento. — Verificado headless: ant llega al alimento.
- [x] Animar desplazamiento. — El controlador mueve la celda `ant` por la ruta.
- [x] Detectar recolección. — La celda del alimento pasa a `ant` al llegar.
- [x] Buscar ruta hacia el hormiguero. — La hormiga movida es el inicio de TO_NEST.
- [x] Animar regreso. — Verificado: ant termina en el hormiguero.
- [x] Mostrar simulación completada. — Ruta vacía muestra error y no avanza; éxito muestra mensaje.

---

# Fase 7 — Controles

### Objetivo

Mejorar la interacción con la simulación.

### Tareas

- [x] Iniciar. — Botón presente; flujo headless verificado con BFS.
- [x] Pausar. — `toggle_pause` verificado headless.
- [x] Reiniciar. — `reset_simulation` verificado headless (clear_simulation ya existe).
- [x] Avanzar paso a paso. — `step()` ahora avanza con `manual=True` aunque esté pausado; verificado: 3 pasos → current_step 3.
- [x] Controlar velocidad. — El nuevo controlador toma el valor del slider; `set_speed` activo durante marcha.
- [x] Cambiar algoritmo. — BFS/DFS seleccionables; métricas muestran algoritmo usado.

---

# Fase 8 — Comparación de algoritmos

### Objetivo

Mostrar diferencias entre las estrategias disponibles.

### Métricas

- [x] Nodos visitados. — Acumulados entre fases en métricas totales.
- [x] Longitud de ruta. — Cuenta nodos de la ruta; acumulada entre fases.
- [x] Tiempo de ejecución. — perf_counter mostrado en métricas.
- [x] Algoritmo utilizado. — Incluido en la etiqueta de métricas.

### Posibles algoritmos adicionales

- [ ] Dijkstra.
- [ ] A*.
- [ ] Greedy Best First Search.

---

# Fase 9 — Mapas

### Objetivo

Permitir reutilizar escenarios.

### Tareas

- [ ] Guardar mapas.
- [ ] Cargar mapas.
- [ ] Crear formato de archivo.
- [ ] Agregar mapas de ejemplo.

---

# Fase 10 — Experimentación

Esta etapa es opcional y dependerá del avance del proyecto.

### Posibilidades

- [ ] Integrar Cython.
- [ ] Comparar rendimiento Python/Cython.
- [ ] Experimentar con algoritmos de colonia de hormigas.
- [ ] Crear escenarios más grandes.
- [x] Permitir múltiples alimentos. — Implementado: colocación múltiple,
  la simulación recoge TODOS antes del hormiguero (tramos enlazados), y
  Reset restaura todas.
- [ ] Permitir múltiples hormigas.
- [ ] Añadir diferentes costos de terreno.
- [ ] Investigar integración de agentes.

---

# Primera versión objetivo

Para considerar que existe una versión inicial funcional de **AntGraphLab**, deben completarse como mínimo:

```text
Fase 1
   ↓
Fase 2
   ↓
Fase 3
   ↓
Fase 4
   ↓
Fase 5
   ↓
Fase 6
```

Esto dará como resultado una aplicación capaz de:

```text
Construir mapa
     ↓
Seleccionar algoritmo
     ↓
Ejecutar búsqueda
     ↓
Visualizar exploración
     ↓
Encontrar alimento
     ↓
Regresar al hormiguero
```

Las fases posteriores deben considerarse mejoras y extensiones.

## Documentación visual

- [x] Renovar README con capturas de `main`, assets originales y presentación
  minimalista; retirar emojis y la sección de estado/guía del README.
  Evidencia: escenario de tres comidas, simulación completada y restauración;
  capturas en `docs/images/`. Código de aplicación sin cambios.
