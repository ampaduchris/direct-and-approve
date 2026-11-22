#!/usr/bin/env python3
"""Extract method/ from a control folder by the declared mapping (spec section 7).

  python3 scripts/extract.py <control-folder> [--out method] [--check] [--date YYYY-MM-DD]
  python3 scripts/extract.py --verify-manifest [--out method]

The mapping is extract.toml at the repository root. Same control folder, mapping, static/ folder
and source date give the same bytes. A private marker in the output stops the run (exit 2) before
anything is written. Standard library only; no network; the clock is never read.

Exit codes: 0 success, 1 --check or --verify-manifest found a difference, 2 private marker,
3 usage, configuration or input error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KINDS = ("copy", "tree", "static")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


class Stop(Exception):
    """A run that ends with an exit code and one message on stderr."""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class Parser(argparse.ArgumentParser):
    def error(self, message):  # usage errors are exit 3 (REQ-041)
        self.print_usage(sys.stderr)
        print(f"extract: {message}", file=sys.stderr)
        raise SystemExit(3)


# ---- globs ----------------------------------------------------------------------------------------

def glob_to_regex(pattern: str) -> re.Pattern:
    """`**/` matches any folders (or none), `**` at the end matches anything, `*` stays in one segment."""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile(out + r"\Z", re.S)


def glob_match(pattern: str, path: str) -> bool:
    return glob_to_regex(pattern).match(path) is not None


def any_match(patterns: list[str], path: str) -> bool:
    return any(glob_match(p, path) for p in patterns)


# ---- mapping --------------------------------------------------------------------------------------

def check_replacements(reps: list[dict]) -> list[str]:
    """Problems that make a replacement list unsafe (REQ-039): an empty or repeated `from`, or a `to`
    that is or contains a `from`."""
    problems = []
    froms = [r.get("from", "") for r in reps]
    for i, f in enumerate(froms):
        if not f:
            problems.append(f"replacement {i + 1}: empty from")
    for f in {f for f in froms if froms.count(f) > 1}:
        problems.append(f"replacement from string used twice (index {froms.index(f) + 1})")
    for i, r in enumerate(reps):
        for j, f in enumerate(froms):
            if f and f in r.get("to", ""):
                problems.append(f"replacement {i + 1}: its to string contains the from string of replacement {j + 1}")
    return problems


def load_mapping(path: Path) -> dict:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Stop(3, f"mapping not found: {path.name}")
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise Stop(3, f"mapping {path.name} cannot be read: {type(e).__name__}")
    meta = data.get("meta", {})
    output = meta.get("output")
    if not output or meta.get("schema") != 1:
        raise Stop(3, "mapping: [meta] needs schema = 1 and output")
    reps = data.get("replacement", [])
    for p in check_replacements(reps):
        raise Stop(3, f"mapping: {p}")
    entries = data.get("entry", [])
    if not entries:
        raise Stop(3, "mapping: no [[entry]]")
    seen: dict[str, int] = {}
    for n, e in enumerate(entries, 1):
        kind = e.get("kind")
        if kind not in KINDS or not e.get("source") or not e.get("target"):
            raise Stop(3, f"mapping: entry {n} needs kind (copy, tree or static), source and target")
        if not e["target"].startswith(output + "/"):
            raise Stop(3, f"mapping: entry target {e['target']} is not under {output}/")
        if e["target"] in seen:
            raise Stop(3, f"mapping: two entries have the target {e['target']} (REQ-030)")
        seen[e["target"]] = n
        if kind == "tree":
            if not e.get("include"):
                raise Stop(3, f"mapping: tree entry {e['target']} needs include")
            if "/skills/" in "/" + e["target"] + "/":
                for g in e.get("replace_in", []):
                    if glob_match(g, "x.py") or glob_match(g, "scripts/x.py") or glob_match(g, "a/b/x.py"):
                        raise Stop(3, f"mapping: tree entry {e['target']}: replace_in {g} can touch a .py file "
                                      "under a skills tree (REQ-071)")
    for e in entries:
        for pat in data.get("forbidden", {}).get("patterns", []):
            try:
                re.compile(pat)
            except re.error:
                raise Stop(3, "mapping: a forbidden pattern is not a valid regular expression")
    return data


# ---- reading --------------------------------------------------------------------------------------

def label(e: dict) -> str:
    return f"{e['kind']} {e['source']}"


def read_text(path: Path, entry: dict, shown: str) -> tuple[bytes, str]:
    if path.is_symlink() or not path.is_file():
        raise Stop(3, f"entry {label(entry)}: {shown} is missing or not a regular file")
    try:
        raw = path.read_bytes()
    except OSError:
        raise Stop(3, f"entry {label(entry)}: {shown} is unreadable")
    try:
        return raw, raw.decode("utf-8")
    except UnicodeDecodeError:
        raise Stop(3, f"entry {label(entry)}: {shown} is not valid UTF-8 text")


def apply_replacements(text: str, reps: list[dict]) -> tuple[str, int]:
    """Literal, case-sensitive, longest `from` first, in one pass over the text."""
    if not reps:
        return text, 0
    table = {r["from"]: r["to"] for r in reps}
    pattern = re.compile("|".join(re.escape(f) for f in sorted(table, key=lambda s: (-len(s), s))))
    count = 0

    def sub(m: re.Match) -> str:
        nonlocal count
        count += 1
        return table[m.group(0)]

    return pattern.sub(sub, text), count


def date_line(text: str, date: str) -> str:
    if not text.startswith("# "):
        raise Stop(3, "a source_date_line entry must start with a title line")
    head, _, rest = text.partition("\n")
    return f"{head}\n\nCopied from the private authority on {date}.\n{rest}"


def source_date(control: Path, flag: str | None) -> str:
    """The --date value, else the date of the control folder's newest commit. Never the clock (REQ-040)."""
    if flag:
        if not DATE_RE.fullmatch(flag):
            raise Stop(3, "--date must be YYYY-MM-DD")
        return flag
    try:
        top = subprocess.run(["git", "-C", str(control), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=30)
        log = subprocess.run(["git", "-C", str(control), "log", "-1", "--format=%cs"],
                             capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        raise Stop(3, "cannot run git; pass --date YYYY-MM-DD")
    ok = (top.returncode == 0 and log.returncode == 0 and DATE_RE.fullmatch(log.stdout.strip() or "")
          and Path(top.stdout.strip()).resolve() == control.resolve())
    if not ok:
        raise Stop(3, "the control folder has no commit to take a date from; pass --date YYYY-MM-DD")
    return log.stdout.strip()


# ---- building -------------------------------------------------------------------------------------

class Built:
    def __init__(self):
        self.files: dict[str, tuple[bytes, str, str]] = {}  # path under out -> (bytes, kind, entry label)
        self.lines: list[str] = []

    def add(self, rel: str, data: bytes, kind: str, entry: dict) -> None:
        if rel in self.files:
            raise Stop(3, f"two entries produce the same file {rel} (REQ-030); the second is {label(entry)}")
        self.files[rel] = (data, kind, label(entry))


def build(control: Path, repo: Path, mapping: dict, date: str, out_prefix: str) -> Built:
    meta, reps = mapping["meta"], mapping.get("replacement", [])
    built = Built()
    skills_py = lambda target, rel: "/skills/" in "/" + target + "/" and rel.endswith(".py")  # noqa: E731
    for e in mapping["entry"]:
        kind, rel_root = e["kind"], e["target"][len(meta["output"]) + 1:]
        size = made = 0
        if kind in ("copy", "static"):
            base = control if kind == "copy" else repo
            raw, text = read_text(base / e["source"], e, e["source"])
            if kind == "copy" and e.get("replace", False):
                text, made = apply_replacements(text, reps)
                raw = text.encode("utf-8")
            if e.get("source_date_line"):
                raw = date_line(text, date).encode("utf-8")
            built.add(rel_root, raw, kind, e)
            size = len(raw)
        else:
            src = control / e["source"]
            if src.is_symlink() or not src.is_dir():
                raise Stop(3, f"entry {label(e)}: the source folder is missing")
            found = []
            for dirpath, dirnames, filenames in os.walk(src, followlinks=False):
                dirnames.sort()
                for name in sorted(filenames):
                    p = Path(dirpath) / name
                    rel = p.relative_to(src).as_posix()
                    if p.is_symlink() or not any_match(e["include"], rel) or any_match(e.get("exclude", []), rel):
                        continue
                    found.append((rel, p))
            for rel, p in sorted(found):
                raw, text = read_text(p, e, rel)
                if any_match(e.get("replace_in", []), rel):
                    new, n = apply_replacements(text, reps)
                    if new != text and skills_py(e["target"], rel):
                        raise Stop(3, f"entry {label(e)}: a replacement changed {rel}, a .py file under a skills tree (REQ-071)")
                    raw, made = new.encode("utf-8"), made + n
                built.add(f"{rel_root}/{rel}", raw, kind, e)
                size += len(raw)
        built.lines.append(f"{kind} {e['source']} -> {e['target']}  {size} bytes, {made} replacements")
    return built


def scan(built: Built, mapping: dict, out_prefix: str) -> None:
    """Private markers (REQ-033): every `from` string and every forbidden pattern, in names and contents.
    Reports the entry and the line number and never the matched text."""
    froms = [r["from"] for r in mapping.get("replacement", [])]
    patterns = [re.compile(p) for p in mapping.get("forbidden", {}).get("patterns", [])]

    def hit(s: str) -> bool:
        return any(f in s for f in froms) or any(p.search(s) for p in patterns)

    for rel in sorted(built.files):
        if hit(rel):
            raise Stop(2, f"refused: entry {built.files[rel][2]}: private marker in a file name (name withheld). Nothing was written.")
    for rel in sorted(built.files):
        data, _, entry = built.files[rel]
        for n, line in enumerate(data.decode("utf-8").split("\n"), 1):
            if hit(line):
                raise Stop(2, f"refused: {out_prefix}/{rel}:{n}: private marker (entry {entry}). Nothing was written.")


def manifest_bytes(built: Built, date: str) -> bytes:
    files = [{"path": rel, "kind": built.files[rel][1], "sha256": hashlib.sha256(built.files[rel][0]).hexdigest()}
             for rel in sorted(built.files)]
    return (json.dumps({"schema": 1, "source_date": date, "files": files}, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


# ---- comparing and writing ------------------------------------------------------------------------

def folder_files(folder: Path) -> dict[str, bytes]:
    if not folder.is_dir():
        return {}
    return {p.relative_to(folder).as_posix(): p.read_bytes()
            for p in sorted(folder.rglob("*")) if p.is_file() or p.is_symlink()}


def differences(want: dict[str, bytes], have: dict[str, bytes]) -> list[str]:
    out = [f"changed: {p}" for p in sorted(want) if p in have and want[p] != have[p]]
    out += [f"missing: {p}" for p in sorted(want) if p not in have]
    out += [f"extra: {p}" for p in sorted(have) if p not in want]
    return out


def write_out(files: dict[str, bytes], out_dir: Path) -> None:
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".extract-", dir=out_dir.parent))
    old = None
    try:
        for rel, data in files.items():
            p = tmp / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        if out_dir.exists():
            old = out_dir.with_name(f".extract-old-{os.getpid()}")
            out_dir.rename(old)
        tmp.rename(out_dir)
    except BaseException:
        if old is not None and old.exists() and not out_dir.exists():
            old.rename(out_dir)
        raise
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if old is not None:
            shutil.rmtree(old, ignore_errors=True)


def verify_manifest(out_dir: Path) -> list[str]:
    mf = out_dir / "MANIFEST.json"
    try:
        listed = {f["path"]: f["sha256"] for f in json.loads(mf.read_text(encoding="utf-8"))["files"]}
    except (OSError, ValueError, KeyError, TypeError):
        raise Stop(3, f"no readable manifest at {mf.name} in {out_dir.name}")
    have = folder_files(out_dir)
    have.pop("MANIFEST.json", None)
    out = [f"changed: {p}" for p in sorted(listed) if p in have and hashlib.sha256(have[p]).hexdigest() != listed[p]]
    out += [f"missing: {p}" for p in sorted(listed) if p not in have]
    out += [f"extra: {p}" for p in sorted(have) if p not in listed]
    return out


# ---- command line ---------------------------------------------------------------------------------

def run(argv: list[str]) -> int:
    ap = Parser(prog="extract.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("control", nargs="?", help="the control folder")
    ap.add_argument("--repo", default=str(ROOT), help="folder holding extract.toml and static/ (default: this repository)")
    ap.add_argument("--out", help="output folder (default: the mapping's output)")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if a fresh extraction differs")
    ap.add_argument("--date", help="source date, YYYY-MM-DD (default: the control folder's newest commit)")
    ap.add_argument("--verify-manifest", action="store_true", help="check the output folder against its manifest; no control folder needed")
    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()

    if args.verify_manifest:
        out_dir = (repo / args.out) if args.out else (repo / "method")
        diff = verify_manifest(out_dir)
        for d in diff:
            print(d)
        print("manifest: OK" if not diff else f"manifest: {len(diff)} difference(s)")
        return 1 if diff else 0

    if not args.control:
        ap.error("a control folder is required")
    control = Path(args.control).resolve()
    if not control.is_dir():
        raise Stop(3, "the control folder does not exist")
    mapping = load_mapping(repo / "extract.toml")
    out_prefix = mapping["meta"]["output"]
    out_dir = repo / (args.out or out_prefix)
    date = source_date(control, args.date)
    built = build(control, repo, mapping, date, out_prefix)
    scan(built, mapping, out_prefix)
    files = {rel: v[0] for rel, v in built.files.items()}
    files["MANIFEST.json"] = manifest_bytes(built, date)
    for line in built.lines:
        print(line)
    if args.check:
        diff = differences(files, folder_files(out_dir))
        for d in diff:
            print(d)
        print("extract: output matches" if not diff else f"extract: {len(diff)} difference(s)")
        return 1 if diff else 0
    write_out(files, out_dir)
    print(f"extract: wrote {len(files)} files to {args.out or out_prefix} (source date {date})")
    return 0


def main(argv: list[str]) -> int:
    try:
        return run(argv)
    except Stop as s:
        print(f"extract: {s.message}", file=sys.stderr)
        return s.code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
