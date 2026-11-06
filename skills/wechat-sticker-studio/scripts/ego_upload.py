#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10.4,<14"]
# ///
"""Open the WeChat artist portal or attach vetted files to one inspected file input."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from album import inspect_album

OPEN_PAGE = """
const task = await taskSpace(args.name);
const page = task.page("p1");
const current = new URL(await page.url());
if (["about:", "chrome-extension:", "chrome:", "edge:"].includes(current.protocol)) {
  await page.goto("https://sticker.weixin.qq.com/");
}
const url = new URL(await page.url());
if (url.origin !== "https://sticker.weixin.qq.com") {
  throw new Error("已有同名会话在其他网站；请另取任务名或恢复正确的官方页面");
}
console.log(JSON.stringify({space:task.spaceId, page:page.label, url:url.href}));
console.log(await page.snapshot());
"""

ATTACH_FILES = """
const task = await taskSpace(args.space);
const page = task.page(args.page);
if (new URL(await page.url()).origin !== "https://sticker.weixin.qq.com") {
  throw new Error("当前页面不是微信表情开放平台");
}
const field = await page.evaluate(selector => {
  const matches = document.querySelectorAll(selector);
  if (matches.length !== 1) return null;
  const el = matches[0];
  if (el.tagName !== "INPUT" || el.type !== "file") return null;
  return {multiple:el.multiple, disabled:el.disabled, filled:el.files.length};
}, args.selector);
if (!field || field.disabled || field.filled) {
  throw new Error("请重新核对该栏是否为空，以及 CSS 是否唯一定位了可用文件输入框");
}
if (args.files.length > 1 && !field.multiple) {
  throw new Error("该控件只接收一个文件；按页面槽位传对应的 --id");
}
await page.setInputFiles("loc=css:" + args.selector, args.files);
console.log("本栏文件已交给网页。检查上传进度与缩略图，成功回显后再处理下一栏。");
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("open")
    start.add_argument("--name", default="微信表情专辑投稿")
    attach = commands.add_parser("attach")
    attach.add_argument("--manifest", type=Path, required=True)
    attach.add_argument("--space", type=int, required=True)
    attach.add_argument("--page", default="p1")
    attach.add_argument(
        "--selector", required=True, help="从当前官方页面核实的唯一文件输入框 CSS"
    )
    attach.add_argument(
        "--field", choices=["stickers", "cover", "icon", "banner"], required=True
    )
    attach.add_argument("--id", nargs="+", help="仅传主图的指定两位编号；默认选全部")
    args = parser.parse_args()
    if not shutil.which("ego-browser"):
        parser.error("本适配器需要 ego-browser；其他交互式浏览器可按投稿手册执行")
    if args.command == "open":
        payload = {"name": args.name}
        script = OPEN_PAGE
    else:
        try:
            plan = json.loads(args.manifest.read_text(encoding="utf-8"))
            root = Path(plan["copy"]).resolve().parent
            if inspect_album(root) != plan:
                parser.error("投稿文件或清单已发生变化，重新运行 album.py 后再上传")
            if args.field == "stickers":
                by_id = {s["id"]: s["file"] for s in plan["stickers"]}
                ids = args.id or list(by_id)
                if len(set(ids)) != len(ids) or not set(ids) <= set(by_id):
                    parser.error("--id 含重复或不存在的编号")
                files = [by_id[i] for i in ids]
            else:
                if args.id:
                    parser.error("--id 仅适用于主图")
                files = [plan[args.field]["file"]]
        except (ValueError, KeyError, TypeError, OSError, EOFError) as error:
            parser.error(str(error))
        payload = {
            "space": args.space,
            "page": args.page,
            "selector": args.selector,
            "files": files,
        }
        script = ATTACH_FILES
    command = "const args = " + json.dumps(payload, ensure_ascii=True) + ";\n" + script
    sys.exit(
        subprocess.run(
            ["ego-browser", "nodejs"], input=command, text=True, check=False
        ).returncode
    )


if __name__ == "__main__":
    main()
