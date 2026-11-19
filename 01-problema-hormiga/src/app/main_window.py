from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel,
                             QPushButton, QHBoxLayout, QComboBox, QSlider, QApplication)
from PyQt6.QtGui import QDrag
from PyQt6.QtCore import Qt, QMimeData
from src.app.ui.grid import GridWidget
from src.app.simulation.controller import SimulationController
from src.app.algorithms.bfs import bfs
from src.app.algorithms.dfs import dfs
from src.app.graph.graph import Graph


class DraggableButton(QPushButton):
    """Botón que inicia un QDrag con su tipo de elemento al arrastrar,
    y además actúa como herramienta de colocación al hacer clic."""

    def __init__(self, text, element_type, tool_callback, parent=None):
        super().__init__(text, parent)
        self.element_type = element_type
        self.tool_callback = tool_callback
        self._press_pos = None
        self.clicked.connect(lambda: self.tool_callback(self.element_type))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._press_pos is not None:
            delta = event.position().toPoint() - self._press_pos
            if delta.manhattanLength() > QApplication.startDragDistance():
                drag = QDrag(self)
                mime_data = QMimeData()
                mime_data.setText(self.element_type)
                drag.setMimeData(mime_data)
                drag.exec(Qt.DropAction.CopyAction)
                self._press_pos = None
        super().mouseMoveEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AntGraphLab - Visual Search Lab")
        self.setMinimumSize(1100, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout(self.central_widget)

        self.left_panel = QWidget()
        self.left_panel.setFixedWidth(280)
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.title_label = QLabel("AntGraphLab")
        self.title_label.setObjectName("MainTitle")

        self.desc_label = QLabel("Haz clic en un elemento y luego en el tablero, o arráStralo. Click derecho borra.")
        self.desc_label.setWordWrap(True)

        self.palette_layout = QVBoxLayout()

        self.ant_btn = DraggableButton("🐜 Ant", "Ant", self.select_tool)
        self.food_btn = DraggableButton("🍎 Food", "Food", self.select_tool)
        self.nest_btn = DraggableButton("🏠 Nest", "Nest", self.select_tool)
        self.obs_btn = DraggableButton("🪨 Obstacle", "Obstacle", self.select_tool)

        for btn in (self.ant_btn, self.food_btn, self.nest_btn, self.obs_btn):
            self.palette_layout.addWidget(btn)

        self.algo_label = QLabel("Algorithm:")
        self.algo_selector = QComboBox()
        self.algo_selector.addItems(["BFS", "DFS"])

        self.start_button = QPushButton("Start Simulation")
        self.start_button.clicked.connect(self.run_simulation)

        self.pause_button = QPushButton("Pause/Resume")
        self.pause_button.clicked.connect(self.toggle_pause)

        self.step_button = QPushButton("Step Forward")
        self.step_button.clicked.connect(self.step_simulation)

        self.reset_button = QPushButton("Reset Simulation")
        self.reset_button.clicked.connect(self.reset_simulation)

        self.clear_map_button = QPushButton("Clear Map")
        self.clear_map_button.clicked.connect(self.clear_map)

        self.speed_label = QLabel("Speed:")
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(20)
        self.speed_slider.setMaximum(1000)
        self.speed_slider.setValue(30)
        self.speed_slider.setInvertedAppearance(True)
        self.speed_slider.valueChanged.connect(self.update_speed)

        self.metrics_label = QLabel("Metrics:\nNodes Visited: -\nPath Length: -\nTime: - ms")
        self.metrics_label.setWordWrap(True)
        self.metrics_label.setStyleSheet("font-weight: bold; color: #4A4453; background: #FFF5F7; padding: 10px; border: 1px solid #F4B6D2; border-radius: 5px;")

        for w in (self.title_label, self.desc_label):
            self.left_layout.addWidget(w)
        self.left_layout.addLayout(self.palette_layout)
        self.left_layout.addWidget(self.algo_label)
        self.left_layout.addWidget(self.algo_selector)
        self.left_layout.addWidget(self.start_button)
        self.left_layout.addWidget(self.pause_button)
        self.left_layout.addWidget(self.step_button)
        self.left_layout.addWidget(self.reset_button)
        self.left_layout.addWidget(self.clear_map_button)
        self.left_layout.addWidget(self.speed_label)
        self.left_layout.addWidget(self.speed_slider)
        self.left_layout.addWidget(self.metrics_label)
        self.left_layout.addStretch()

        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.grid_widget = GridWidget()
        self.right_layout.addWidget(self.grid_widget)

        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.right_panel)

        self.controller = None
        self.simulation_phase = "IDLE"
        self.active_tool = None
        self.totals = {"nodes_visited": 0, "path_length": 0, "execution_time": 0.0}

        # Sincronizar herramienta de colocación con el tablero
        self.active_tool = None
        self.grid_widget.set_placement_tool(None)
        self.grid_widget.on_tool_consumed = self._on_tool_consumed

    def _on_tool_consumed(self):
        self.desc_label.setText(f"Colocar: {self.active_tool} activo. Clic en el mapa para seguir colocando; elige otra herramienta para cambiar.")

    def select_tool(self, element_type):
        self.active_tool = element_type
        self.grid_widget.set_placement_tool(element_type)
        self.desc_label.setText(f"Colocar: {element_type}. Clic en el tablero.")

    def find_node_by_type(self, node_type):
        for row in self.grid_widget.grid:
            for node in row:
                if node.type == node_type:
                    return node
        return None

    def run_simulation(self):
        # Siempre reinicia desde cero: si una fase quedó activa o pausada,
        # se detiene y se lanza una nueva desde TO_FOOD.
        if self.controller:
            self.controller.stop()
            self.controller = None
        self.totals = {"nodes_visited": 0, "path_length": 0, "execution_time": 0.0}
        # Devolver el mapa a como lo dejó el usuario antes de volver a simular
        if self.grid_widget.snapshot is None:
            self.grid_widget.capture_snapshot()
        else:
            self.grid_widget.restore_snapshot()
        self.grid_widget.clear_simulation()
        self.simulation_phase = "TO_FOOD"
        self.start_cycle()

    def _collect_all_food_search(self, graph_ignored, start, goal_ignored):
        """Recorre TODOS los alimentos antes de pasar al hormiguero.

        De la posición actual va a la comida más cercana (según el algoritmo
        elegido), luego desde ahí a la siguiente, y así hasta agotarlas.
        Devuelve {"visited": ..., "path": ...} concatenados de todos los
        tramos, o ruta vacía si alguna comida es inalcanzable.
        """
        algo_name = self.algo_selector.currentText()
        algo_func = bfs if algo_name == "BFS" else dfs
        graph = Graph.convert_grid_to_graph(self.grid_widget.grid)
        remaining = list(self.find_foods())
        current = start
        visited_all = []
        path_all = []
        while remaining:
            best = None
            best_path = []
            best_visited = []
            for food in remaining:
                result = algo_func(graph, current, food)
                if result["path"] and (not best_path or len(result["path"]) < len(best_path)):
                    best = food
                    best_path = result["path"]
                    best_visited = result["visited"]
            if best is None:
                return {"visited": visited_all, "path": []}
            visited_all.extend(best_visited)
            if path_all:
                path_all.extend(best_path[1:])
            else:
                path_all.extend(best_path)
            current = best
            remaining.remove(best)
        return {"visited": visited_all, "path": path_all}

    def find_foods(self):
        foods = []
        for row in self.grid_widget.grid:
            for node in row:
                if node.type == "food":
                    foods.append(node)
        return foods

    def start_cycle(self):
        if self.controller:
            self.controller.stop()

        if self.simulation_phase == "TO_FOOD":
            ant = self.find_node_by_type("ant")
            if ant is not None:
                # La posición de la hormiga pasa a ant_cell; su tipo original
                # se libera para que el alimento/hormiguero no se sobrescriban.
                self.grid_widget.ant_cell = ant
                ant.type = "empty"
            start_node = ant
            candidates = self.find_foods()
            goal = candidates[0] if candidates else None
            goal_desc = "food"
        else:
            start_node = self.grid_widget.ant_cell
            goal = self.find_node_by_type("nest")
            goal_desc = "nest"

        if goal_desc == "food" and not candidates:
            self.desc_label.setText("Error: coloca al menos una comida antes de iniciar.")
            self.simulation_phase = "IDLE"
            return
        if start_node is None or goal is None:
            self.desc_label.setText("Error: coloca hormiga y " + goal_desc + " antes de iniciar.")
            self.simulation_phase = "IDLE"
            return

        algo_name = self.algo_selector.currentText()
        algo_func = bfs if algo_name == "BFS" else dfs
        if self.simulation_phase == "TO_FOOD":
            algo_func = self._collect_all_food_search

        self.controller = SimulationController(self.grid_widget, algo_func)
        self.controller.speed = self.speed_slider.value()
        self.controller.start(start_node, goal, on_complete=self.handle_phase_completion)

        status_text = "Searching for Food..." if self.simulation_phase == "TO_FOOD" else "Returning to Nest..."
        self.desc_label.setText(status_text)
        self.update_metrics_display()

    def handle_phase_completion(self):
        self.update_metrics_display()
        if not self.controller or not self.controller.final_path:
            self.desc_label.setText("No se encontró ruta. Revisa obstáculos y elementos.")
            self.simulation_phase = "IDLE"
            return

        if self.simulation_phase == "TO_FOOD":
            self.simulation_phase = "TO_NEST"
            self.desc_label.setText("Food collected! Returning to Nest...")
            self.start_cycle()
        else:
            self.simulation_phase = "FINISHED"
            self.desc_label.setText("Simulation Completed! Ant is home. 🏠")

    def update_metrics_display(self):
        if self.controller and self.controller.metrics:
            m = self.controller.metrics
            self.totals["nodes_visited"] += m["nodes_visited"]
            self.totals["path_length"] += m["path_length"]
            self.totals["execution_time"] += m["execution_time"]
            last_algo = m.get("algorithm", "?")
            self.controller.metrics = {}
            self.metrics_label.setText(
                f"Metrics (total, {last_algo.upper()}):\nNodes Visited: {self.totals['nodes_visited']}\n"
                f"Path Length: {self.totals['path_length']}\n"
                f"Time: {self.totals['execution_time']:.2f} ms"
            )
        elif self.simulation_phase == "IDLE":
            self.metrics_label.setText("Metrics:\nNodes Visited: -\nPath Length: -\nTime: - ms")

    def toggle_pause(self):
        if self.controller:
            paused = self.controller.toggle_pause()
            self.desc_label.setText("Simulation Paused" if paused else "Simulation Resumed")

    def step_simulation(self):
        if self.controller:
            self.controller.step()

    def update_speed(self, value):
        if self.controller:
            self.controller.set_speed(value)

    def reset_simulation(self):
        if self.controller:
            self.controller.stop()
            self.controller = None
        # Devolver hormiga, alimento y hormiguero a su posición original
        self.grid_widget.restore_snapshot()
        self.grid_widget.clear_simulation()
        self.simulation_phase = "IDLE"
        self.totals = {"nodes_visited": 0, "path_length": 0, "execution_time": 0.0}
        self.desc_label.setText("Map restored to original. Ready.")
        self.metrics_label.setText("Metrics:\nNodes Visited: -\nPath Length: -\nTime: - ms")
        self.active_tool = None
        self.grid_widget.set_placement_tool(None)

    def clear_map(self):
        if self.controller:
            self.controller.stop()
        self.grid_widget.clear_map()
        self.simulation_phase = "IDLE"
        self.desc_label.setText("Map cleared. Ready to build.")
        self.totals = {"nodes_visited": 0, "path_length": 0, "execution_time": 0.0}
        self.metrics_label.setText("Metrics:\nNodes Visited: -\nPath Length: -\nTime: - ms")
