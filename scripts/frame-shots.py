#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["pillow>=10"]
# ///
"""Frame raw simulator screenshots into App Store marketing shots.

One command between "I captured screens" and "I can run upload_shots":
each raw PNG becomes a store-sized canvas with a headline over a dark
gradient and the screenshot inset below it, rounded and shadowed.

Usage:
  frame-shots.py --raw <dir of PNGs> --out <dir> [--captions captions.txt]
                 [--size 1320x2868] [--bg 0B0912] [--accent E8720C]

captions.txt: one line per shot, "filename_stem|Headline text".
A stem with no line gets no headline, just the framed screenshot.
"""
import argparse
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont


def hex_rgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def font(size):
    for name in ("/System/Library/Fonts/SFNSRounded.ttf",
                 "/System/Library/Fonts/SFNS.ttf",
                 "/System/Library/Fonts/Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def frame(raw, out_path, size, bg, accent, headline):
    W, H = size
    canvas = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(canvas)
    # vertical gradient: bg at top -> slightly lifted at bottom
    top, bottom = bg, tuple(min(255, c + 14) for c in bg)
    for y in range(H):
        t = y / H
        row = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (W, y)], fill=row)

    # headline block
    inset_top = int(H * 0.055)
    if headline:
        f = font(int(W * 0.062))
        words, lines, line = headline.split(), [], ""
        for w in words:
            probe = (line + " " + w).strip()
            if draw.textlength(probe, font=f) > W * 0.86 and line:
                lines.append(line); line = w
            else:
                line = probe
        lines.append(line)
        y = inset_top
        for ln in lines:
            tw = draw.textlength(ln, font=f)
            draw.text(((W - tw) / 2, y), ln, font=f, fill=(240, 236, 228))
            y += int(W * 0.075)
        # accent underline, sized to the last line
        tw = draw.textlength(lines[-1], font=f)
        draw.rectangle([(W - tw) / 2, y + 6, (W + tw) / 2, y + 12], fill=accent)
        inset_top = y + int(H * 0.03)

    # the screenshot: scaled, rounded, shadowed, bottom-bled
    shot = Image.open(raw).convert("RGB")
    target_w = int(W * 0.86)
    ratio = target_w / shot.width
    shot = shot.resize((target_w, int(shot.height * ratio)), Image.LANCZOS)
    radius = int(W * 0.055)
    mask = Image.new("L", shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, shot.width, shot.height],
                                           radius=radius, fill=255)
    sx = (W - shot.width) // 2
    # soft shadow
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [sx - 8, inset_top + 10, sx + shot.width + 8, inset_top + shot.height + 26],
        radius=radius, fill=(0, 0, 0, 140))
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    canvas.paste(shadow, (0, 0), shadow)
    canvas.paste(shot, (sx, inset_top + 14), mask)

    canvas.save(out_path, "PNG")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--captions")
    ap.add_argument("--size", default="1320x2868")
    ap.add_argument("--bg", default="0B0912")
    ap.add_argument("--accent", default="E8720C")
    args = ap.parse_args()

    size = tuple(int(x) for x in args.size.lower().split("x"))
    bg, accent = hex_rgb(args.bg), hex_rgb(args.accent)
    captions = {}
    if args.captions:
        for line in pathlib.Path(args.captions).read_text().splitlines():
            if "|" in line:
                k, v = line.split("|", 1)
                captions[k.strip()] = v.strip()

    raw_dir, out_dir = pathlib.Path(args.raw), pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    pngs = sorted(raw_dir.glob("*.png"))
    if not pngs:
        sys.exit(f"no PNGs in {raw_dir}")
    for p in pngs:
        frame(p, out_dir / p.name, size, bg, accent, captions.get(p.stem, ""))
        print(f"framed {p.name}")


if __name__ == "__main__":
    main()
