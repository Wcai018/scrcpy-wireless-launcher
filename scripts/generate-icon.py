"""
scrcpy-wireless-launcher :: 生成项目图标

设计：圆角深蓝渐变底 + 手机轮廓 + 投屏符号 + 无线信号波纹
输出：assets/icon.png (1024px) 与 assets/icon.ico (多尺寸)

用法： python scripts/generate-icon.py
"""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SIZE = 1024
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

C_TOP = (56, 89, 189)
C_BOTTOM = (28, 43, 110)
C_PHONE = (250, 251, 255)
C_SCREEN = (86, 190, 255)
C_ACCENT = (94, 234, 168)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def build() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # ---- 圆角渐变背景 ----
    grad = Image.new("RGBA", (1, SIZE))
    gdr = ImageDraw.Draw(grad)
    for y in range(SIZE):
        gdr.point((0, y), fill=lerp(C_TOP, C_BOTTOM, y / SIZE) + (255,))
    grad = grad.resize((SIZE, SIZE))

    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=210, fill=255)
    bg = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    bg.paste(grad, (0, 0), mask)
    img = Image.alpha_composite(img, bg)

    # ---- 手机机身 ----
    PW, PH = 400, 660
    px = (SIZE - PW) // 2 - 40
    py = (SIZE - PH) // 2 + 20

    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [px + 12, py + 18, px + PW + 12, py + PH + 18], radius=58, fill=(0, 0, 40, 110)
    )
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(22)))

    d = ImageDraw.Draw(img)
    d.rounded_rectangle([px, py, px + PW, py + PH], radius=58, fill=C_PHONE)

    M = 22
    d.rounded_rectangle([px + M, py + M, px + PW - M, py + PH - M], radius=40, fill=(20, 32, 70))

    # 屏幕上的投屏符号
    sx0, sy0 = px + M + 26, py + M + 120
    sx1, sy1 = px + PW - M - 26, py + M + 330
    d.rounded_rectangle([sx0, sy0, sx1, sy1], radius=16, outline=C_SCREEN, width=16)
    cx, cy, r = (sx0 + sx1) / 2, (sy0 + sy1) / 2, 62
    d.polygon([(cx - r * 0.5, cy - r), (cx - r * 0.5, cy + r), (cx + r * 0.85, cy)], fill=C_SCREEN)

    # 内容线
    for i, wf in enumerate((0.72, 0.46)):
        ly = py + M + 400 + i * 52
        d.rounded_rectangle(
            [sx0 + 8, ly, sx0 + 8 + (sx1 - sx0 - 16) * wf, ly + 22],
            radius=11, fill=(120, 140, 190),
        )

    # 听筒（左移，避开右上信号点）
    d.rounded_rectangle([px + PW / 2 - 105, py + 42, px + PW / 2 - 15, py + 54], radius=6,
                        fill=(170, 180, 205))

    # ---- 无线信号波纹 ----
    sig_cx, sig_cy = px + PW + 6, py + 34
    for rad, alpha in ((78, 255), (140, 215), (202, 165)):
        layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        ImageDraw.Draw(layer).arc(
            [sig_cx - rad, sig_cy - rad, sig_cx + rad, sig_cy + rad],
            start=278, end=362, fill=C_ACCENT + (alpha,), width=22,
        )
        img = Image.alpha_composite(img, layer)

    d = ImageDraw.Draw(img)
    dr = 26
    d.ellipse([sig_cx - dr, sig_cy - dr, sig_cx + dr, sig_cy + dr], fill=C_ACCENT)
    return img


def main() -> None:
    img = build()
    png = ASSETS / "icon.png"
    ico = ASSETS / "icon.ico"
    img.save(png, "PNG")
    img.save(ico, format="ICO", sizes=[(s, s) for s in (256, 128, 64, 48, 32, 16)])
    print(f"  [OK] {png}  ({os.path.getsize(png)} bytes)")
    print(f"  [OK] {ico}  ({os.path.getsize(ico)} bytes)")


if __name__ == "__main__":
    main()
