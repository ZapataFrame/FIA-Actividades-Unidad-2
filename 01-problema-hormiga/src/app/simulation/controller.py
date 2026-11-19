from PyQt6.QtCore import QTimer
from src.app.graph.graph import Graph
import time


class SimulationController:
    def __init__(self, grid_widget, algorithm_func):
        self.grid_widget = grid_widget
        self.algorithm_func = algorithm_func
        self.timer = QTimer()
        self.timer.timeout.connect(self._step_simulation)

        self.visited_queue = []
        self.final_path = []
        self.current_step = 0
        self.is_paused = False
        self.speed = 30
        self.start_node = None
        self.goal_node = None
        self.on_phase_complete = None
        self.metrics = {}
        self.walking = False
        self.walk_index = 0

    def start(self, start_node, goal_node, on_complete=None):
        self.stop()
        self.on_phase_complete = on_complete
        self.start_node = start_node
        self.goal_node = goal_node
        self._run_search()

    def _run_search(self):
        grid_data = self.grid_widget.grid
        graph = Graph.convert_grid_to_graph(grid_data)

        start_time = time.perf_counter()
        result = self.algorithm_func(graph, self.start_node, self.goal_node)
        end_time = time.perf_counter()

        self.visited_queue = result["visited"]
        self.final_path = result["path"]
        self.current_step = 0
        self.walking = False
        self.walk_index = 0

        self.metrics = {
            "nodes_visited": len(self.visited_queue),
            "path_length": len(self.final_path),
            "execution_time": (end_time - start_time) * 1000,  # ms
            "algorithm": getattr(self.algorithm_func, "__name__", "?"),
        }

        self.grid_widget.clear_simulation()
        self.timer.start(self.speed)

    def _step_simulation(self, manual=False):
        if self.is_paused and not manual:
            return

        if not self.walking:
            if self.current_step < len(self.visited_queue):
                node = self.visited_queue[self.current_step]
                self.grid_widget.set_current(node)
                self.grid_widget.set_visited(node)
                self.current_step += 1
            else:
                self.walking = True
                self.walk_index = 0
                self.grid_widget.set_current(None)
                self.grid_widget.set_path(self.final_path)
        else:
            if self.walk_index < len(self.final_path):
                target = self.final_path[self.walk_index]
                # El alimento recogido desaparece; las celdas del hormiguero y
                # demás se conservan (la nest nunca se borra).
                if target.type == "food":
                    target.type = "empty"
                self.grid_widget.ant_cell = target
                self.grid_widget.update()
                self.walk_index += 1
            else:
                self.timer.stop()
                self.grid_widget.set_current(None)
                if self.on_phase_complete:
                    self.on_phase_complete()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        return self.is_paused

    def step(self):
        if self.is_paused:
            self._step_simulation(manual=True)

    def set_speed(self, ms):
        self.speed = ms
        if self.timer.isActive():
            self.timer.start(self.speed)

    def stop(self):
        self.timer.stop()
