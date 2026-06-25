"""Render SVG to PNG for LaTeX (Playwright headless Chromium)."""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def render_svg(svg_path: Path, png_path: Path, scale: float = 2.0) -> None:
    svg = svg_path.read_text(encoding="utf-8", errors="replace")
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{ margin: 0; background: white; }}
  svg {{ display: block; }}
</style></head>
<body>{svg}</body></html>"""
    png_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 400})
        page.set_content(html, wait_until="networkidle")
        page.locator("svg").screenshot(path=str(png_path), type="png")
        browser.close()


if __name__ == "__main__":
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    render_svg(src, dst)
    print(dst, dst.stat().st_size)
