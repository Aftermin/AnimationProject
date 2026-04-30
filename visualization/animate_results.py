"""
animate_results.py — Visualize benchmark results จาก experiments/results/runtime.csv
รัน: python visualization/animate_results.py
ต้องรัน benchmark.py ก่อนเพื่อสร้าง runtime.csv
"""
from __future__ import annotations

import sys, os, csv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "experiments", "results")
CSV_PATH    = os.path.join(RESULTS_DIR, "runtime.csv")
OUT_DIR     = os.path.join(RESULTS_DIR)
os.makedirs(OUT_DIR, exist_ok=True)

# ──────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────
def load_csv(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"ไม่พบ {path}\n"
            "กรุณารัน:  python experiments/benchmark.py  ก่อน"
        )
    ns, t_base, t_prop, speedups = [], [], [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            ns.append(int(row["n_particles"]))
            t_base.append(float(row["baseline_ms"]))
            t_prop.append(float(row["proposed_ms"]))
            speedups.append(float(row["speedup"]))
    return ns, t_base, t_prop, speedups


ns, t_base, t_prop, speedups = load_csv(CSV_PATH)

# ──────────────────────────────────────────────
# Theme helpers
# ──────────────────────────────────────────────
BG       = "#0f1117"
RED      = "#ff5050"
GREEN    = "#3cdc8c"
GREY     = "#282c3c"
WHITE    = "#e6e8f5"
SUBTEXT  = "#6e7391"

def style_ax(ax):
    ax.set_facecolor(BG)
    ax.tick_params(colors=WHITE, labelsize=9)
    ax.xaxis.label.set_color(WHITE)
    ax.yaxis.label.set_color(WHITE)
    ax.title.set_color(WHITE)
    for spine in ax.spines.values():
        spine.set_edgecolor(GREY)
    ax.grid(color=GREY, linestyle="--", linewidth=0.5)


# ══════════════════════════════════════════════
# Figure 1: Static 4-panel summary
# ══════════════════════════════════════════════
fig, axes = plt.subplots(2, 2, figsize=(13, 9))
fig.patch.set_facecolor(BG)
fig.suptitle("Particle Simulation — Baseline vs Proposed", color=WHITE,
             fontsize=14, fontweight="bold", y=0.98)

# Panel A — Runtime line chart
ax = axes[0, 0];  style_ax(ax)
ax.plot(ns, t_base, "o-", color=RED,   lw=2, label="Baseline O(N²)")
ax.plot(ns, t_prop, "o-", color=GREEN, lw=2, label="Proposed O(N)")
ax.set_title("A. Runtime vs Particle Count");  ax.set_xlabel("Particles");  ax.set_ylabel("ms / frame")
ax.legend(facecolor="#1c1f2e", labelcolor=WHITE, fontsize=9)

# Panel B — Speedup bar
ax = axes[0, 1];  style_ax(ax)
bars = ax.bar(range(len(ns)), speedups, color=GREEN, alpha=0.85, zorder=2)
ax.set_xticks(range(len(ns)))
ax.set_xticklabels([f"{n:,}" for n in ns], rotation=30, ha="right", fontsize=8)
ax.set_title("B. Speedup (Baseline / Proposed)");  ax.set_xlabel("Particles");  ax.set_ylabel("Speedup ×")
ax.axhline(1, color=RED, linestyle="--", lw=1)
for bar, sp in zip(bars, speedups):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
            f"{sp:.1f}×", ha="center", va="bottom", color=WHITE, fontsize=8)

# Panel C — Log-scale runtime
ax = axes[1, 0];  style_ax(ax)
ax.loglog(ns, t_base, "o-", color=RED,   lw=2, label="Baseline")
ax.loglog(ns, t_prop, "o-", color=GREEN, lw=2, label="Proposed")
# Reference lines
x_ref = np.array([ns[0], ns[-1]], dtype=float)
ax.loglog(x_ref, t_base[0] * (x_ref / ns[0]) ** 2, "--", color=RED,   lw=1, alpha=0.5, label="O(N²)")
ax.loglog(x_ref, t_prop[0] * (x_ref / ns[0]) ** 1, "--", color=GREEN, lw=1, alpha=0.5, label="O(N)")
ax.set_title("C. Log-Log Scaling");  ax.set_xlabel("Particles");  ax.set_ylabel("ms / frame (log)")
ax.legend(facecolor="#1c1f2e", labelcolor=WHITE, fontsize=9)

# Panel D — Memory estimate (O(N) vs O(N²) conceptual)
ax = axes[1, 1];  style_ax(ax)
x_mem = np.linspace(ns[0], ns[-1], 200)
mem_b = (x_mem / 1000) ** 2        # O(N²) relative units
mem_p = (x_mem / 1000) * 1.2       # O(N)
ax.fill_between(x_mem, mem_b, color=RED,   alpha=0.25)
ax.fill_between(x_mem, mem_p, color=GREEN, alpha=0.25)
ax.plot(x_mem, mem_b, color=RED,   lw=2, label="Baseline O(N²) pairs")
ax.plot(x_mem, mem_p, color=GREEN, lw=2, label="Proposed O(N) cells")
ax.set_title("D. Collision-Check Complexity");  ax.set_xlabel("Particles");  ax.set_ylabel("Relative work units")
ax.legend(facecolor="#1c1f2e", labelcolor=WHITE, fontsize=9)

plt.tight_layout()
out_static = os.path.join(OUT_DIR, "summary.png")
plt.savefig(out_static, dpi=150, bbox_inches="tight", facecolor=BG)
print(f"✅  Saved summary  → {out_static}")

# ══════════════════════════════════════════════
# Figure 2: Animated runtime bar race
# ══════════════════════════════════════════════
fig2, ax2 = plt.subplots(figsize=(9, 5))
fig2.patch.set_facecolor(BG)
style_ax(ax2)
ax2.set_title("Runtime Build-up: Baseline vs Proposed", color=WHITE)
ax2.set_xlabel("ms / frame");  ax2.set_ylabel("Particle Count")

labels = [f"{n:,}" for n in ns]

def animate(frame):
    ax2.clear();  style_ax(ax2)
    ax2.set_title("Runtime Build-up: Baseline vs Proposed", color=WHITE)
    ax2.set_xlabel("ms / frame");  ax2.set_ylabel("Particle Count")

    k = frame + 1
    t_b_part = t_base[:k];  t_p_part = t_prop[:k];  lbl = labels[:k]
    y = np.arange(k)

    ax2.barh(y - 0.2, t_b_part, height=0.35, color=RED,   label="Baseline")
    ax2.barh(y + 0.2, t_p_part, height=0.35, color=GREEN, label="Proposed")
    ax2.set_yticks(y);  ax2.set_yticklabels(lbl, color=WHITE)
    ax2.legend(facecolor="#1c1f2e", labelcolor=WHITE, fontsize=9)

    for i, (tb, tp) in enumerate(zip(t_b_part, t_p_part)):
        ax2.text(tb + 0.1, i - 0.2, f"{tb:.1f}", va="center", color=RED,   fontsize=8)
        ax2.text(tp + 0.1, i + 0.2, f"{tp:.1f}", va="center", color=GREEN, fontsize=8)

ani = animation.FuncAnimation(fig2, animate, frames=len(ns),
                               interval=600, repeat=False)
out_gif = os.path.join(OUT_DIR, "runtime_animation.gif")
ani.save(out_gif, writer="pillow", fps=1.5,
         savefig_kwargs={"facecolor": BG})
print(f"✅  Saved animation → {out_gif}")

plt.close("all")
print("\nDone! ตรวจสอบผลลัพธ์ที่ experiments/results/")