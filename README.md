# Efficient Particle Simulation with Spatial Hashing

**Course:** 2110512 Computer Animation  
**Semester:** เทอมปลาย 2568

---

## Problem

Particle collision detection แบบ Brute-force มี Time Complexity O(N²)
ทำให้ช้ามากเมื่อจำนวน particle เพิ่มขึ้น ไม่สามารถรัน real-time ได้เมื่อ N > 1,000

## Approach

- **Baseline:** Brute-force O(N²) — ตรวจทุกคู่ particle
- **Proposed:** Spatial Hashing O(N) — แบ่ง space เป็น grid cells ตรวจเฉพาะ neighbor cells

## Results

| N Particles | Baseline (ms/frame) | Proposed (ms/frame) |    Speedup |
| ----------: | ------------------: | ------------------: | ---------: |
|         100 |                0.60 |                0.15 |      3.96× |
|         500 |               14.82 |                0.85 |     17.50× |
|       1,000 |               60.12 |                2.18 |     27.61× |
|       2,000 |              244.55 |                5.65 |     43.25× |
|       5,000 |            1,523.30 |               24.62 |     61.88× |
|      10,000 |            6,185.05 |               79.73 | **77.57×** |

- **Max Speedup:** 77.57× ที่ 10,000 particles
- **Stability:** particles อยู่ใน boundary ทุก frame ไม่มี tunneling
- Baseline ที่ 10,000 particles ใช้เวลา ~6.2 วินาที/frame (ใช้งาน real-time ไม่ได้)
- Proposed ที่ 10,000 particles ใช้เวลา ~80 ms/frame (~12 FPS)

## How to Run

```bash
pip install -r requirements.txt

# Main simulation (interactive)
python src/main.py

# Benchmark / Scaling test
python experiments/benchmark.py

# Unit tests
python -m pytest tests/test_simulation.py -v

# Visualize results (ต้องรัน benchmark ก่อน)
python visualization/animate_results.py
```

### Controls (main simulation)

| Key / Action | ผล                                   |
| ------------ | ------------------------------------ |
| `SPACE`      | สลับระหว่าง Baseline และ Proposed    |
| `Click`      | เพิ่ม 30 particles ตรงตำแหน่งที่คลิก |
| `R`          | รีเซ็ต simulation                    |
| `ESC`        | ออกจากโปรแกรม                        |

## Project Structure

```
AnimationProject/
├── README.md
├── requirements.txt
├── report/
│   └── final_report.pdf
├── src/
│   ├── main.py
│   ├── algorithms/
│   │   ├── baseline.py
│   │   └── proposed.py
│   └── data_structures/
│       └── spatial_hash.py
├── experiments/
│   ├── benchmark.py
│   └── results/
│       ├── runtime.csv
│       ├── plots.png
│       └── summary.png
├── visualization/
│   └── animate_results.py
├── demo/
│   └── README.md
└── tests/
    └── test_simulation.py
```

## Keywords

Particle Simulation, Spatial Hashing, Collision Detection, Real-time Animation, O(N) Algorithm
