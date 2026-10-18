"""Erzeugt eigene Welten-Logos (transparente PNGs) mit OFL-Schriften.

Aufruf (Python 3 + Pillow):
    mkdir -p fonts out
    curl -sLf -o fonts/Rye-Regular.ttf https://raw.githubusercontent.com/google/fonts/main/ofl/rye/Rye-Regular.ttf
    curl -sLf -o fonts/Creepster-Regular.ttf https://raw.githubusercontent.com/google/fonts/main/ofl/creepster/Creepster-Regular.ttf
    python3 make_logos.py fonts out

Schriften: siehe LIZENZ-Schriften.txt (SIL Open Font License 1.1).
"""
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = sys.argv[1]
OUT = sys.argv[2]
W = 800
MAX_BREITE = 640


def speichern(logo, path):
    """Auf höchstens 640 px Breite verkleinern und als Paletten-PNG (128 Farben) speichern."""
    if logo.width > MAX_BREITE:
        logo = logo.resize((MAX_BREITE, round(logo.height * MAX_BREITE / logo.width)), Image.LANCZOS)
    logo.quantize(colors=128, method=Image.Quantize.FASTOCTREE).save(path, optimize=True)
    print(path, logo.size)


def gradient_text(lines, top, bottom, outline, shadow, path, second_color=None):
    """lines: [(text, font, gap_after)] -> zentriertes Logo mit Verlauf, Kontur und Schatten."""
    pad = 24
    sizes = [ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), t, font=f, stroke_width=6) for t, f, _ in lines]
    height = sum(b[3] - b[1] + g for b, (_, _, g) in zip(sizes, lines)) + 2 * pad
    mask = Image.new("L", (W, height), 0)
    stroke = Image.new("L", (W, height), 0)
    md, sd = ImageDraw.Draw(mask), ImageDraw.Draw(stroke)
    y = pad
    for (text, font, gap), b in zip(lines, sizes):
        x = (W - (b[2] - b[0])) // 2 - b[0]
        sd.text((x, y - b[1]), text, font=font, fill=255, stroke_width=6, stroke_fill=255)
        md.text((x, y - b[1]), text, font=font, fill=255)
        y += b[3] - b[1] + gap

    grad = Image.new("RGBA", (W, height))
    gd = ImageDraw.Draw(grad)
    for row in range(height):
        t = row / max(1, height - 1)
        gd.line([(0, row), (W, row)], fill=tuple(int(a + (c - a) * t) for a, c in zip(top, bottom)) + (255,))

    logo = Image.new("RGBA", (W, height), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, height), shadow + (0,))
    sh.putalpha(stroke.filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * 0.85)))
    logo.alpha_composite(sh, (4, 6))
    ol = Image.new("RGBA", (W, height), outline + (255,))
    ol.putalpha(stroke)
    logo.alpha_composite(ol)
    fill = grad.copy()
    fill.putalpha(mask)
    logo.alpha_composite(fill)
    if second_color:
        # zweite Zeile einfarbig überdecken (z. B. Knochenweiß)
        y2 = pad + sizes[0][3] - sizes[0][1] + lines[0][2]
        m2 = mask.crop((0, y2 - 4, W, height))
        layer = Image.new("RGBA", m2.size, second_color + (255,))
        layer.putalpha(m2)
        logo.alpha_composite(layer, (0, y2 - 4))
    speichern(logo.crop(logo.getbbox()), path)


def rye(size):
    return ImageFont.truetype(f"{FONTS}/Rye-Regular.ttf", size)


def creep(size):
    return ImageFont.truetype(f"{FONTS}/Creepster-Regular.ttf", size)


gradient_text(
    [("BUD SPENCER", rye(92), 6), ("&", rye(54), 6), ("TERENCE HILL", rye(92), 0)],
    top=(255, 226, 140), bottom=(196, 120, 40), outline=(62, 32, 12), shadow=(0, 0, 0),
    path=f"{OUT}/bud-spencer-terence-hill.png",
)
gradient_text(
    [("HORROR", creep(170), 4), ("KLASSIKER", creep(84), 0)],
    top=(235, 40, 40), bottom=(110, 0, 0), outline=(20, 0, 0), shadow=(0, 0, 0),
    path=f"{OUT}/horror-klassiker.png", second_color=(236, 228, 210),
)
