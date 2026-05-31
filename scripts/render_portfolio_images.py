#!/usr/bin/env python3
"""Render portfolio PNG diagrams for README and LinkedIn."""

from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise SystemExit("Install pillow: uv run --with pillow python scripts/render_portfolio_images.py") from exc

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "docs" / "images"
IMAGES.mkdir(parents=True, exist_ok=True)

FONT = ImageFont.load_default()


def _box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    label: str,
    fill: str,
    outline: str = "#333333",
) -> None:
    draw.rounded_rectangle(xy, radius=8, fill=fill, outline=outline, width=2)
    x0, y0, x1, y1 = xy
    tw, th = draw.textbbox((0, 0), label, font=FONT)[2:]
    draw.text(((x0 + x1 - tw) // 2, (y0 + y1 - th) // 2), label, fill="#111111", font=FONT)


def _arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int]) -> None:
    draw.line([start, end], fill="#555555", width=2)
    ex, ey = end
    if ex > start[0]:
        draw.polygon([(ex, ey), (ex - 10, ey - 5), (ex - 10, ey + 5)], fill="#555555")
    elif ey > start[1]:
        draw.polygon([(ex, ey), (ex - 5, ey - 10), (ex + 5, ey - 10)], fill="#555555")


def render_architecture() -> None:
    img = Image.new("RGB", (960, 520), "#ffffff")
    draw = ImageDraw.Draw(img)
    draw.text((24, 16), "FinOps AI Gateway — architecture", fill="#111111", font=FONT)

    _box(draw, (40, 80, 160, 130), "Client / CLI", "#e8f4fd")
    _box(draw, (220, 60, 400, 110), "Classifier\n(Groq)", "#fff3cd")
    _box(draw, (220, 130, 400, 180), "Hybrid RAG", "#d4edda")
    _box(draw, (440, 130, 560, 180), "Postgres\npgvector", "#f8d7da")
    _box(draw, (220, 210, 400, 260), "Tier router", "#fff3cd")
    _box(draw, (440, 210, 560, 260), "Ollama\n(simple)", "#d4edda")
    _box(draw, (440, 280, 560, 330), "Groq / Claude", "#f8d7da")
    _box(draw, (620, 130, 760, 180), "Pushgateway", "#e2e3e5")
    _box(draw, (620, 200, 760, 250), "Prometheus", "#e2e3e5")
    _box(draw, (620, 270, 760, 320), "Grafana", "#cfe2ff")
    _box(draw, (620, 340, 760, 390), "LangSmith", "#e2e3e5")

    _arrow(draw, (160, 105), (220, 85))
    _arrow(draw, (160, 105), (220, 155))
    _arrow(draw, (400, 155), (440, 155))
    _arrow(draw, (160, 105), (220, 235))
    _arrow(draw, (400, 235), (440, 235))
    _arrow(draw, (400, 235), (440, 305))
    _arrow(draw, (560, 155), (620, 155))
    _arrow(draw, (560, 235), (620, 225))
    _arrow(draw, (690, 180), (690, 200))
    _arrow(draw, (690, 250), (690, 270))

    out = IMAGES / "architecture.png"
    img.save(out)
    print(f"Wrote {out}")


def render_grafana_mock() -> None:
    img = Image.new("RGB", (800, 480), "#181b1f")
    draw = ImageDraw.Draw(img)
    draw.text((24, 16), "FinOps AI Gateway — Cost by Tier (USD total)", fill="#d8d9da", font=FONT)

    tiers = [
        ("simple", 0.0, "#73bf69"),
        ("medium", 0.004702, "#fade2a"),
        ("complex", 0.010395, "#f2495c"),
    ]
    max_val = 0.011
    x0, bar_top, bar_h = 80, 80, 280
    bar_w = 120
    gap = 60
    for i, (tier, cost, color) in enumerate(tiers):
        x = x0 + i * (bar_w + gap)
        height = int((cost / max_val) * bar_h) if max_val else 0
        y = bar_top + bar_h - height
        draw.rectangle([x, y, x + bar_w, bar_top + bar_h], fill=color)
        draw.text((x, bar_top + bar_h + 12), tier, fill="#d8d9da", font=FONT)
        draw.text((x, bar_top + bar_h + 28), f"${cost:.4f}", fill="#d8d9da", font=FONT)

    draw.text((24, 400), "Routing: simple 7 | medium 3 | complex 2  (58% local $0 tier)", fill="#8e8e8e", font=FONT)
    draw.text((24, 430), "Load test n=12 — see data/load_test_results.json", fill="#8e8e8e", font=FONT)

    out = IMAGES / "grafana-cost-by-tier.png"
    img.save(out)
    print(f"Wrote {out}")


def main() -> None:
    render_architecture()
    render_grafana_mock()


if __name__ == "__main__":
    main()
