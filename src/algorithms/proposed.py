from __future__ import annotations
from typing import List

from algorithms.baseline import resolve_collision
from data_structures.spatial_hash import SpatialHash

def update_proposed(
    particles: List,
    width: int,
    height: int,
    spatial_hash: SpatialHash,
) -> None:

    for p in particles:
        p.update(width, height)

    spatial_hash.clear()
    for p in particles:
        spatial_hash.insert(p)

    for p1 in particles:
        neighbors = spatial_hash.get_nearby(p1)
        for p2 in neighbors:
            if id(p1) < id(p2):
                resolve_collision(p1, p2)