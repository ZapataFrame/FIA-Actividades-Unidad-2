from pathlib import Path

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QDrag, QPixmap, QBrush
from PyQt6.QtCore import Qt, QRect, QMimeData
from src.app.graph.node import Node
from src.app.utils.constants import GRID_ROWS, GRID_COLS, CELL_SIZE, TYPE_OBSTACLE

IMAGES_DIR = Path(__file__).resolve().parents[2] / "assets" / "images"

TYPE_MAP = {
    "Ant": "ant",
    "Food": "food",
    "Nest": "nest",
    "Obstacle": TYPE_OBSTACLE,
}
UNIQUE_TYPES = ("ant", "nest")

IMAGE_FILES = {
    "terrain": "terrain.png",
    "ant": "ant.png",
    "food": "food.png",
    "nest": "hormiguero-2.png",
    TYPE_OBSTACLE: "obstacle.png",
}


class GridWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(GRID_COLS * CELL_SIZE, GRID_ROWS * CELL_SIZE)
        self.setAcceptDrops(True)

        self.grid = []
        for r in range(GRID_ROWS):
            row = []
            for c in range(GRID_COLS):
                row.append(Node(c, r))
            self.grid.append(row)

        self.selected_node = None
        self.placement_tool = None
        self.visited_nodes = set()
        self.current_node = None
        self.path_nodes = []
        self.ant_cell = None
        self.snapshot = None  # tipos del mapa tal y como los dejó el usuario
        self.on_tool_consumed = None

        self.pixmaps = {}
        for key, filename in IMAGE_FILES.items():
            pixmap = QPixmap(str(IMAGES_DIR / filename))
            if not pixmap.isNull():
                self.pixmaps[key] = pixmap.scaled(
                    CELL_SIZE, CELL_SIZE,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

    def set_placement_tool(self, tool):
        self.placement_tool = tool

    def node_at_position(self, x, y):
        col = int(x // CELL_SIZE)
        row = int(y // CELL_SIZE)
        if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
            return self.grid[row][col]
        return None

    def place_element(self, node, element_type):
        if node is None:
            return
        node_type = TYPE_MAP.get(element_type)
        if node_type is None:
            return
        if node_type in UNIQUE_TYPES:
            for row in self.grid:
                for n in row:
                    if n.type == node_type:
                        n.type = "empty"
        node.type = node_type
        if node_type == "ant":
            self.ant_cell = None
        self.snapshot = None  # el usuario editó el mapa: invalidar copia anterior
        self.update()

    def capture_snapshot(self):
        self.snapshot = [[n.type for n in row] for row in self.grid]

    def restore_snapshot(self):
        if self.snapshot is None:
            return
        for r, row in enumerate(self.grid):
            for c, n in enumerate(row):
                n.type = self.snapshot[r][c]
        self.ant_cell = None
        self.update()

    def clear_cell(self, node):
        if node is not None:
            node.type = "empty"
            if node is self.ant_cell:
                self.ant_cell = None
            self.snapshot = None
            self.update()

    def clear_map(self):
        for row in self.grid:
            for n in row:
                n.type = "empty"
        self.ant_cell = None
        self.snapshot = None
        self.clear_simulation()

    def clear_simulation(self):
        self.visited_nodes = set()
        self.current_node = None
        self.path_nodes = []
        self.update()

    def set_visited(self, node):
        self.visited_nodes.add(node)
        self.update()

    def set_current(self, node):
        self.current_node = node
        self.update()

    def set_path(self, path):
        self.path_nodes = list(path) if path else []
        self.update()

    def mousePressEvent(self, event):
        pos = event.position()
        node = self.node_at_position(pos.x(), pos.y())
        if event.button() == Qt.MouseButton.LeftButton:
            if self.placement_tool and node is not None:
                self.place_element(node, self.placement_tool)
                # La herramienta sigue activa: seguir clicando en el mapa
                # coloca más elementos del mismo tipo.
                if self.on_tool_consumed:
                    self.on_tool_consumed()
            else:
                self.selected_node = node
                self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.clear_cell(node)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        pos = event.position()
        node = self.node_at_position(pos.x(), pos.y())
        if node is not None:
            self.place_element(node, event.mimeData().text())
            event.acceptProposedAction()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor("#F4B6D2"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                rect = QRect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                node = self.grid[r][c]

                # Fondo: terreno para todas las celdas
                if "terrain" in self.pixmaps:
                    painter.drawPixmap(rect, self.pixmaps["terrain"])
                else:
                    painter.fillRect(rect, QColor("#FFF5F7"))

                # Imagen del elemento de la celda
                pixmap_key = node.type if node.type in self.pixmaps else None
                if pixmap_key in self.pixmaps:
                    painter.drawPixmap(rect, self.pixmaps[pixmap_key])

                # Hormiga durante la simulación (no muta el tipo de la celda)
                if node is self.ant_cell and "ant" in self.pixmaps:
                    painter.drawPixmap(rect, self.pixmaps["ant"])

                # Superposición semitransparente del estado de simulación
                overlay = None
                if node == self.current_node:
                    overlay = QColor(255, 214, 165, 160)
                elif node in self.path_nodes and node.type != "ant" and node is not self.ant_cell:
                    overlay = QColor(202, 255, 191, 160)
                elif node in self.visited_nodes:
                    overlay = QColor(253, 255, 182, 140)
                elif node == self.selected_node:
                    overlay = QColor(247, 200, 221, 140)
                if overlay is not None:
                    painter.fillRect(rect, overlay)

                painter.drawRect(rect)

        painter.end()
