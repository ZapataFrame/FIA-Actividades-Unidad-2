from dataclasses import dataclass

@dataclass
class GridElement:
    name: str
    symbol: str
    color: str

class Ant(GridElement):
    def __init__(self):
        super().__init__("Ant", "🐜", "#4A4453")

class Food(GridElement):
    def __init__(self):
        super().__init__("Food", "🍎", "#FFB7B2")

class Nest(GridElement):
    def __init__(self):
        super().__init__("Nest", "🏠", "#B2E2F2")

class Obstacle(GridElement):
    def __init__(self):
        super().__init__("Obstacle", "🪨", "#CDB4DB")
