from __future__ import annotations
import random
import math
import time
import pygame

from algorithms.baseline import update_baseline
from algorithms.proposed import update_proposed
from data_structures.spatial_hash import SpatialHash

WIDTH, HEIGHT     = 1200, 700
PANEL_W           = 260
SIM_W             = WIDTH - PANEL_W   

PARTICLE_RADIUS   = 5
CELL_SIZE         = PARTICLE_RADIUS * 4
INIT_COUNT        = 200
MAX_PARTICLES     = 5000
ADD_PER_CLICK     = 30
FPS_CAP           = 0                       

GRAVITY           = 0.15                     
RESTITUTION_WALL  = 0.82                     
TRAIL_LENGTH      = 8                        

BG_SIM            = (15,  17,  23)
BG_PANEL          = (20,  22,  30)
BG_PANEL_CARD     = (28,  31,  42)
ACCENT_BASELINE   = (255,  80,  80)
ACCENT_PROPOSED   = ( 60, 220, 140)
COL_TEXT_HI       = (230, 232, 245)
COL_TEXT_LO       = (110, 115, 145)
COL_DIVIDER       = ( 40,  44,  60)


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "radius", "color", "trail")

    def __init__(self, x: float, y: float) -> None:
        self.x      = x
        self.y      = y
        speed       = random.uniform(2.0, 5.0)
        angle       = random.uniform(0, 6.2832)
        self.vx     = speed * math.cos(angle)
        self.vy     = speed * math.sin(angle)
        self.radius = PARTICLE_RADIUS
        self.trail: list = []

        r = random.randint(60, 140)
        g = random.randint(100, 200)
        b = random.randint(200, 255)
        self.color  = (r, g, b)

    def update(self, width: int, height: int) -> None:
        self.trail.append((self.x, self.y))
        if len(self.trail) > TRAIL_LENGTH:
            self.trail.pop(0)

        self.vy += GRAVITY

        self.x += self.vx
        self.y += self.vy

        if self.x - self.radius < 0:
            self.vx = abs(self.vx) * RESTITUTION_WALL
            self.x  = self.radius
        elif self.x + self.radius > width:
            self.vx = -abs(self.vx) * RESTITUTION_WALL
            self.x  = width - self.radius

        if self.y - self.radius < 0:
            self.vy = abs(self.vy) * RESTITUTION_WALL
            self.y  = self.radius
        elif self.y + self.radius > height:
            self.vy = -abs(self.vy) * RESTITUTION_WALL
            self.y  = height - self.radius

            if abs(self.vy) < 0.8:
                self.vy = 0.0


def draw_ball(surf: pygame.Surface, p: Particle) -> None:
    """วาด particle แบบสมจริง: trail → glow → base → shadow → highlight"""
    ix, iy = int(p.x), int(p.y)
    r      = p.radius
    cr, cg, cb = p.color

    n_trail = len(p.trail)
    for i, (tx, ty) in enumerate(p.trail):
        ratio     = (i + 1) / (n_trail + 1)          # 0 → 1
        trail_r   = max(1, int(r * ratio * 0.65))
        alpha     = ratio * 0.35
        col       = (int(cr * alpha), int(cg * alpha), int(cb * alpha))
        pygame.draw.circle(surf, col, (int(tx), int(ty)), trail_r)

    glow_col = (max(0, cr - 140), max(0, cg - 100), max(0, cb - 60))
    pygame.draw.circle(surf, glow_col, (ix, iy), r + 4)

    pygame.draw.circle(surf, p.color, (ix, iy), r)

    shadow_col = (max(0, cr - 90), max(0, cg - 90), max(0, cb - 60))
    pygame.draw.circle(surf, shadow_col,
                       (ix + r // 3, iy + r // 3), r - 1)

    hl_x = ix - r // 3
    hl_y = iy - r // 3
    hl_r = max(1, r // 3)
    pygame.draw.circle(surf, (255, 255, 255), (hl_x, hl_y), hl_r)

    pygame.draw.circle(surf, (200, 220, 255),
                       (hl_x + 1, hl_y + 1), max(1, hl_r - 1))


def draw_text(surf, font, text, x, y, color=COL_TEXT_HI):
    surf.blit(font.render(text, True, color), (x, y))


def draw_card(surf, x, y, w, h, color=BG_PANEL_CARD, radius=8):
    pygame.draw.rect(surf, color, (x, y, w, h), border_radius=radius)


def draw_bar(surf, x, y, w, h, frac, color):
    pygame.draw.rect(surf, COL_DIVIDER, (x, y, w, h), border_radius=4)
    filled = max(1, int(w * min(frac, 1.0)))
    pygame.draw.rect(surf, color, (x, y, filled, h), border_radius=4)


def draw_panel(surf, fonts, state: dict) -> None:
    f_sm  = fonts["sm"]
    f_md  = fonts["md"]
    f_lg  = fonts["lg"]

    px = SIM_W + 12
    pw = PANEL_W - 24
    y  = 16

    draw_text(surf, f_lg, "Particle Sim", px, y, COL_TEXT_HI);  y += 28
    draw_text(surf, f_sm, "2110512 Computer Animation",
              px, y, COL_TEXT_LO);                               y += 30

    pygame.draw.line(surf, COL_DIVIDER, (px, y), (px + pw, y)); y += 12

    algo    = state["algo"]
    is_prop = algo == "proposed"
    a_color = ACCENT_PROPOSED if is_prop else ACCENT_BASELINE
    a_label = "PROPOSED  O(N)" if is_prop else "BASELINE  O(N²)"

    draw_card(surf, px, y, pw, 44, BG_PANEL_CARD)
    pygame.draw.rect(surf, a_color, (px, y, 4, 44), border_radius=2)
    draw_text(surf, f_md, a_label,              px + 14, y + 6,  a_color)
    draw_text(surf, f_sm, "Spatial Hashing" if is_prop else "Brute-force",
              px + 14, y + 26, COL_TEXT_LO);                     y += 58

    stats = [
        ("Particles",      f"{state['n_particles']:,}"),
        ("Compute",        f"{state['compute_ms']} ms"),
        ("True FPS",       f"{state['fps']:.1f}"),
        ("Occupied cells", f"{state['cells']:,}"),
    ]
    for label, value in stats:
        draw_card(surf, px, y, pw, 48, BG_PANEL_CARD)
        draw_text(surf, f_sm, label, px + 10, y + 6,  COL_TEXT_LO)
        draw_text(surf, f_md, value, px + 10, y + 24, COL_TEXT_HI)
        y += 56

    pygame.draw.line(surf, COL_DIVIDER, (px, y), (px + pw, y)); y += 12

    draw_text(surf, f_sm, "Particle load", px, y, COL_TEXT_LO);  y += 18
    draw_bar(surf, px, y, pw, 10,
             state["n_particles"] / MAX_PARTICLES, a_color);      y += 26
    draw_text(surf, f_sm,
              f"{state['n_particles']} / {MAX_PARTICLES}",
              px, y, COL_TEXT_LO);                                y += 32

    pygame.draw.line(surf, COL_DIVIDER, (px, y), (px + pw, y)); y += 14

    history = state["fps_history"]
    if len(history) > 1:
        draw_text(surf, f_sm, "FPS history", px, y, COL_TEXT_LO); y += 18
        max_h = 40
        bar_w = max(1, pw // len(history))
        max_v = max(history) or 1
        for i, v in enumerate(history):
            bh = int(max_h * v / max_v)
            pygame.draw.rect(surf, a_color,
                             (px + i * bar_w, y + max_h - bh, bar_w - 1, bh))
        y += max_h + 10

    pygame.draw.line(surf, COL_DIVIDER, (px, y), (px + pw, y)); y += 14

    hints = [
        ("[SPACE]", "สลับอัลกอริทึม"),
        ("[CLICK]", f"เพิ่ม {ADD_PER_CLICK} particles"),
        ("[R]",     "รีเซ็ต"),
        ("[ESC]",   "ออก"),
    ]
    for key, desc in hints:
        draw_text(surf, f_sm, key,  px,      y, a_color)
        draw_text(surf, f_sm, desc, px + 72, y, COL_TEXT_LO)
        y += 20

def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Particle Collision — 2110512")
    clock  = pygame.time.Clock()

    fonts = {
        "sm": pygame.font.SysFont("segoeui", 14),
        "md": pygame.font.SysFont("segoeui", 18, bold=True),
        "lg": pygame.font.SysFont("segoeui", 22, bold=True),
        "xl": pygame.font.SysFont("segoeui", 28, bold=True),
    }

    sim_surf = pygame.Surface((SIM_W, HEIGHT))

    def make_particles(n: int) -> list:
        return [
            Particle(random.randint(20, SIM_W - 20),
                     random.randint(20, HEIGHT - 20))
            for _ in range(n)
        ]

    particles    = make_particles(INIT_COUNT)
    spatial_hash = SpatialHash(CELL_SIZE)

    algo         = "baseline"
    fps_history: list[float] = []
    MAX_HIST     = 80

    running = True
    while running:
        clock.tick(FPS_CAP) if FPS_CAP else clock.tick(10000)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    algo = "proposed" if algo == "baseline" else "baseline"
                if event.key == pygame.K_r:
                    particles = make_particles(INIT_COUNT)
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if mx < SIM_W and len(particles) < MAX_PARTICLES:
                    for _ in range(ADD_PER_CLICK):
                        particles.append(
                            Particle(
                                mx + random.uniform(-10, 10),
                                my + random.uniform(-10, 10),
                            )
                        )

        t0 = time.perf_counter()
        if algo == "proposed":
            update_proposed(particles, SIM_W, HEIGHT, spatial_hash)
        else:
            update_baseline(particles, SIM_W, HEIGHT)
        compute_ms = int((time.perf_counter() - t0) * 1000)

        fps = clock.get_fps()
        fps_history.append(fps)
        if len(fps_history) > MAX_HIST:
            fps_history.pop(0)

        sim_surf.fill(BG_SIM)
        for p in particles:
            draw_ball(sim_surf, p)

        screen.blit(sim_surf, (0, 0))

        pygame.draw.rect(screen, BG_PANEL, (SIM_W, 0, PANEL_W, HEIGHT))
        pygame.draw.line(screen, COL_DIVIDER,
                         (SIM_W, 0), (SIM_W, HEIGHT), 1)

        cells_used = len(spatial_hash) if algo == "proposed" else 0
        draw_panel(screen, fonts, {
            "algo":        algo,
            "n_particles": len(particles),
            "compute_ms":  compute_ms,
            "fps":         fps,
            "cells":       cells_used,
            "fps_history": fps_history,
        })

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()