# Estado actual de AntGraphLab

Actualizado: 2026-10-04. Código auditado: commit `63f81cd`.
Fases 1–6 implementadas y verificadas headless; Fases 7–8 verificadas
headless (sin QA visual de interacción). Fase activa pendiente de cierre
visual: QA con ventana real. Siguiente fase candidata: 9.

## Fase actual

**Fase 2 — Tablero.**
Próximo hito: verificar y completar la cuadrícula (`GridWidget`), incluyendo detección de posición, selección y drag & drop básico.
Hay implementaciones parciales de las fases 3–8; no constituyen fases terminadas.
El [roadmap](../ROADMAP.md) contiene las casillas; este archivo registra contexto.

## Evidencia de Fase 1 (completada)
- `MainWindow` importado, creado y cerrado sin errores.
- QSS cargado correctamente desde `src/assets/styles/pink.qss` (538 caracteres).
- Aplicación abre/cierra sin traceback.
- PyQt6 funcional en `.venv` (Python 3.12.3).

## Bloqueos, en orden
1. ~~pytest~~ Resuelto (instalado y declarado). Suite: 7 pasan.
2. ~~Conversión del grafo~~ Resuelto (dimensiones desde `grid_data`).
3. ~~Contrato tablero/controlador~~ Resuelto (4 métodos implementados y verificados).
4. ~~Paso manual~~ Resuelto (`manual=True`).
5. ~~Simulación de ida/regreso~~ Resuelto (2026-10-04, segunda sesión):
   el controlador ahora anima la exploración, luego mueve la hormiga celda a
   celda por `final_path`, recoge el alimento (la celda pasa a `ant`), y usa
   la posición de la hormiga como inicio del regreso. Ruta vacía no continúa:
   `handle_phase_completion` muestra error y vuelve a IDLE.
6. **QA visual real**: todo verificado con `QT_QPA_PLATFORM=offscreen`,
   eventos simulados y bucle manual de `_step_simulation()`. Falta ejecutar
   `.venv/bin/python main.py` con ventana visible y probar drag real.

## Evidencia de esta sesión (2026-10-04, parte 4)
- Varios alimentos: `UNIQUE_TYPES` ya no incluye `food`; se pueden colocar
  varios (probado 3). TO_FOOD elige el que el algoritmo alcance con ruta más
  corta (`_pick_best_goal`); al recogerlo desaparece y el resto permanecen.
- DFS atravesando el hormiguero: ya no borra la nest. La hormiga ahora se
  sigue con `grid_widget.ant_cell` y NO muta tipos de celda (solo el alimento
  recogido pasa a `empty`). Tras correr DFS la nest sigue en su sitio y el
  regreso TO_NEST la encuentra.
- Reset Simulation: restaura la copia del mapa (`snapshot`) tomada antes de
  simular — hormiga, alimento, hormiguero y obstáculos vuelven a su sitio —
  y deja `ant_cell=None`. Segunda ejecución funciona: `FINISHED` de nuevo.
- Bug "Start no ejecutaba tras fase activa": ya corregido en sesión previa y
  cubierto con esta prueba.
- Colocar elementos: herramienta de una sola colocación (clic) para evitar
  cambios accidentales al inspeccionar; el estado se refleja en `desc_label`.
- QSS: `QComboBox` blanco con selección rosa pastel (`#F7C8DD`).
- `pytest -q`: 7 pasan.
- Herramienta de colocación persistente: un clic en el elemento de la paleta
  la activa y luego los clics en el mapa colocan varias instancias hasta
  cambiar de herramienta.
- Fase TO_FOOD recorre TODOS los alimentos: `_collect_all_food_search`
  enlaza tramos (algoritmo elegido, comida más cercana primero) y la hormiga
  recoge cada una al pasar. Verificado: 3 comidas → `foods left: []`,
  ant en la nest, y segunda corrida tras Reset igual.

## Evidencia de esta sesión (2026-10-04, parte 3)
- Imágenes en el tablero: `terrain.png` de fondo en cada celda y
  `ant.png`, `food.png`, `hormiguero-2.png`, `obstacle.png` para cada tipo.
  Superposición semitransparente para visitado/actual/ruta/selección.
- Bug "Start no ejecuta tras limpiar": `run_simulation` ahora siempre detiene
  el controlador anterior, limpia la visualización y reinicia desde TO_FOOD
  (antes devolvía silenciosamente si una fase seguía marcada).
- Velocidad por defecto 100→30 ms: la exploración de un mapa 20×20 ya no
  parece congelada; dos corridas seguidas terminan en `FINISHED` con la
  hormiga en el hormiguero (verificado con bucle real de eventos).
- Herramienta de colocación de una sola vez; unicidad de hormiga/hormiguero
  verificada. (El alimento ahora admite varias instancias.)
- `pytest -q`: 7 pasan.

## Evidencia de esta sesión (2026-10-04, parte 2)
- Colocación por herramienta de clic: `select_tool` + `place_element`
  colocan `ant`/`food`/`nest`/`obstacle`; unicidad para ant/nest;
  clic derecho borra; `QDropEvent` también funciona (Drag&Drop desde la paleta).
- End-to-end headless: `run_simulation()` → ant (0,0) → alimento (4,0) →
  hormiguero (0,4); fase final `FINISHED`; métricas totales acumuladas
  (`Nodes Visited: 70`, `Path Length: 14`, algoritmo en etiqueta).
- `pytest -q`: 7 pasan.

## Evidencia de esta sesión (2026-10-04)
- `.venv/bin/python -m pytest -q`: 7 pasaron, 0 fallas (antes 6/7 directo).
- GridWidget: tamaño 600×600, rejilla 20×20, clic en celda (5,3) selecciona
  `Node(5, 3, empty)`.
- `QDropEvent` con texto `Obstacle` en celda (2,2) la marca como `obstacle`.
- Integración headless: `SimulationController`+BFS producen
  `visited_queue` de 11 nodos, ruta `(0,0)→(4,0)` y métricas; con
  `is_paused=True`, tres `step()` manuales avanzan a `current_step == 3`.
- GridWidget.clear_simulation() deja `visited`/`current`/`path` vacíos.

## Próxima tarea para el modelo pequeño
**Única tarea: QA visual con ventana real.**
Ejecutar `.venv/bin/python main.py`, colocar hormiga/alimento/hormiguero/
obstáculos arrastrando o clicando herramientas, ejecutar BFS y DFS con las
nuevas imágenes, pausar, paso a paso, velocidad, reiniciar y limpiar.
Registrar fallos; si todo va bien, cerrar y considerar Fase 9 (mapas).

## Cómo mantener el seguimiento con modelos pequeños
Pegar al iniciar cada tarea:
> Lee AGENTS.md, docs/STATE.md y ROADMAP.md. Trabaja solo en la próxima tarea
> indicada en el estado. Antes de editar, declara archivos y criterio de aceptación.
> Revisa los contratos con los módulos que consumen el cambio. Al terminar ejecuta
> la verificación, actualiza ROADMAP.md y docs/STATE.md con evidencia y elige una
> próxima tarea. Si falla, conserva la casilla pendiente y registra el bloqueo.
> No avances a otras fases ni hagas refactorizaciones adicionales.

Al cerrar cada entrega, conservar en este archivo: fecha/commit verificado,
fase activa, evidencia, bloqueos y **una** siguiente tarea. La actualización
no es automática: el agente debe efectuarla y el revisor debe comprobar el diff.
Si repite una solución sin nueva evidencia o modifica módulos ajenos, cerrar esa
tarea, guardar el error exacto y comenzar otra sesión con un alcance menor.

## Cambios locales preexistentes
`git status` mostraba ` D opencode.json` antes de la auditoría. Se preservó ese
borrado; no se restauró ni se modificó la configuración.

## README visual — versión main `8d09237`

Se renovó el README con capturas de la aplicación y assets existentes, sin emojis
ni sección de estado/guía. `docs/images/board.png` y `simulation.png` muestran
el escenario y el resultado con tres comidas. Se capturó la ventana real en
Wayland y se verificaron recogida, regreso y restauración; para las imágenes
publicadas se usó una ventana offscreen de 1160×800 con el mismo código y QSS,
sin modificar la aplicación. No se verificó drag real en esta tarea.
