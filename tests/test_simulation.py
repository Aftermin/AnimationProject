"""
test_simulation.py — Unit tests สำหรับ Particle Simulation
รัน: python -m pytest tests/test_simulation.py -v
หรือ: python tests/test_simulation.py
"""
from __future__ import annotations

import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest
from algorithms.baseline import resolve_collision, update_baseline
from algorithms.proposed import update_proposed
from data_structures.spatial_hash import SpatialHash

SIM_W, SIM_H = 940, 700
CELL_SIZE     = 20


# ──────────────────────────────────────────────
# Minimal Particle stub
# ──────────────────────────────────────────────
class _P:
    __slots__ = ("x", "y", "vx", "vy", "radius", "color", "trail")
    def __init__(self, x=100.0, y=100.0, vx=0.0, vy=0.0, r=5):
        self.x, self.y   = x, y
        self.vx, self.vy = vx, vy
        self.radius      = r
        self.color       = (100, 180, 255)
        self.trail       = []

    def update(self, width: int, height: int) -> None:
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8:
            self.trail.pop(0)
        self.vy += 0.15
        self.x  += self.vx;  self.y += self.vy
        if self.x - self.radius < 0:
            self.vx = abs(self.vx) * 0.82;  self.x = self.radius
        elif self.x + self.radius > width:
            self.vx = -abs(self.vx) * 0.82; self.x = width - self.radius
        if self.y - self.radius < 0:
            self.vy = abs(self.vy) * 0.82;  self.y = self.radius
        elif self.y + self.radius > height:
            self.vy = -abs(self.vy) * 0.82; self.y = height - self.radius
            if abs(self.vy) < 0.8:
                self.vy = 0.0


# ══════════════════════════════════════════════
# SpatialHash tests
# ══════════════════════════════════════════════
class TestSpatialHash(unittest.TestCase):

    def test_insert_and_len(self):
        sh = SpatialHash(20)
        p1 = _P(10, 10);  p2 = _P(500, 500)
        sh.insert(p1);    sh.insert(p2)
        self.assertEqual(len(sh), 2)

    def test_clear(self):
        sh = SpatialHash(20)
        sh.insert(_P(10, 10))
        sh.clear()
        self.assertEqual(len(sh), 0)

    def test_get_nearby_finds_neighbor(self):
        sh = SpatialHash(20)
        p1 = _P(100, 100);  p2 = _P(105, 105)   # same cell
        sh.insert(p1);       sh.insert(p2)
        nearby = sh.get_nearby(p1)
        self.assertIn(p2, nearby)

    def test_get_nearby_misses_far(self):
        sh = SpatialHash(20)
        p1 = _P(100, 100);  p2 = _P(500, 500)   # different cells, far apart
        sh.insert(p1);       sh.insert(p2)
        nearby = sh.get_nearby(p1)
        self.assertNotIn(p2, nearby)

    def test_query_radius(self):
        sh = SpatialHash(20)
        p_near = _P(102, 102)
        p_far  = _P(300, 300)
        sh.insert(p_near);  sh.insert(p_far)
        result = sh.query_radius(100, 100, 15)
        self.assertIn(p_near, result)
        self.assertNotIn(p_far, result)

    def test_same_cell_multiple_particles(self):
        sh = SpatialHash(20)
        particles = [_P(10 + i, 10 + i) for i in range(5)]
        for p in particles:
            sh.insert(p)
        # ทุก particle อยู่ใน cell เดียวกัน
        self.assertEqual(len(sh), 1)


# ══════════════════════════════════════════════
# resolve_collision tests
# ══════════════════════════════════════════════
class TestResolveCollision(unittest.TestCase):

    def test_no_collision_when_far(self):
        p1 = _P(0, 0,   vx=1, vy=0)
        p2 = _P(100, 0, vx=-1, vy=0)
        vx1_before = p1.vx
        resolve_collision(p1, p2)
        self.assertAlmostEqual(p1.vx, vx1_before)  # ไม่เปลี่ยน

    def test_overlap_resolved(self):
        """หลัง resolve ระยะห่างต้อง >= min_dist"""
        p1 = _P(0,  0,  vx=2,  vy=0, r=5)
        p2 = _P(8,  0,  vx=-2, vy=0, r=5)   # overlap 2px
        resolve_collision(p1, p2)
        dist = math.hypot(p1.x - p2.x, p1.y - p2.y)
        self.assertGreaterEqual(dist, p1.radius + p2.radius - 1e-6)

    def test_approaching_velocities_reversed(self):
        """particle ที่วิ่งหากันต้องกระดอนออก"""
        p1 = _P(0, 0,  vx=3, vy=0, r=5)
        p2 = _P(8, 0,  vx=-3, vy=0, r=5)
        resolve_collision(p1, p2)
        # p1 ต้องถูกเบนออกทางซ้าย (vx ลดลงหรือกลับทาง)
        self.assertLess(p1.vx, 3)

    def test_same_position_no_crash(self):
        """dist == 0 ต้องไม่ raise"""
        p1 = _P(50, 50);  p2 = _P(50, 50)
        try:
            resolve_collision(p1, p2)
        except Exception as e:
            self.fail(f"resolve_collision raised {e} on zero distance")

    def test_separating_particles_not_affected(self):
        """particle ที่แยกออกจากกันแล้ว (v_rel_n >= 0) ไม่ควรถูก impulse"""
        p1 = _P(0, 0,  vx=-3, vy=0, r=5)   # กำลังแยกออก
        p2 = _P(8, 0,  vx= 3, vy=0, r=5)
        vx1_before = p1.vx
        resolve_collision(p1, p2)
        self.assertAlmostEqual(p1.vx, vx1_before, places=4)


# ══════════════════════════════════════════════
# update_baseline / update_proposed tests
# ══════════════════════════════════════════════
class TestUpdateFunctions(unittest.TestCase):

    def _make(self, n=30):
        return [_P(random.uniform(20, SIM_W - 20),
                   random.uniform(20, SIM_H - 20),
                   vx=random.uniform(-3, 3),
                   vy=random.uniform(-3, 3)) for _ in range(n)]

    def test_baseline_moves_particles(self):
        ps   = self._make()
        x0   = [p.x for p in ps]
        update_baseline(ps, SIM_W, SIM_H)
        moved = sum(1 for p, x in zip(ps, x0) if abs(p.x - x) > 0)
        self.assertGreater(moved, 0)

    def test_proposed_moves_particles(self):
        ps = self._make()
        x0 = [p.x for p in ps]
        sh = SpatialHash(CELL_SIZE)
        update_proposed(ps, SIM_W, SIM_H, sh)
        moved = sum(1 for p, x in zip(ps, x0) if abs(p.x - x) > 0)
        self.assertGreater(moved, 0)

    def test_boundary_containment_baseline(self):
        ps = self._make(50)
        for _ in range(30):
            update_baseline(ps, SIM_W, SIM_H)
        for p in ps:
            self.assertGreaterEqual(p.x, p.radius - 1e-3)
            self.assertLessEqual   (p.x, SIM_W - p.radius + 1e-3)
            self.assertGreaterEqual(p.y, p.radius - 1e-3)
            self.assertLessEqual   (p.y, SIM_H - p.radius + 1e-3)

    def test_boundary_containment_proposed(self):
        ps = self._make(50)
        sh = SpatialHash(CELL_SIZE)
        for _ in range(30):
            update_proposed(ps, SIM_W, SIM_H, sh)
        for p in ps:
            self.assertGreaterEqual(p.x, p.radius - 1e-3)
            self.assertLessEqual   (p.x, SIM_W - p.radius + 1e-3)
            self.assertGreaterEqual(p.y, p.radius - 1e-3)
            self.assertLessEqual   (p.y, SIM_H - p.radius + 1e-3)

    def test_proposed_clears_hash_each_frame(self):
        """SpatialHash ต้อง clear ทุก frame ไม่งั้น particle เก่าค้างอยู่"""
        ps = self._make(10)
        sh = SpatialHash(CELL_SIZE)
        update_proposed(ps, SIM_W, SIM_H, sh)
        count_after = sum(len(v) for v in sh.cells.values())
        self.assertEqual(count_after, len(ps))


# ══════════════════════════════════════════════
if __name__ == "__main__":
    unittest.main(verbosity=2)