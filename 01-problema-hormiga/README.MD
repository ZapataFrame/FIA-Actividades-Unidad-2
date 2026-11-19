<div align="center">

<img src="src/assets/images/ant.png" width="88" alt="Hormiga de AntGraphLab">

<h1>AntGraphLab</h1>

<p>Construye un mapa. Encuentra la comida. Vuelve a casa.</p>

<p><sub>Python · PyQt6 · BFS · DFS</sub></p>

</div>

<br>

![Tablero de AntGraphLab con tres comidas y obstáculos](docs/images/board.png)

Un laboratorio visual de grafos donde una hormiga recoge las comidas distribuidas
en el mapa y regresa al hormiguero. Construye el escenario y observa cómo cambia
el recorrido al elegir búsqueda en anchura o en profundidad.

<p align="center">
  <img src="src/assets/images/food.png" width="48" alt="Comida">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="src/assets/images/hormiguero-2.png" width="60" alt="Hormiguero">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="src/assets/images/obstacle.png" width="48" alt="Obstáculo">
</p>

## Explora

1. Selecciona un elemento y colócalo con un clic o arrástralo al tablero.
2. Distribuye varias comidas, una hormiga, un hormiguero y los obstáculos.
3. Elige **BFS** o **DFS** e inicia la simulación.

Puedes pausar, avanzar un paso y ajustar la velocidad. El clic derecho borra una
celda; **Reset Simulation** restaura el escenario y **Clear Map** vacía el tablero.

## Del mapa al recorrido

![Simulación completada: las tres comidas recogidas y la hormiga en el hormiguero](docs/images/simulation.png)

Los colores muestran la exploración y la ruta. Al terminar, el panel reúne los
nodos visitados, la longitud del recorrido y el tiempo de búsqueda.

## Ejecución

Desde la raíz del proyecto, en tu entorno virtual con PyQt6 instalado:

```bash
python main.py
```

---

<p align="center">
  <sub>Diego Eduardo Zapata Aguilar · Melissa Jazmin Torres Martinez · Georgina Reta Limas</sub>
</p>
