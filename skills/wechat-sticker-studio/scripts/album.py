#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10.4,<14"]
# ///
"""Validate a WeChat sticker submission and optionally write a ZIP or browser upload plan."""

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

from PIL import Image


def read_copy(path):
    title = intro = ""
    rows = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if line.startswith("专辑名称"):
            title = line[len("专辑名称") :].lstrip(" \t　:：")
        elif line.startswith("专辑介绍"):
            intro = line[len("专辑介绍") :].lstrip(" \t　:：")
        elif line[:1].isdigit():
            # Two spaces, a tab, or a full-width space separates fields.
            fields = re.split(r"(?:\t+|　+| {2,})", line)
            if len(fields) != 3 or not re.fullmatch(r"[0-9]{2}", fields[0]):
                raise ValueError(f"{path.name} 文案行格式错误：{line}")
            number, caption, meaning = (field.strip() for field in fields)
            if number in rows or not caption or not 1 <= len(meaning) <= 4:
                raise ValueError(f"{number} 编号重复、台词为空或含义词长度有误")
            rows[number] = (caption, meaning)
    if not 1 <= len(title) <= 8 or not 1 <= len(intro) <= 80:
        raise ValueError("专辑名称须为 1～8 字，本工具要求投稿文案包含 1～80 字介绍")
    return title, intro, rows


def validate_gif(path):
    if path.stat().st_size > 500_000:
        raise ValueError(f"{path.name} 超过本工具的 500,000 字节投稿预算")
    with Image.open(path) as image:
        if (
            image.format != "GIF"
            or image.size != (240, 240)
            or image.info.get("loop") != 0
        ):
            raise ValueError(f"{path.name} 应为 240×240、无限循环的 GIF")
        first = None
        changed = False
        duration = 0
        for index in range(image.n_frames):
            image.seek(index)
            delay = image.info.get("duration", 0)
            rgba = image.convert("RGBA")
            if delay <= 0 or not rgba.getchannel("A").getbbox():
                raise ValueError(f"{path.name} 第 {index + 1} 帧为空或缺少正时长")
            # Composite onto a fixed chat background so hidden RGB values do not count as motion.
            visible = Image.new("RGBA", rgba.size, "#eeeeee")
            visible.alpha_composite(rgba)
            pixels = visible.tobytes()
            if first is None:
                first = pixels
            changed |= pixels != first
            duration += delay
        if not changed:
            raise ValueError(f"{path.name} 需要至少两个可区分的画面")
        return image.n_frames, duration


def check_static(path, formats, size, limit, transparent):
    with Image.open(path) as image:
        image.load()
        if (
            image.format not in formats
            or image.size != size
            or path.stat().st_size > limit
        ):
            raise ValueError(
                f"{path.name} 格式、尺寸或体积有误，应为 {formats} {size}，≤{limit} 字节"
            )
        alpha = image.convert("RGBA").getchannel("A").getextrema()
        if transparent and (alpha[0] != 0 or alpha[1] == 0):
            raise ValueError(f"{path.name} 应包含可见主体和透明背景")
        if not transparent and alpha[0] < 255:
            raise ValueError(f"{path.name} 请导出有色实底横幅")


def descriptor(root, path):
    if not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError(f"投稿素材必须是目录内可读的文件：{path.name}")
    return {
        "file": str(path),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def inspect_album(root):
    copy_path = root / "专辑文案.txt"
    descriptor(root, copy_path)
    title, intro, rows = read_copy(copy_path)
    files = sorted((root / "表情").glob("*.gif"))
    ids = [f"{i:02d}" for i in range(1, len(files) + 1)]
    if (
        not 8 <= len(ids) <= 24
        or [file.stem for file in files] != ids
        or set(ids) != rows.keys()
    ):
        raise ValueError("需要 8～24 张从 01 开始连续编号的 GIF，每张恰好对应一行文案")
    banners = [
        p
        for p in root.iterdir()
        if p.stem == "详情页横幅" and p.suffix.lower() in {".png", ".jpg", ".jpeg"}
    ]
    if len(banners) != 1:
        raise ValueError("请保留一张详情页横幅，PNG 或 JPEG")
    assets = {}
    for key, path, formats, size, limit, transparent in [
        ("cover", root / "封面.png", {"PNG"}, (240, 240), 500_000, True),
        ("icon", root / "聊天面板图标.png", {"PNG"}, (50, 50), 100_000, True),
        ("banner", banners[0], {"PNG", "JPEG"}, (750, 400), 500_000, False),
    ]:
        assets[key] = descriptor(root, path)
        check_static(path, formats, size, limit, transparent)
    stickers = []
    for path in files:
        entry = descriptor(root, path)
        frames, duration = validate_gif(path)
        caption, meaning = rows[path.stem]
        stickers.append(
            dict(
                entry,
                id=path.stem,
                caption=caption,
                meaning=meaning,
                frames=frames,
                duration_ms=duration,
            )
        )
    return {
        "title": title,
        "intro": intro,
        "copy": str(copy_path),
        **assets,
        "stickers": stickers,
    }


def write_bundle(path, root, plan):
    entries = [
        plan["copy"],
        *(plan[k]["file"] for k in ("cover", "icon", "banner")),
        *(item["file"] for item in plan["stickers"]),
    ]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in entries:
            archive.write(item, Path(item).relative_to(root))


def atomic_write(destination, writer):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as tmp:
        staging = Path(tmp.name)
    try:
        writer(staging)
        os.replace(staging, destination)
    finally:
        staging.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "album", type=Path, help="含表情、封面、图标、横幅及专辑文案的目录"
    )
    parser.add_argument("--manifest", type=Path, help="写出本地浏览器上传用 JSON 文件")
    parser.add_argument("--zip", type=Path, help="仅打包已通过检查的投稿文件")
    args = parser.parse_args()
    root = args.album.resolve()
    targets = [p.resolve() for p in (args.manifest, args.zip) if p is not None]
    if len(targets) != len(set(targets)) or any(
        p.is_relative_to(root) for p in targets
    ):
        parser.error("清单和 ZIP 请分别写到投稿目录以外的不同文件")
    try:
        plan = inspect_album(root)
        if args.manifest:
            payload = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
            atomic_write(
                args.manifest, lambda path: path.write_text(payload, encoding="utf-8")
            )
        if args.zip:
            atomic_write(args.zip, lambda path: write_bundle(path, root, plan))
        print(
            f"{plan['title']} · {len(plan['stickers'])} 张动态表情、封面、图标、横幅、文案通过检查"
        )
    except (ValueError, OSError, EOFError, Image.DecompressionBombError) as error:
        sys.exit(f"投稿素材检查失败：{error}")


if __name__ == "__main__":
    main()
