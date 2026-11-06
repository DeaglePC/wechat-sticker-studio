"""Offline regressions for the publishable archive and the upload manifest."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "wechat-sticker-studio" / "scripts"


class AlbumTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.work = Path(tmp.name)
        self.album = self.work / "album"
        shutil.copytree(ROOT / "examples" / "badge-shrimp" / "album", self.album)
        self.manifest = self.work / "plan.json"

    def inspect(self, *args):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "album.py"),
                str(self.album),
                "--manifest",
                str(self.manifest),
                *map(str, args),
            ],
            capture_output=True,
            check=False,
            text=True,
        )

    def test_only_submission_material_in_zip(self):
        (self.album / "笔记.txt").write_text("private")
        dest = self.work / "pack.zip"
        result = self.inspect("--zip", dest)
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            [s["id"] for s in plan["stickers"]], [f"{i:02d}" for i in range(1, 17)]
        )
        self.assertEqual(plan["stickers"][0]["meaning"], "确认")
        with zipfile.ZipFile(dest) as archive:
            self.assertEqual(len(archive.namelist()), 20)
            self.assertNotIn("笔记.txt", archive.namelist())
            self.assertIsNone(archive.testzip())

    def test_missing_intro_blocks_plan(self):
        path = self.album / "专辑文案.txt"
        lines = path.read_text(encoding="utf-8").splitlines()
        path.write_text(
            "\n".join(l for l in lines if not l.startswith("专辑介绍")),
            encoding="utf-8",
        )
        self.assertNotEqual(self.inspect().returncode, 0)
        self.assertFalse(self.manifest.exists())

    def test_single_frame_rejected(self):
        gif = self.album / "表情" / "01.gif"
        with Image.open(gif) as image:
            still = image.convert("RGBA")
        still.save(gif, loop=0, duration=100)
        self.assertNotEqual(self.inspect().returncode, 0)
        self.assertFalse(self.manifest.exists())


if __name__ == "__main__":
    unittest.main()
