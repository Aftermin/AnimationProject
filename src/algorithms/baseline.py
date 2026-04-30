from __future__ import annotations
import math
from typing import List

def resolve_collision(p1, p2, restitution: float = 0.85) -> None:
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    dist = math.hypot(dx, dy)
    min_dist = p1.radius + p2.radius

    if dist >= min_dist or dist == 0:
        return

    overlap = min_dist - dist
    nx = dx / dist  
    ny = dy / dist

    p1.x += nx * overlap * 0.5
    p1.y += ny * overlap * 0.5
    p2.x -= nx * overlap * 0.5
    p2.y -= ny * overlap * 0.5

    v_rel_n = (p1.vx - p2.vx) * nx + (p1.vy - p2.vy) * ny

    if v_rel_n >= 0:
        return

    impulse = v_rel_n * restitution
    p1.vx -= impulse * nx
    p1.vy -= impulse * ny
    p2.vx += impulse * nx
    p2.vy += impulse * ny


def update_baseline(particles: List, width: int, height: int) -> None:
    
    for p in particles:
        p.update(width, height)

    n = len(particles)
    for i in range(n):
        for j in range(i + 1, n):
            resolve_collision(particles[i], particles[j])