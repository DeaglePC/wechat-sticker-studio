#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10.4,<14"]
# ///
"""Build a chat-size transparent GIF from a horizontal strip of three animation keys."""

import argparse
import io
import os
import sys
import tempfile
from itertools import pairwise
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

LANCZOS = Image.Resampling.LANCZOS
WORK_SIZE = 480


def extract_keys(source):
    with Image.open(source) as raw:
        image = raw.convert("RGBA")
    mask = image.getchannel("A").point(lambda a: 255 if a >= 100 else 0)
    if mask.getextrema() != (0, 255) or image.width < 2 * image.height:
        raise ValueError("提供一行三格的透明 PNG，格与格之间留透明间隔")
    occupied, _ = mask.getprojection()
    cuts = [0]
    for n in (1, 2):
        mid = round(image.width * n / 3)
        span = image.width // 10
        gaps = [x for x in range(mid - span, mid + span) if not occupied[x]]
        if not gaps:
            raise ValueError(f"第 {n} 条分界线穿过主体，请拉开关键姿势的间距")
        cuts.append(min(gaps, key=lambda x: abs(x - mid)))
    cuts.append(image.width)
    keys = []
    for left, right in pairwise(cuts):
        cell = image.crop((left, 0, right, image.height))
        box = cell.getchannel("A").point(lambda a: 255 if a >= 100 else 0).getbbox()
        if not box:
            raise ValueError("一格中缺少可见角色")
        keys.append(cell.crop(box))
    return keys


def make_caption(text, font_path):
    layer = Image.new("RGBA", (WORK_SIZE, WORK_SIZE))
    if not text:
        return layer
    draw = ImageDraw.Draw(layer)
    for size in range(72, 31, -2):
        font = ImageFont.truetype(str(font_path), size)
        left, _, right, bottom = draw.textbbox((0, 0), text, font=font)
        if right - left < WORK_SIZE - 40:
            break
    else:
        raise ValueError("台词太长，缩成一句能读清的短句")
    x = (WORK_SIZE - right + left) / 2 - left
    y = 458 - bottom
    draw.text(
        (x, y + 2),
        text,
        font=font,
        fill="#152740",
        stroke_width=8,
        stroke_fill="#fff8e9",
    )
    draw.text(
        (x, y), text, font=font, fill="#fff8e9", stroke_width=5, stroke_fill="#152740"
    )
    return layer


def compose(keys, caption, lean, hold):
    has_caption = caption.getbbox() is not None
    baseline = 394 if has_caption else 459
    scale = min(
        423 / max(k.width for k in keys), (baseline - 28) / max(k.height for k in keys)
    )
    # Hold the expressive key and spend fewer frames in the return.
    beats = [
        (0, 0, 1, 170),
        (0, -0.2, 0.985, 70),
        (1, 0.35, 1, 100),
        (1, 0.55, 1.016, 90),
        (1, 0.2, 1, 70),
        (2, 1, 1.03, 80),
        (2, 0.45, 1.014, 100),
        (2, 0.15, 1, hold),
        (2, 0, 0.992, 90),
        (1, 0, 1, 100),
        (0, 0, 0.99, 80),
    ]
    frames = []
    times = []
    for index, amount, zoom, ms in beats:
        key = keys[index]
        size = tuple(max(1, round(edge * scale * zoom)) for edge in key.size)
        art = ImageOps.expand(key.resize(size, LANCZOS), border=5, fill=(0, 0, 0, 0))
        outline = Image.new("RGBA", art.size, "#fff9e9")
        outline.putalpha(art.getchannel("A").filter(ImageFilter.MaxFilter(5)))
        outline.alpha_composite(art)
        art = outline.rotate(lean * amount, Image.Resampling.BICUBIC, expand=True)
        art = art.crop(art.getbbox())
        art.thumbnail((450, baseline - 14), LANCZOS)
        x = (WORK_SIZE - art.width) // 2
        y = max(10, round(baseline - art.height - amount * 5))
        frame = Image.new("RGBA", (WORK_SIZE, WORK_SIZE))
        frame.alpha_composite(art, (x, y))
        frame.alpha_composite(caption)
        frames.append(frame.resize((240, 240), LANCZOS))
        times.append(ms)
    return frames, times


def encode(frames, times, colors):
    strip = Image.new("RGB", (240 * len(frames), 240), "#fff8e9")
    for i, frame in enumerate(frames):
        strip.paste(frame, (240 * i, 0), frame.getchannel("A"))
    shared = strip.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    palette = shared.getpalette()[: colors * 3]
    palette += palette[:3] * ((768 - len(palette)) // 3)
    shared.putpalette(palette)
    indexed = []
    for frame in frames:
        pic = frame.convert("RGB").quantize(palette=shared, dither=Image.Dither.NONE)
        pic = pic.point([i if i < colors else 0 for i in range(256)])
        pic.putpalette(palette)
        transparent = frame.getchannel("A").point(lambda a: 255 if a < 128 else 0)
        pic.paste(255, (0, 0), transparent)
        indexed.append(pic)
    out = io.BytesIO()
    indexed[0].save(
        out,
        "GIF",
        save_all=True,
        append_images=indexed[1:],
        duration=times,
        disposal=2,
        loop=0,
        transparency=255,
        background=255,
        optimize=False,
    )
    return out.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("strip", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--caption", default="")
    parser.add_argument("--font", type=Path, help="已获授权且包含台词字符的 TTF/OTF")
    parser.add_argument(
        "--lean", type=float, default=2, help="动作高峰的角度，建议 -5 到 5"
    )
    parser.add_argument("--hold-ms", type=int, default=340)
    parser.add_argument("--frames-dir", type=Path, help="选填，导出编号 PNG 帧到新目录")
    args = parser.parse_args()
    if args.caption and not args.font:
        parser.error("有台词时请指定 --font")
    if not 50 <= args.hold_ms <= 3000 or not -12 <= args.lean <= 12:
        parser.error("--hold-ms 支持 50～3000，--lean 支持 -12～12")
    if (
        args.output.suffix.lower() != ".gif"
        or args.strip.resolve() == args.output.resolve()
    ):
        parser.error("输出应为独立的 .gif 文件")
    try:
        keys = extract_keys(args.strip)
        frames, times = compose(
            keys, make_caption(args.caption, args.font), args.lean, args.hold_ms
        )
        for colors in (255, 160, 96, 64):
            data = encode(frames, times, colors)
            if len(data) <= 500_000:
                break
        else:
            raise ValueError("仍超出 500,000 字节，请简化杂色或动作")
        if args.frames_dir:
            args.frames_dir.mkdir(parents=True, exist_ok=False)
            for n, frame in enumerate(frames, 1):
                frame.save(args.frames_dir / f"frame-{n:03}.png")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=args.output.parent, delete=False) as tmp:
            tmp.write(data)
            stage = Path(tmp.name)
        try:
            os.replace(stage, args.output)
        finally:
            stage.unlink(missing_ok=True)
        print(f"{args.output} · {len(frames)} 帧 · {len(data):,} 字节")
    except (ValueError, OSError) as error:
        sys.exit(f"动画导出失败：{error}")


if __name__ == "__main__":
    main()
