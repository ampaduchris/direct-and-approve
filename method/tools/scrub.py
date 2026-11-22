#!/usr/bin/env python3
"""Personal-data and employer-term scrubber (control R5).

Terms are matched as normalised word n-grams (1 to 5 words, across line breaks), in a spaced
and a joined form ("acme widgets" and "acmewidgets"), and as a run inside a longer token
("acmewidgetsgmbh", a hashtag, a German compound). Terms are compared by SHA-256, so the
plaintext list stays in private/denylist.txt, which never leaves this private repo. There is no
CI copy of the list and no way to export hashes: public CI runs gitleaks only.

  scrub.py <path>             scan a file or tree: file contents, file and folder names, text inside
                              Office files (docx, pptx, xlsx, odt, odp, ods), zips and PDFs (including
                              metadata and embedded files), and strings in image metadata
  scrub.py --text-file <f>    scan a PR body, a commit message file or an issue text; "-" reads stdin
  scrub.py --history [repo]   scan every commit of a repo before its first push: messages, author
                              names and emails, branch and tag names, and every file version ever
                              committed, including ones since deleted (default repo: current folder)
  scrub.py --self-test        prove each mode catches a planted term and passes clean input

Prints CLEAN, or file:line hits (never the matched text, only the line number and a hash prefix),
or UNVERIFIED for anything that could not be read. Exit codes: 0 clean, 1 hits, 2 usage or no list,
3 nothing found but something could not be read (never reported as CLEAN).

Limits, stated so nobody trusts it too far: pixels in images are not read (render gallery and demo
images only from scrubbed synthetic specs). PDF text in subsetted CID fonts needs `pdftotext`
(poppler); without it such a PDF is reported UNVERIFIED. Fonts are skipped. The folders in
SKIP_DIRS are skipped, so a built wheel in dist/ is not scanned: scan the unpacked source.
"""
from __future__ import annotations

import contextlib
import hashlib
import html
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = ROOT / "private" / "denylist.txt"
# The private folder of this private repo holds the denylist and the source material that
# public repos are scrubbed against. It is skipped by location, never by name: a folder
# called "private" inside a public repo (repos/<name>/private) is still scanned.
PRIVATE = (ROOT / "private").resolve()
MAX_N = 5
MIN_RUN = 8          # shortest joined term that is also matched inside a longer token
MAX_RUN_TOKEN = 80   # longer tokens (base64, hashes) are not searched for embedded terms
MAX_MEMBER = 200 * 1024 * 1024
MAX_DEPTH = 3
SKIP_DIRS = {".git", "node_modules", ".venv", "dist", "build", "__pycache__"}
OFFICE = {".docx", ".dotx", ".docm", ".pptx", ".potx", ".pptm", ".xlsx", ".xltx", ".xlsm",
          ".odt", ".odp", ".ods", ".zip", ".epub", ".jar"}
IMAGES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".tif", ".tiff", ".bmp"}
FONTS = {".woff", ".woff2", ".ttf", ".otf"}
XMLISH = {".xml", ".rels", ".xmp", ".svg", ".xhtml", ".html", ".htm"}
# Kept for tools/hooks/guard.py: file types that cannot be read as plain text.
BINARY = OFFICE | IMAGES | FONTS | {".pdf"}


# ---------------------------------------------------------------- hashing

def norm_tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower().replace("ß", "ss")
    return re.findall(r"[a-z0-9@]+", text)


def h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


class Hashes(set):
    """A set of digests that also knows which joined-term lengths to search for inside tokens."""

    def __init__(self, *a):
        super().__init__(*a)
        self.lengths: set[int] = set()


def hashes_from_terms(terms) -> Hashes:
    out = Hashes()
    for term in terms:
        toks = norm_tokens(term)
        if not toks:
            continue
        out.add(h(" ".join(toks)))
        out.add(h("".join(toks)))
        if len("".join(toks)) >= MIN_RUN:
            out.lengths.add(len("".join(toks)))
    return out


def load_hashes() -> Hashes:
    if not LIST.exists():
        return Hashes()
    return hashes_from_terms(line.split("#", 1)[0].strip() for line in LIST.read_text().splitlines())


# ---------------------------------------------------------------- matching

def scan_text(text: str, hashes: set[str]) -> list[tuple[int, str]]:
    """Hits as (line of the first word, hash prefix). Windows of words run across line breaks."""
    toks: list[tuple[str, int]] = []
    for ln, line in enumerate(text.splitlines(), 1):
        toks += [(t, ln) for t in norm_tokens(line)]
    lengths = getattr(hashes, "lengths", set())
    hits: list[tuple[int, str]] = []
    seen = set()

    def add(ln: int, d: str) -> None:
        if (ln, d) not in seen:
            seen.add((ln, d))
            hits.append((ln, d[:10]))

    for i, (tok, ln) in enumerate(toks):
        for n in range(1, MAX_N + 1):
            if i + n > len(toks):
                break
            words = [t for t, _ in toks[i:i + n]]
            for d in (h(" ".join(words)), h("".join(words))):
                if d in hashes:
                    add(ln, d)
        if lengths and len(tok) <= MAX_RUN_TOKEN:
            for size in lengths:
                for s in range(0, len(tok) - size + 1):
                    d = h(tok[s:s + size])
                    if d in hashes:
                        add(ln, d)
    return hits


def scan_compact(text: str, hashes: set[str]) -> list[tuple[int, str]]:
    """Terms run together with no separators (PDF text drawn one glyph at a time)."""
    lengths = getattr(hashes, "lengths", set())
    flat = "".join(norm_tokens(text))
    hits, seen = [], set()
    for size in lengths:
        for s in range(0, len(flat) - size + 1):
            d = h(flat[s:s + size])
            if d in hashes and d not in seen:
                seen.add(d)
                hits.append((1, d[:10]))
    return hits


# ---------------------------------------------------------------- extraction
# Each extractor returns (items, warnings). An item is (label, text, compact).

def strings(data: bytes) -> str:
    out = [m.decode("latin-1") for m in re.findall(rb"[\x20-\x7e]{6,}", data)]
    out += [m.decode("utf-16-le", "ignore") for m in re.findall(rb"(?:[\x20-\x7e]\x00){6,}", data)]
    return "\n".join(out)


def decode_text(data: bytes) -> str | None:
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16", "ignore")
    if b"\x00" in data[:8192]:
        return None
    return data.decode("utf-8", "ignore")


def xml_items(label: str, text: str):
    spaced = re.sub(r"<[^>]*>", " ", re.sub(r"</[A-Za-z0-9:]*(?:p|h|si|row)>", "\n", text))
    merged = re.sub(r"<[^>]*>", "", re.sub(r"</[A-Za-z0-9:]*(?:p|h|si|row)>", "\n", text))
    return [(label, text, False), (label, html.unescape(spaced), False), (label, html.unescape(merged), False)]


def extract(name: str, data: bytes, depth: int = 0):
    items, warns = [], []
    suffix = os.path.splitext(name.lower())[1]
    if suffix in FONTS:
        return items, warns
    if data[:4] == b"PK\x03\x04" or suffix in OFFICE:
        return zip_items(name, data, depth)
    if data[:5] == b"%PDF-" or suffix == ".pdf":
        return pdf_items(name, data)
    if suffix in IMAGES or data[:8] == b"\x89PNG\r\n\x1a\n" or data[:3] == b"\xff\xd8\xff" or data[:4] == b"GIF8":
        return [(f"{name} [image metadata]", strings(data), False)], warns
    text = decode_text(data)
    if text is None:
        return [(f"{name} [binary strings]", strings(data), False)], warns
    if suffix in XMLISH or text.lstrip()[:5] == "<?xml":
        return xml_items(name, text), warns
    return [(name, text, False)], warns


def zip_items(name: str, data: bytes, depth: int):
    items, warns = [], []
    if depth > MAX_DEPTH:
        return items, [(name, "archives nested too deeply")]
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return [(f"{name} [binary strings]", strings(data), False)], [(name, "not a readable zip")]
    if zf.comment:
        items.append((f"{name} [zip comment]", zf.comment.decode("utf-8", "ignore"), False))
    total = 0
    for info in zf.infolist():
        member = f"{name}!{info.filename}"
        items.append((f"{member} [member name]", info.filename + "\n" + info.comment.decode("utf-8", "ignore"), False))
        if info.is_dir():
            continue
        total += info.file_size
        if info.file_size > MAX_MEMBER or total > 2 * MAX_MEMBER:
            warns.append((member, "too large to read"))
            continue
        try:
            raw = zf.read(info)
        except Exception as e:  # encrypted, corrupt
            warns.append((member, f"cannot read member ({type(e).__name__})"))
            continue
        i, w = extract(member, raw, depth + 1)
        items += i
        warns += w
    return items, warns


STREAM = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.S)
PDF_SHOW = re.compile(
    rb"\[((?:\\.|[^\]\\])*)\]\s*TJ"
    rb"|(\((?:\\.|[^\\()]|\((?:\\.|[^\\()])*\))*\)|<[0-9A-Fa-f\s]+>)\s*(?:Tj|'|\")", re.S)
PDF_PIECE = re.compile(rb"\(((?:\\.|[^\\()]|\((?:\\.|[^\\()])*\))*)\)|<([0-9A-Fa-f\s]+)>|(-?\d+\.?\d*)", re.S)
ESC = {ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12}


def pdf_unescape(b: bytes) -> bytes:
    out, i = bytearray(), 0
    while i < len(b):
        c = b[i]
        if c == 0x5C and i + 1 < len(b):
            n = b[i + 1]
            if n in ESC:
                out.append(ESC[n])
                i += 2
            elif 48 <= n <= 55:
                j, v = i + 1, 0
                while j < len(b) and j < i + 4 and 48 <= b[j] <= 55:
                    v = v * 8 + b[j] - 48
                    j += 1
                out.append(v & 255)
                i = j
            elif n in (10, 13):
                i += 2
            else:
                out.append(n)
                i += 2
        else:
            out.append(c)
            i += 1
    return bytes(out)


def pdf_text(b: bytes) -> str:
    return b.decode("utf-16-be", "ignore") if b[:2] == b"\xfe\xff" else b.decode("latin-1")


def pdf_pieces(stream: bytes) -> list[str]:
    pieces = []
    for m in PDF_SHOW.finditer(stream):
        if m.group(1) is not None:  # a TJ array: join the strings; a wide negative kern is a space
            s = ""
            for p in PDF_PIECE.finditer(m.group(1)):
                if p.group(1) is not None:
                    s += pdf_text(pdf_unescape(p.group(1)))
                elif p.group(2) is not None:
                    try:
                        s += pdf_text(bytes.fromhex(re.sub(rb"\s", b"", p.group(2)).decode()))
                    except ValueError:
                        pass
                elif float(p.group(3)) <= -200:
                    s += " "
            pieces.append(s)
        else:
            lit = m.group(2)
            if lit[:1] == b"(":
                pieces.append(pdf_text(pdf_unescape(lit[1:-1])))
            else:
                try:
                    pieces.append(pdf_text(bytes.fromhex(re.sub(rb"\s", b"", lit[1:-1]).decode())))
                except ValueError:
                    pass
    return pieces


def pdf_items(name: str, data: bytes):
    items, warns = [], []
    outside = STREAM.sub(b"", data)
    items.append((f"{name} [pdf header and metadata]", strings(outside), False))
    if b"/Encrypt" in outside:
        warns.append((name, "encrypted PDF"))
    decoded = []
    for m in STREAM.finditer(data):
        raw = m.group(1)
        try:
            dec = zlib.decompress(raw)
        except zlib.error:
            try:
                dec = zlib.decompressobj().decompress(raw)
            except zlib.error:
                dec = raw
        decoded.append(dec)
    cid = b"Identity-H" in data or any(b"Identity-H" in d for d in decoded)
    for n, dec in enumerate(decoded):
        label = f"{name} [pdf stream {n}]"
        if b"<x:xmpmeta" in dec or dec.lstrip()[:7] == b"<?xpack":
            items += xml_items(label, dec.decode("utf-8", "ignore"))
            continue
        pieces = pdf_pieces(dec)
        if pieces:
            items.append((label, "\n".join(pieces), False))
            items.append((label, "".join(pieces), True))
        items.append((label, strings(dec), False))
    exe = shutil.which("pdftotext")
    got_text = False
    if exe:
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "in.pdf"
            f.write_bytes(data)
            r = subprocess.run([exe, "-layout", str(f), "-"], capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                items.append((f"{name} [pdftotext]", r.stdout, False))
                items.append((f"{name} [pdftotext]", re.sub(r"\s+", "", r.stdout), True))
                got_text = True
    if cid and not got_text:
        warns.append((name, "text in CID fonts cannot be decoded without pdftotext (brew install poppler)"))
    return items, warns


# ---------------------------------------------------------------- scanning

def scan_items(items, hashes):
    out = []
    for label, text, compact in items:
        for ln, hid in (scan_compact if compact else scan_text)(text, hashes):
            out.append((label, ln, hid))
    return out


def scan_bytes(name: str, data: bytes, hashes: set[str]):
    """Hits and warnings for one file's bytes, its name included."""
    items, warns = extract(name, data)
    items.append((f"{name} [file name]", name.replace("/", "\n"), False))
    return scan_items(items, hashes), warns


def report(prefix: str, hits, warns) -> tuple[int, int]:
    seen = set()
    for label, ln, hid in hits:
        line = f"{prefix}{label}:{ln}: denylisted term #{hid}"
        if line not in seen:
            seen.add(line)
            print(line)
    for label, why in warns:
        print(f"{prefix}{label}: UNVERIFIED, {why}")
    return len(seen), len(warns)


def scan_path(root: Path, hashes: set[str]) -> tuple[int, int]:
    total = bad = 0
    files = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file() and not p.is_symlink()]
    for p in files:
        rel = p.relative_to(root) if root.is_dir() else Path(p.name)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if PRIVATE in p.resolve().parents:
            continue
        try:
            data = p.read_bytes()
        except Exception:
            print(f"{p}: UNVERIFIED, cannot read")
            bad += 1
            continue
        hits, warns = scan_bytes(rel.as_posix(), data, hashes)
        # Scanned under the relative name (so the scan root's own folders never match); shown by path.
        shown = lambda l: str(p) + l[len(rel.as_posix()):] if l.startswith(rel.as_posix()) else l  # noqa: E731
        t, b = report("", [(shown(l), ln, d) for l, ln, d in hits], [(shown(l), w) for l, w in warns])
        total += t
        bad += b
    return total, bad


def git_out(repo: Path, *args: str) -> bytes:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "ignore").strip())
    return r.stdout


def scan_history(repo: Path, hashes: set[str]) -> tuple[int, int]:
    top = Path(git_out(repo, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    skip_private = top == ROOT
    hits, warns = [], []
    log = git_out(top, "log", "--all", "--format=commit %h%n%an%n%ae%n%cn%n%ce%n%B%n").decode("utf-8", "ignore")
    hits += [("history commit messages and authors", ln, d) for ln, d in scan_text(log, hashes)]
    refs = git_out(top, "for-each-ref", "--format=%(refname)").decode("utf-8", "ignore")
    hits += [("history branch and tag names", ln, d) for ln, d in scan_text(refs, hashes)]
    objs = git_out(top, "rev-list", "--objects", "--all").decode("utf-8", "ignore").splitlines()
    names: dict[str, str] = {}
    for line in objs:
        sha, _, path = line.partition(" ")
        if path:
            names.setdefault(sha, path)
    # Names of folders count too: every path, file or folder, ever committed.
    hits += [("history path names", ln, d) for ln, d in scan_text("\n".join(sorted(set(names.values()))), hashes)]
    if names:
        proc = subprocess.run(["git", "-C", str(top), "cat-file", "--batch"], input="\n".join(names).encode() + b"\n",
                              capture_output=True, timeout=1800)
        buf, pos = proc.stdout, 0
        while pos < len(buf):
            eol = buf.index(b"\n", pos)
            sha, kind, size = buf[pos:eol].decode().split()
            size = int(size)
            body = buf[eol + 1:eol + 1 + size]
            pos = eol + 1 + size + 1
            if kind != "blob":
                continue
            path = names[sha]
            if skip_private and path.startswith("private/"):
                continue
            h2, w2 = scan_bytes(path, body, hashes)
            hits += [(f"history {sha[:8]}:{l}", ln, d) for l, ln, d in h2]
            warns += [(f"history {sha[:8]}:{l}", w) for l, w in w2]
    return report("", hits, warns)


def scan_text_file(arg: str, hashes: set[str]) -> tuple[int, int]:
    data = sys.stdin.buffer.read() if arg == "-" else Path(arg).read_bytes()
    text = data.decode("utf-8", "ignore")
    hits = [(arg, ln, d) for ln, d in scan_text(text, hashes)]
    return report("", hits, [])


# ---------------------------------------------------------------- self-test

def _zip(members: dict[str, str | bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for k, v in members.items():
            z.writestr(k, v)
    return buf.getvalue()


def _pdf(content: bytes, author: str = "nobody", cid: bool = False) -> bytes:
    body = zlib.compress(content)
    enc = b" /Encoding /Identity-H" if cid else b""
    return (b"%PDF-1.4\n1 0 obj\n<< /Author (" + author.encode() + b") >>\nendobj\n2 0 obj\n<< /Type /Font"
            + enc + b" >>\nendobj\n3 0 obj\n<< /Length " + str(len(body)).encode() + b" /Filter /FlateDecode >>\nstream\n"
            + body + b"\nendstream\nendobj\ntrailer\n<< /Info 1 0 R >>\n%%EOF\n")


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=tester", "-c", "user.email=tester@example.com",
                    "-c", "commit.gpgsign=false", *args], check=True, capture_output=True)


PLANTED_TERM = "acme widgets gmbh"


def run_cases() -> list[tuple[str, bool]]:
    planted = hashes_from_terms([PLANTED_TERM])
    results: list[tuple[str, bool]] = []

    def case(name: str, ok: bool) -> None:
        results.append((name, bool(ok)))

    def hit(name: str, data: bytes) -> bool:
        return bool(scan_bytes(name, data, planted)[0])

    # text: planted caught, clean passes
    case("text caught", scan_text("We worked at ACME Widgets GmbH last year.", planted))
    case("text clean", not scan_text("We worked at a manufacturing company.", planted))
    # joined token, hashtag, compound, line break
    case("joined caught", scan_text("Follow AcmeWidgetsGmbH today", planted))
    case("hashtag caught", scan_text("#acme_widgets_gmbh hiring", planted))
    case("run in compound caught", scan_text("Die Acme-Widgets-GmbH-Mitarbeiterin und Co", planted) and scan_text("xxAcmeWidgetsGmbHyy", planted))
    case("line break caught", scan_text("Acme\nWidgets\nGmbH", planted))
    case("joined clean", not scan_text("Acme sells widgets to a GmbH in Hamburg", planted))
    # Office: split runs, author field, nested workbook, member name
    runs = ('<w:document><w:p><w:r><w:t>Worked at Acme</w:t></w:r><w:r><w:t xml:space="preserve"> Widgets </w:t></w:r>'
            '<w:r><w:t>GmbH</w:t></w:r></w:p></w:document>')
    clean_doc = "<w:document><w:p><w:r><w:t>A manufacturing company</w:t></w:r></w:p></w:document>"
    core = '<cp:coreProperties><dc:creator>Acme Widgets GmbH</dc:creator></cp:coreProperties>'
    clean_core = '<cp:coreProperties><dc:creator>Synthetic Author</dc:creator></cp:coreProperties>'
    case("docx split runs caught", hit("a.docx", _zip({"word/document.xml": runs, "docProps/core.xml": clean_core})))
    case("docx author caught", hit("a.docx", _zip({"word/document.xml": clean_doc, "docProps/core.xml": core})))
    case("docx clean", not hit("a.docx", _zip({"word/document.xml": clean_doc, "docProps/core.xml": clean_core})))
    case("zip member name caught", hit("a.pptx", _zip({"ppt/acme-widgets-gmbh.xml": clean_doc})))
    book = _zip({"docProps/core.xml": core})
    case("nested workbook caught", hit("a.pptx", _zip({"ppt/slide1.xml": clean_doc, "ppt/embeddings/book.xlsx": book})))
    case("xlsx shared strings caught", hit("a.xlsx", _zip({"xl/sharedStrings.xml": "<sst><si><t>Acme</t></si><si><t>Widgets GmbH</t></si></sst>"})))
    # PDF: kerned array, glyph by glyph, metadata, clean, undecodable fonts
    kerned = b"BT /F1 12 Tf [(A)-20(cme Wid)5(gets )-300(GmbH)] TJ ET"
    glyphs = b"BT " + b" ".join(b"(" + c.encode() + b") Tj" for c in "AcmeWidgetsGmbH") + b" ET"
    clean_pdf = b"BT /F1 12 Tf [(A manufacturing )-300(company)] TJ ET"
    case("pdf kerned text caught", hit("a.pdf", _pdf(kerned)))
    case("pdf glyph text caught", hit("a.pdf", _pdf(glyphs)))
    case("pdf metadata caught", hit("a.pdf", _pdf(clean_pdf, author="Acme Widgets GmbH")))
    case("pdf clean", not hit("a.pdf", _pdf(clean_pdf)))
    if not shutil.which("pdftotext"):
        case("pdf CID fonts reported unverified", bool(scan_bytes("a.pdf", _pdf(clean_pdf, cid=True), planted)[1]))
    # images: metadata strings
    png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\x20tEXtAuthor\x00Acme Widgets GmbH\x00\x00\x00\x00"
    case("png metadata caught", hit("a.png", png))
    case("png clean", not hit("a.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\x20tEXtAuthor\x00Synthetic\x00\x00\x00\x00"))
    # file and folder names
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        (t / "ok").mkdir()
        (t / "ok" / "notes.txt").write_text("nothing here")
        case("names clean", scan_path(t, planted) == (0, 0))
        (t / "ok" / "acme-widgets-gmbh-notes.txt").write_text("nothing here")
        case("file name caught", scan_path(t, planted)[0] > 0)
        (t / "ok" / "acme-widgets-gmbh-notes.txt").unlink()
        (t / "AcmeWidgetsGmbH").mkdir()
        (t / "AcmeWidgetsGmbH" / "x.txt").write_text("nothing here")
        case("folder name caught", scan_path(t, planted)[0] > 0)
        # --text-file
        f = t / "body.md"
        f.write_text("Tier table\nWorked with Acme Widgets GmbH on this.\n")
        case("text-file caught", scan_text_file(str(f), planted)[0] > 0)
        f.write_text("Tier table\nAll checks pass.\n")
        case("text-file clean", scan_text_file(str(f), planted) == (0, 0))
    # --history
    def repo(td: str, name: str) -> Path:
        r = Path(td) / name
        r.mkdir()
        subprocess.run(["git", "init", "-q", str(r)], check=True, capture_output=True)
        return r

    with tempfile.TemporaryDirectory() as td:
        r = repo(td, "removed")
        (r / "a.txt").write_text("Worked at Acme Widgets GmbH\n")
        _git(r, "add", "."); _git(r, "commit", "-q", "-m", "first")
        (r / "a.txt").write_text("Worked at a manufacturer\n")
        _git(r, "add", "."); _git(r, "commit", "-q", "-m", "second")
        case("history deleted text caught", scan_history(r, planted)[0] > 0)
        r = repo(td, "message")
        (r / "a.txt").write_text("fine\n")
        _git(r, "add", "."); _git(r, "commit", "-q", "-m", "Notes from Acme Widgets GmbH")
        case("history message caught", scan_history(r, planted)[0] > 0)
        r = repo(td, "branch")
        (r / "a.txt").write_text("fine\n")
        _git(r, "add", "."); _git(r, "commit", "-q", "-m", "first"); _git(r, "branch", "acme-widgets-gmbh")
        case("history branch name caught", scan_history(r, planted)[0] > 0)
        r = repo(td, "docx")
        (r / "a.docx").write_bytes(_zip({"docProps/core.xml": core}))
        _git(r, "add", "."); _git(r, "commit", "-q", "-m", "first")
        (r / "a.docx").unlink()
        _git(r, "add", "-A"); _git(r, "commit", "-q", "-m", "second")
        case("history deleted docx caught", scan_history(r, planted)[0] > 0)
        r = repo(td, "clean")
        (r / "a.txt").write_text("fine\n")
        _git(r, "add", "."); _git(r, "commit", "-q", "-m", "first")
        case("history clean", scan_history(r, planted) == (0, 0))
    real = load_hashes()
    case("denylist loaded", len(real) > 0)
    return results


def self_test() -> int:
    with contextlib.redirect_stdout(io.StringIO()):  # the cases print their hit lines; the test reports only the verdict
        results = run_cases()
    failed = [n for n, ok in results if not ok]
    if failed:
        print("SELF-TEST FAIL: " + "; ".join(failed))
        return 1
    print("SELF-TEST PASS")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    if argv[0] == "--self-test":
        return self_test()
    hashes = load_hashes()
    if not hashes:
        print("NO DENYLIST LOADED: refusing to report CLEAN")
        return 2
    if argv[0] == "--text-file" and len(argv) == 2:
        if argv[1] != "-" and not Path(argv[1]).is_file():
            print(f"NO SUCH FILE: {argv[1]}")
            return 2
        n, bad = scan_text_file(argv[1], hashes)
    elif argv[0] == "--history" and len(argv) <= 2:
        repo = Path(argv[1] if len(argv) == 2 else ".")
        try:
            n, bad = scan_history(repo, hashes)
        except Exception as e:
            print(f"CANNOT READ HISTORY: {e}")
            return 2
    elif argv[0].startswith("--"):
        print(__doc__)
        return 2
    else:
        target = Path(argv[0])
        if not target.exists():
            print(f"NO SUCH PATH: {target}")
            return 2
        n, bad = scan_path(target, hashes)
    if n:
        print(f"{n} hit(s)")
        return 1
    if bad:
        print(f"UNVERIFIED: {bad} item(s) could not be read; not reporting CLEAN")
        return 3
    print("CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
