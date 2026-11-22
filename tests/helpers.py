"""Shared helpers for the 9.2 tests. Fixtures are built here, never read from the real control folder."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FX1 = ROOT / "tests" / "fixtures" / "fx1"
DATE = "2026-11-22"


def run(script: str, *args: object, cwd: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *map(str, args)],
        capture_output=True, text=True, cwd=cwd, env=env, timeout=60,
    )


class Fx:
    """A private copy of FX-1: `control` is the control folder, `repo` holds extract.toml and static/."""

    def __init__(self, base: Path):
        shutil.copytree(FX1, base / "fx1", symlinks=True)
        self.base = base / "fx1"
        self.control = self.base / "control"
        self.repo = self.base / "repo"
        self.out = self.repo / "method"
        self.mapping = self.repo / "extract.toml"

    def extract(self, *extra: object, date: str | None = DATE) -> subprocess.CompletedProcess:
        args: list[object] = [self.control, "--repo", self.repo]
        if date:
            args += ["--date", date]
        return run("extract.py", *args, *extra)

    def check(self, *extra: object) -> subprocess.CompletedProcess:
        return self.extract("--check", *extra)

    def append(self, rel: str, text: str) -> None:
        p = self.control / rel
        p.write_text(p.read_text(encoding="utf-8") + text, encoding="utf-8")

    def set_mapping(self, text: str) -> None:
        self.mapping.write_text(text, encoding="utf-8")


def tree_hash(folder: Path) -> dict[str, str]:
    """Relative path to SHA-256 for every file; an absent folder gives an empty dict."""
    if not folder.exists():
        return {}
    return {
        p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(folder.rglob("*")) if p.is_file()
    }
