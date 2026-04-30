from __future__ import annotations
from typing import List, Tuple, Dict

class SpatialHash:
    def __init__(self, cell_size: float) -> None:
        self.cell_size: float = cell_size
        self.cells: Dict[Tuple[int, int], list] = {}

    def _hash(self, x: float, y: float) -> Tuple[int, int]:
        return (int(x // self.cell_size), int(y // self.cell_size))


    def insert(self, particle) -> None:
        key = self._hash(particle.x, particle.y)
        if key not in self.cells:
            self.cells[key] = []
        self.cells[key].append(particle)

    def get_nearby(self, particle) -> List:
        hx, hy = self._hash(particle.x, particle.y)
        nearby: List = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                key = (hx + dx, hy + dy)
                if key in self.cells:
                    nearby.extend(self.cells[key])
        return nearby

    def query_radius(self, x: float, y: float, radius: float) -> List:
        r_cells = int(radius // self.cell_size) + 1
        cx, cy = self._hash(x, y)
        result: List = []
        r2 = radius * radius
        for dx in range(-r_cells, r_cells + 1):
            for dy in range(-r_cells, r_cells + 1):
                key = (cx + dx, cy + dy)
                if key in self.cells:
                    for p in self.cells[key]:
                        if (p.x - x) ** 2 + (p.y - y) ** 2 <= r2:
                            result.append(p)
        return result

    def clear(self) -> None:
        self.cells.clear()

    def __len__(self) -> int:
        return len(self.cells)