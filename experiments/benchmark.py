"""
benchmark.py — Scaling test: Baseline O(N²) vs Proposed O(N)
รัน: python experiments/benchmark.py
ผลลัพธ์จะถูกบันทึกที่ experiments/results/runtime.csv และ experiments/results/plots.png
"""
from __future__ import annotations

import sys, os, time, csv, math, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from algorithms.baseline import update_baseline
from algorithms.proposed import update_proposed
from data_structures.spatial_hash import SpatialHash

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
SIZES        = [100, 500, 1_000, 2_000, 5_000, 10_000]   # ปรับได้
WARMUP_STEPS = 3
BENCH_STEPS  = 10
SIM_W        = 940
SIM_H        = 700
CELL_SIZE    = 20          # PARTICLE_RADIUS * 4

RESULTS_DIR  = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# ──────────────────────────────────────────────
# Minimal Particle (ไม่ต้องการ pygame)
# ──────────────────────────────────────────────
class _P:
    __slots__ = ("x", "y", "vx", "vy", "radius", "color", "trail")
    def __init__(self):
        self.x      = random.uniform(10, SIM_W - 10)
        self.y      = random.uniform(10, SIM_H - 10)
        speed       = random.uniform(2.0, 5.0)
        angle       = random.uniform(0, 6.2832)
        self.vx     = speed * math.cos(angle)
        self.vy     = speed * math.sin(angle)
        self.radius = 5
        self.color  = (100, 180, 255)
        self.trail  = []

    def update(self, width: int, height: int) -> None:
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8:
            self.trail.pop(0)
        self.vy += 0.15
        self.x  += self.vx
        self.y  += self.vy
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


def make_particles(n: int) -> list:
    return [_P() for _ in range(n)]


def bench(fn, *args, steps=BENCH_STEPS) -> float:
    """คืนค่าเวลาเฉลี่ย ms/frame"""
    for _ in range(WARMUP_STEPS):
        fn(*args)
    t0 = time.perf_counter()
    for _ in range(steps):
        fn(*args)
    return (time.perf_counter() - t0) / steps * 1000


# ──────────────────────────────────────────────
# Run benchmark
# ──────────────────────────────────────────────
rows = []
print(f"{'N':>8}  {'Baseline (ms)':>14}  {'Proposed (ms)':>14}  {'Speedup':>8}")
print("-" * 52)

for n in SIZES:
    sh = SpatialHash(CELL_SIZE)

    ps_b = make_particles(n)
    t_b  = bench(update_baseline, ps_b, SIM_W, SIM_H)

    ps_p = make_particles(n)
    t_p  = bench(update_proposed, ps_p, SIM_W, SIM_H, sh)

    speedup = t_b / t_p if t_p > 0 else float("inf")
    rows.append((n, t_b, t_p, speedup))
    print(f"{n:>8,}  {t_b:>14.2f}  {t_p:>14.2f}  {speedup:>7.2f}x")

# ──────────────────────────────────────────────
# Save CSV
# ──────────────────────────────────────────────
csv_path = os.path.join(RESULTS_DIR, "runtime.csv")
with open(csv_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["n_particles", "baseline_ms", "proposed_ms", "speedup"])
    w.writerows(rows)
print(f"\n✅  Saved CSV → {csv_path}")

# ──────────────────────────────────────────────
# Plot
# ──────────────────────────────────────────────
ns       = [r[0] for r in rows]
t_base   = [r[1] for r in rows]
t_prop   = [r[2] for r in rows]
speedups = [r[3] for r in rows]

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.patch.set_facecolor("#0f1117")
for ax in axes:
    ax.set_facecolor("#0f1117")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#282c3c")

# — Runtime comparison —
axes[0].plot(ns, t_base,  "o-", color="#ff5050", linewidth=2, label="Baseline O(N²)")
axes[0].plot(ns, t_prop,  "o-", color="#3cdc8c", linewidth=2, label="Proposed O(N)")
axes[0].set_title("Runtime vs Particle Count")
axes[0].set_xlabel("Number of Particles")
axes[0].set_ylabel("ms / frame")
axes[0].legend(facecolor="#1c1f2e", labelcolor="white")
axes[0].grid(color="#282c3c", linestyle="--", linewidth=0.5)

# — Speedup —
axes[1].bar(range(len(ns)), speedups, color="#3cdc8c", alpha=0.85)
axes[1].set_xticks(range(len(ns)))
axes[1].set_xticklabels([f"{n:,}" for n in ns], rotation=30, ha="right")
axes[1].set_title("Speedup (Baseline / Proposed)")
axes[1].set_xlabel("Number of Particles")
axes[1].set_ylabel("Speedup (×)")
axes[1].axhline(1, color="#ff5050", linestyle="--", linewidth=1)
axes[1].grid(color="#282c3c", linestyle="--", linewidth=0.5, axis="y")

plt.tight_layout()
plot_path = os.path.join(RESULTS_DIR, "plots.png")
plt.savefig(plot_path, dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print(f"✅  Saved plot  → {plot_path}")