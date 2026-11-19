# Arquitectura real y puntos de integración

```text
main.py                          Entrada y carga del QSS
src/app/main_window.py           Ventana, selección de algoritmo y fases
src/app/ui/grid.py               Tablero, eventos y dibujo
src/app/graph/node.py            Posición y tipo de celda
src/app/graph/graph.py           Nodos, aristas, vecinos y conversión
src/app/algorithms/{bfs,dfs}.py   Búsqueda pura: {visited, path}
src/app/simulation/controller.py Búsqueda, métricas y temporizador
src/app/entities/elements.py     Clases de entidades; actualmente sin integrar
src/app/utils/constants.py       Tamaño y tipos
src/assets/images/              Imágenes usadas por el tablero (ant, food, nest, obstacle, terrain)
src/assets/styles/pink.qss       Estilo principal
tests/                          Pruebas de grafos y algoritmos
docs/STATE.md                    Evidencia, bloqueos y siguiente tarea
ROADMAP.md                       Única lista de progreso
SPECIFICATIONS.md               Requisitos y alcance
AGENTS.md                        Reglas y ciclo de trabajo
```

## Flujo esperado

Interfaz → controlador → grafo/algoritmo → resultado → animación de la interfaz.
Los algoritmos ya están separados de PyQt6. El controlador usa `QTimer`.
La búsqueda completa se calcula de forma síncrona antes de animar; comprobar
respuesta de interfaz si en el futuro crecen los mapas.

## Contratos que requieren resolución

- Grafo: la conversión usa las constantes globales 20×20; las pruebas esperan
  que acepte un tablero 2×2. Elegir y documentar el contrato al corregir esa tarea.
- Tablero: el controlador espera `clear_simulation()`, `set_current(node_or_none)`,
  `set_visited(node)` y `set_path(path)`. Ninguno existe aún. La corrección debe
  definir estado visual y dibujo, no limitarse a métodos vacíos.
- Hormiga: las fases `TO_FOOD` y `TO_NEST` cambian etiquetas y objetivos,
  pero no actualizan la posición. Separar exploración, recorrido y recogida;
  no declarar éxito con `path=[]`.
- Reinicio: distinguir limpiar la exploración de reconstruir el mapa inicial;
  hoy ambas rutas llaman a un método ausente.
- Pausa/paso: el paso manual debe poder avanzar estando pausado sin reactivar
  automáticamente la reproducción. La lógica actual impide ese avance.

Mantener esta estructura; no renombrar módulos solo para hacerlos coincidir con
la estructura ideal que aparecía en documentos anteriores.
