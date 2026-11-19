class Node:
    def __init__(self, x, y, node_type="empty"):
        self.x = x
        self.y = y
        self.type = node_type

    def __repr__(self):
        return f"Node({self.x}, {self.y}, {self.type})"
