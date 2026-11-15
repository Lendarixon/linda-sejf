"""Ekstrakcja tekstu z dokumentów (biblioteka standardowa + opcjonalnie pypdf / python-docx)."""
from __future__ import annotations

import codecs
import logging
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

log = logging.getLogger(__name__)

TEXT_EXT = frozenset({".txt", ".md", ".csv", ".tsv"})
SUPPORTED_EXT = frozenset({
    ".txt", ".md", ".csv", ".tsv", ".pdf", ".docx",
    ".odt", ".rtf", ".html", ".htm", ".epub", ".pptx", ".xlsx",
})

MAX_ZIP_FILES = 10_000
MAX_ZIP_BYTES = 200 * 1024 * 1024  # 200 MB łącznego rozmiaru odczytywanych członków
MAX_XLSX_ROWS = 20_000

_ODF_TEXT = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
_ODF_TABLE = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


class _SafeZip:
    """Czytnik ZIP z ochroną przed zip-bombą (limit liczby plików i sumy rozpakowanych bajtów)."""

    def __init__(self, path: Path):
        self.zf = zipfile.ZipFile(path, "r")
        infos = self.zf.infolist()
        if len(infos) > MAX_ZIP_FILES:
            self.zf.close()
            raise ValueError(f"zbyt wiele plików w archiwum ({len(infos)})")
        self.used = 0
        self._names = {i.filename: i for i in infos}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.zf.close()

    def has(self, name: str) -> bool:
        return name in self._names

    def namelist(self) -> list[str]:
        return list(self._names)

    def read_bytes(self, name: str) -> bytes:
        info = self._names.get(name)
        if info is None:
            raise KeyError(name)
        if info.file_size < 0 or info.file_size > MAX_ZIP_BYTES or self.used + info.file_size > MAX_ZIP_BYTES:
            raise ValueError(f"przekroczono limit rozmiaru archiwum ({name})")
        parts: list[bytes] = []
        with self.zf.open(info, "r") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                self.used += len(chunk)
                if self.used > MAX_ZIP_BYTES:
                    raise ValueError(f"przekroczono limit rozmiaru rozpakowanych danych ({name})")
                parts.append(chunk)
        return b"".join(parts)


# ------------------------------------------------------------------ .txt / .md
def _read_txt(p: Path) -> str:
    data = p.read_bytes()
    if not data:
        return ""
    # UTF-16 (Notatnik „Unicode”): BOM albo wiele bajtów zerowych na przemian
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", errors="replace")
    head = data[:4000]
    if len(head) >= 4 and head.count(b"\x00") > len(head) // 4:
        odd = head[1::2].count(b"\x00")
        return data.decode("utf-16-le" if odd >= head[0::2].count(b"\x00") else "utf-16-be", errors="replace")
    for enc in ("utf-8-sig", "utf-8"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    if not data.startswith(b"\xef\xbb\xbf"):
        try:
            return data.decode("cp1250")
        except UnicodeDecodeError:
            pass
    raw = data[3:] if data.startswith(b"\xef\xbb\xbf") else data
    return raw.decode("utf-8", errors="replace")


# ------------------------------------------------------------------ .pdf / .docx
def _read_pdf(p: Path) -> str:
    if p.stat().st_size == 0:
        return ""
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    return "\n".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)


def _read_docx(p: Path) -> str:
    if p.stat().st_size == 0:
        return ""
    try:
        import docx
        from docx.table import Table
        from docx.text.paragraph import Paragraph
    except ImportError:
        return ""
    with _SafeZip(p) as sz:
        for name in sz.namelist():
            if name.lower().endswith((".xml", ".rels")):
                sz.read_bytes(name)
    doc = docx.Document(str(p))
    out: list[str] = []
    for item in doc.iter_inner_content():
        if isinstance(item, Paragraph):
            out.append(item.text)
        elif isinstance(item, Table):
            for row in item.rows:
                seen: set[int] = set()
                cells: list[str] = []
                for cell in row.cells:
                    tc = id(cell._tc)
                    if tc in seen:
                        continue
                    seen.add(tc)
                    cells.append(" ".join(cell.text.split()))
                if any(cells):
                    out.append(" | ".join(cells))
    return "\n".join(out)


# ------------------------------------------------------------------ .odt
def _odt_inline(el: ET.Element, buf: list[str], in_cell: bool = False) -> None:
    if el.text:
        buf.append(el.text)
    for child in el:
        loc = _local(child.tag)
        if loc == "s":
            cnt_raw = child.get(f"{{{_ODF_TEXT}}}c") or child.get("c") or "1"
            try:
                cnt = max(1, min(int(cnt_raw), 1000))
            except ValueError:
                cnt = 1
            buf.append(" " * cnt)
        elif loc == "tab":
            buf.append("\t")
        elif loc == "line-break":
            buf.append(" " if in_cell else "\n")
        elif loc in ("p", "h"):
            if buf and not buf[-1].endswith(("\n", " ")):
                buf.append(" " if in_cell else "\n")
            _odt_inline(child, buf, in_cell=in_cell)
        else:
            _odt_inline(child, buf, in_cell=in_cell)
        if child.tail:
            buf.append(child.tail)


def _odt_table(el: ET.Element, lines: list[str]) -> None:
    if _local(el.tag) == "table-row":
        cells: list[str] = []
        for cell in el:
            if _local(cell.tag) in ("table-cell", "covered-table-cell"):
                buf: list[str] = []
                _odt_inline(cell, buf, in_cell=True)
                val = " ".join("".join(buf).split())
                rep_raw = cell.get(f"{{{_ODF_TABLE}}}number-columns-repeated") or cell.get("number-columns-repeated") or "1"
                try:
                    rep = max(1, min(int(rep_raw), 50))
                except ValueError:
                    rep = 1
                if val or rep == 1:
                    cells.extend([val] * rep)
                else:
                    cells.append("")
        while cells and not cells[-1]:
            cells.pop()
        if any(cells):
            lines.append(" | ".join(cells))
    else:
        for child in el:
            _odt_table(child, lines)


def _odt_walk(el: ET.Element, lines: list[str]) -> None:
    loc = _local(el.tag)
    if loc in ("automatic-styles", "styles", "master-styles", "scripts", "font-face-decls", "meta"):
        return
    if loc in ("p", "h"):
        buf: list[str] = []
        _odt_inline(el, buf, in_cell=False)
        lines.append("".join(buf))
        return
    if loc == "table":
        for child in el:
            _odt_table(child, lines)
        return
    for child in el:
        _odt_walk(child, lines)


def _read_odt(p: Path) -> str:
    if p.stat().st_size == 0:
        return ""
    with _SafeZip(p) as sz:
        root = ET.fromstring(sz.read_bytes("content.xml"))
    lines: list[str] = []
    _odt_walk(root, lines)
    return "\n".join(lines)


# ------------------------------------------------------------------ .rtf
_RTF_SKIP_DEST = frozenset({
    "fonttbl", "colortbl", "stylesheet", "info", "pict", "object",
    "fldinst", "datafield", "listtable", "listoverridetable",
    "revtbl", "rsidtbl", "themedata", "colorschememapping",
    "latentstyles", "datastore", "xmlnstbl", "bkmkstart", "bkmkend",
    "pgdsctbl", "trackchanges", "aftnsep", "aftnsepc", "aftncn",
    "ftnsep", "ftnsepc", "ftncn", "xe", "tc", "rxe",
})

_RTF_SPECIAL = {
    "par": "\n",
    "line": "\n",
    "page": "\n",
    "tab": "\t",
    "emdash": "\u2014",
    "endash": "\u2013",
    "emspace": "\u2003",
    "enspace": "\u2002",
    "qmspace": "\u2005",
    "bullet": "\u2022",
    "lquote": "\u2018",
    "rquote": "\u2019",
    "ldblquote": "\u201c",
    "rdblquote": "\u201d",
    "~": "\u00a0",
    "_": "-",
    "-": "",
}


def _rtf_codepage(num: int) -> str:
    if num == 65001:
        return "utf-8"
    cand = f"cp{num}"
    try:
        codecs.lookup(cand)
        return cand
    except LookupError:
        return "cp1250"


def _read_rtf(p: Path) -> str:
    raw = p.read_bytes()
    if not raw:
        return ""
    if not raw.lstrip().startswith(b"{\\rtf"):
        raise ValueError("niepoprawny nagłówek RTF")

    n = len(raw)
    i = 0
    stack: list[tuple[int, bool, str]] = []
    uc = 1
    skip = False
    cpg = "cp1250"
    ignorable = False
    skip_chars = 0
    hex_buf = bytearray()
    out: list[str] = []

    def flush_hex() -> None:
        if hex_buf:
            if not skip:
                out.append(hex_buf.decode(cpg, errors="replace"))
            hex_buf.clear()

    while i < n:
        b = raw[i]
        if b == 123:  # '{'
            flush_hex()
            stack.append((uc, skip, cpg))
            ignorable = False
            skip_chars = 0
            i += 1
        elif b == 125:  # '}'
            flush_hex()
            if stack:
                uc, skip, cpg = stack.pop()
            ignorable = False
            skip_chars = 0
            i += 1
        elif b in (10, 13):  # surowe \n, \r ignorowane
            i += 1
        elif b == 92:  # '\'
            i += 1
            if i >= n:
                break
            c = raw[i]
            if c == 39:  # \'hh
                i += 1
                if i + 2 <= n:
                    try:
                        val = int(raw[i:i + 2], 16)
                        i += 2
                        if skip_chars > 0:
                            skip_chars -= 1
                        elif not skip:
                            hex_buf.append(val)
                    except ValueError:
                        pass
                ignorable = False
            elif c == 42:  # \*
                flush_hex()
                ignorable = True
                i += 1
            elif c in (10, 13):  # \<CR>/<LF> oznacza \par
                flush_hex()
                i += 2 if c == 13 and i + 1 < n and raw[i + 1] == 10 else 1
                if not skip:
                    out.append("\n")
                ignorable = False
                skip_chars = 0
            elif not (65 <= c <= 90 or 97 <= c <= 122):
                flush_hex()
                sym = chr(c)
                i += 1
                ignorable = False
                if skip_chars > 0:
                    skip_chars -= 1
                elif not skip:
                    if sym in ("\\", "{", "}"):
                        out.append(sym)
                    elif sym in _RTF_SPECIAL:
                        out.append(_RTF_SPECIAL[sym])
            else:
                flush_hex()
                wstart = i
                while i < n and (65 <= raw[i] <= 90 or 97 <= raw[i] <= 122):
                    i += 1
                word = raw[wstart:i].decode("ascii")
                param: int | None = None
                pstart = i
                if i < n and raw[i] == 45:  # '-'
                    i += 1
                dstart = i
                while i < n and 48 <= raw[i] <= 57:
                    i += 1
                if i > dstart:
                    param = int(raw[pstart:i])
                else:
                    i = pstart
                if i < n and raw[i] == 32:  # opcjonalna spacja kończąca słowo sterujące
                    i += 1

                if ignorable:
                    ignorable = False
                    skip = True
                    skip_chars = 0
                    continue
                if word in _RTF_SKIP_DEST:
                    skip = True
                    skip_chars = 0
                    continue
                if word == "ansicpg" and param is not None:
                    cpg = _rtf_codepage(param)
                    continue
                if word == "mac":
                    cpg = "mac_roman"
                    continue
                if word == "pc":
                    cpg = "cp437"
                    continue
                if word == "pca":
                    cpg = "cp850"
                    continue
                if word == "uc" and param is not None:
                    uc = max(0, param)
                    continue
                if word == "u" and param is not None:
                    cp = param if param >= 0 else param + 65536
                    if not skip and 0 <= cp <= 0x10FFFF:
                        out.append(chr(cp))
                    skip_chars = uc
                    continue
                if word == "bin" and param is not None and param > 0:
                    i = min(n, i + param)
                    continue
                if not skip:
                    if word in _RTF_SPECIAL:
                        out.append(_RTF_SPECIAL[word])
                    elif word == "cell":
                        out.append(" | ")
                    elif word == "row":
                        if out and out[-1] == " | ":
                            out.pop()
                        out.append("\n")
        else:
            flush_hex()
            ignorable = False
            if skip_chars > 0:
                skip_chars -= 1
                i += 1
                continue
            if not skip:
                if b < 128:
                    out.append(chr(b))
                else:
                    out.append(bytes([b]).decode(cpg, errors="replace"))
            i += 1

    flush_hex()
    return "".join(out)


# ------------------------------------------------------------------ .html / .htm / .epub
_META_CHARSET = re.compile(rb'<meta\b[^>]*?\bcharset\s*=\s*["\']?\s*([a-zA-Z0-9._-]+)', re.I)
_XML_ENCODING = re.compile(rb'<\?xml\b[^>]*?\bencoding\s*=\s*["\']([a-zA-Z0-9._-]+)["\']', re.I)
_HTML_SKIP = frozenset({"script", "style", "head", "nav", "footer", "noscript", "template"})
_HTML_BLOCK = frozenset({
    "p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6",
    "tr", "br", "hr", "section", "article", "table",
    "blockquote", "pre", "header", "main", "aside", "dl", "dt", "dd",
})
_HTML_VOID = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})


def _decode_html(raw: bytes) -> str:
    if not raw:
        return ""
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig", errors="replace")
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", errors="replace")
    head = raw[:8192]
    m = _META_CHARSET.search(head) or _XML_ENCODING.search(head)
    if m:
        enc = m.group(1).decode("ascii", errors="ignore").strip()
        try:
            codecs.lookup(enc)
            return raw.decode(enc, errors="replace")
        except LookupError:
            pass
    for enc in ("utf-8", "cp1250"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.skip_stack: list[str] = []
        self.in_pre = 0
        self.row_cells: list[str] | None = None
        self.cell_buf: list[str] | None = None

    def _newline(self) -> None:
        if self.out and not self.out[-1].endswith("\n"):
            self.out.append("\n")

    def _finish_cell(self) -> None:
        if self.cell_buf is not None:
            text = " ".join("".join(self.cell_buf).split())
            if self.row_cells is not None:
                self.row_cells.append(text)
            self.cell_buf = None

    def _finish_row(self) -> None:
        if self.row_cells is not None:
            cells = list(self.row_cells)
            while cells and not cells[-1]:
                cells.pop()
            if any(cells):
                self._newline()
                self.out.append(" | ".join(cells))
                self._newline()
            self.row_cells = None

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if self.skip_stack:
            if tag in _HTML_SKIP and tag not in _HTML_VOID:
                self.skip_stack.append(tag)
            return
        if tag in _HTML_SKIP:
            self.skip_stack.append(tag)
            return
        if tag == "pre":
            self.in_pre += 1
        if tag == "tr":
            self._finish_cell()
            self._finish_row()
            self.row_cells = []
            return
        if tag in ("td", "th"):
            if self.row_cells is None:
                self.row_cells = []
            self._finish_cell()
            self.cell_buf = []
            return
        if tag in _HTML_BLOCK:
            if self.cell_buf is not None:
                if self.cell_buf and not self.cell_buf[-1].endswith((" ", "\n")):
                    self.cell_buf.append(" ")
            else:
                self._newline()

    def handle_startendtag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if self.skip_stack or tag in _HTML_SKIP:
            return
        if tag in ("br", "hr"):
            if self.cell_buf is not None:
                self.cell_buf.append(" ")
            else:
                self._newline()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.skip_stack:
            if tag in self.skip_stack:
                while self.skip_stack:
                    if self.skip_stack.pop() == tag:
                        break
            return
        if tag == "pre" and self.in_pre > 0:
            self.in_pre -= 1
        if tag in ("td", "th"):
            self._finish_cell()
            return
        if tag == "tr":
            self._finish_cell()
            self._finish_row()
            return
        if tag == "table":
            self._finish_cell()
            self._finish_row()
            self._newline()
            return
        if tag in _HTML_BLOCK:
            if self.cell_buf is not None:
                if self.cell_buf and not self.cell_buf[-1].endswith((" ", "\n")):
                    self.cell_buf.append(" ")
            else:
                self._newline()

    def handle_data(self, data: str) -> None:
        if self.skip_stack or not data:
            return
        if self.cell_buf is not None:
            self.cell_buf.append(data)
        elif self.in_pre:
            self.out.append(data)
        else:
            self.out.append(re.sub(r"[ \t\r\n\f\v\xa0]+", " ", data))

    def result(self) -> str:
        self._finish_cell()
        self._finish_row()
        lines = (ln.strip() for ln in "".join(self.out).splitlines())
        return "\n".join(ln for ln in lines if ln)


def _extract_html_bytes(raw: bytes) -> str:
    if not raw:
        return ""
    parser = _HTMLTextExtractor()
    parser.feed(_decode_html(raw))
    parser.close()
    return parser.result()


def _read_html(p: Path) -> str:
    return _extract_html_bytes(p.read_bytes())


def _read_epub(p: Path) -> str:
    if p.stat().st_size == 0:
        return ""
    with _SafeZip(p) as sz:
        croot = ET.fromstring(sz.read_bytes("META-INF/container.xml"))
        opf_path = ""
        for el in croot.iter():
            if _local(el.tag) == "rootfile":
                opf_path = el.get("full-path") or ""
                if opf_path:
                    break
        if not opf_path:
            return ""
        opf_path = opf_path.lstrip("/")
        oroot = ET.fromstring(sz.read_bytes(opf_path))
        opf_dir = posixpath.dirname(opf_path)
        manifest: dict[str, str] = {}
        spine_ids: list[str] = []
        for el in oroot.iter():
            loc = _local(el.tag)
            if loc == "item":
                iid, href = el.get("id"), el.get("href")
                if iid and href:
                    href_clean = unquote(href.split("#", 1)[0])
                    full = posixpath.normpath(posixpath.join(opf_dir, href_clean)) if opf_dir else posixpath.normpath(href_clean)
                    manifest[iid] = full.lstrip("/")
            elif loc == "itemref":
                idref = el.get("idref")
                if idref:
                    spine_ids.append(idref)
        parts: list[str] = []
        for idref in spine_ids:
            href = manifest.get(idref)
            if not href or not sz.has(href):
                continue
            txt = _extract_html_bytes(sz.read_bytes(href))
            if txt:
                parts.append(txt)
        return "\n\n".join(parts)


# ------------------------------------------------------------------ .pptx
_PPTX_SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$", re.I)


def _pptx_para_text(el: ET.Element) -> str:
    buf: list[str] = []

    def walk(node: ET.Element) -> None:
        loc = _local(node.tag)
        if loc == "t":
            if node.text:
                buf.append(node.text)
        elif loc == "br":
            buf.append("\n")
        elif loc == "tab":
            buf.append("\t")
        for ch in node:
            walk(ch)

    walk(el)
    return "".join(buf)


def _pptx_walk(el: ET.Element, lines: list[str]) -> None:
    loc = _local(el.tag)
    if loc == "tbl":
        for child in el:
            if _local(child.tag) == "tr":
                cells: list[str] = []
                for tc in child:
                    if _local(tc.tag) == "tc":
                        p_texts = []
                        for p_el in tc.iter():
                            if _local(p_el.tag) == "p":
                                t = _pptx_para_text(p_el).strip()
                                if t:
                                    p_texts.append(t)
                        cells.append(" ".join(" ".join(p_texts).split()))
                while cells and not cells[-1]:
                    cells.pop()
                if any(cells):
                    lines.append(" | ".join(cells))
        return
    if loc == "p":
        t = _pptx_para_text(el)
        if t.strip():
            lines.append(t)
        return
    for child in el:
        _pptx_walk(child, lines)


def _read_pptx(p: Path) -> str:
    if p.stat().st_size == 0:
        return ""
    with _SafeZip(p) as sz:
        slides: list[tuple[int, str]] = []
        for name in sz.namelist():
            m = _PPTX_SLIDE_RE.match(name)
            if m:
                slides.append((int(m.group(1)), name))
        slides.sort(key=lambda x: x[0])
        out: list[str] = []
        for num, name in slides:
            root = ET.fromstring(sz.read_bytes(name))
            slide_lines: list[str] = []
            _pptx_walk(root, slide_lines)
            out.append(f"Slajd {num}")
            out.extend(slide_lines)
        return "\n".join(out)


# ------------------------------------------------------------------ .xlsx
_XLSX_SHEET_RE = re.compile(r"^xl/worksheets/sheet(\d+)\.xml$", re.I)
_CELL_COL_RE = re.compile(r"^([A-Za-z]+)")


def _col_index(ref: str) -> int:
    m = _CELL_COL_RE.match(ref)
    if not m:
        return -1
    idx = 0
    for ch in m.group(1).upper():
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def _xlsx_si_text(el: ET.Element) -> str:
    buf: list[str] = []

    def walk(node: ET.Element) -> None:
        loc = _local(node.tag)
        if loc == "rPh":
            return
        if loc == "t":
            if node.text:
                buf.append(node.text)
            return
        for ch in node:
            walk(ch)

    walk(el)
    return "".join(buf)


def _xlsx_sheets(sz: _SafeZip) -> list[tuple[str, str]]:
    rels: dict[str, str] = {}
    if sz.has("xl/_rels/workbook.xml.rels"):
        rroot = ET.fromstring(sz.read_bytes("xl/_rels/workbook.xml.rels"))
        for el in rroot.iter():
            if _local(el.tag) == "Relationship":
                rid, tgt = el.get("Id"), el.get("Target")
                if rid and tgt:
                    tgt_clean = tgt.lstrip("/")
                    if not tgt_clean.startswith("xl/"):
                        tgt_clean = posixpath.normpath(posixpath.join("xl", tgt_clean))
                    rels[rid] = tgt_clean

    numbered: list[tuple[int, str]] = []
    for name in sz.namelist():
        m = _XLSX_SHEET_RE.match(name)
        if m:
            numbered.append((int(m.group(1)), name))
    numbered.sort(key=lambda x: x[0])

    if sz.has("xl/workbook.xml"):
        wroot = ET.fromstring(sz.read_bytes("xl/workbook.xml"))
        sheets_el = [el for el in wroot.iter() if _local(el.tag) == "sheet"]
        if sheets_el:
            out: list[tuple[str, str]] = []
            for idx, el in enumerate(sheets_el):
                sname = el.get("name") or f"Arkusz {idx + 1}"
                rid = next((av for ak, av in el.attrib.items() if _local(ak) == "id"), None)
                spath = rels.get(rid) if rid else None
                if not spath or not sz.has(spath):
                    if idx < len(numbered):
                        spath = numbered[idx][1]
                    else:
                        continue
                out.append((sname, spath))
            if out:
                return out

    return [(f"Arkusz {n}", path) for n, path in numbered]


def _read_xlsx(p: Path) -> str:
    if p.stat().st_size == 0:
        return ""
    with _SafeZip(p) as sz:
        shared: list[str] = []
        if sz.has("xl/sharedStrings.xml"):
            sroot = ET.fromstring(sz.read_bytes("xl/sharedStrings.xml"))
            for el in sroot:
                if _local(el.tag) == "si":
                    shared.append(_xlsx_si_text(el))

        out: list[str] = []
        total_rows = 0
        for sname, spath in _xlsx_sheets(sz):
            if total_rows >= MAX_XLSX_ROWS:
                break
            out.append(f"Arkusz: {sname}")
            root = ET.fromstring(sz.read_bytes(spath))
            for row_el in root.iter():
                if _local(row_el.tag) != "row":
                    continue
                if total_rows >= MAX_XLSX_ROWS:
                    break
                row_vals: dict[int, str] = {}
                seq = 0
                for c_el in row_el:
                    if _local(c_el.tag) != "c":
                        continue
                    col = _col_index(c_el.get("r") or "")
                    if col < 0:
                        col = seq
                    seq = col + 1
                    ctype = c_el.get("t") or "n"
                    val = ""
                    if ctype == "inlineStr":
                        for sub in c_el:
                            if _local(sub.tag) == "is":
                                val = _xlsx_si_text(sub)
                                break
                    elif ctype == "s":
                        v_el = next((sub for sub in c_el if _local(sub.tag) == "v"), None)
                        if v_el is not None and v_el.text is not None:
                            try:
                                idx = int(v_el.text.strip())
                                if 0 <= idx < len(shared):
                                    val = shared[idx]
                            except ValueError:
                                pass
                    else:
                        v_el = next((sub for sub in c_el if _local(sub.tag) == "v"), None)
                        if v_el is not None and v_el.text is not None:
                            val = v_el.text
                    val = " ".join(val.split())
                    if val:
                        row_vals[col] = val
                if row_vals:
                    max_c = max(row_vals)
                    if max_c <= 100:
                        cells = [row_vals.get(i, "") for i in range(max_c + 1)]
                    else:
                        cells = [row_vals[i] for i in sorted(row_vals)]
                    out.append(" | ".join(cells))
                    total_rows += 1
        return "\n".join(out)


# ------------------------------------------------------------------ główny punkt wejścia
def read_text(p: Path | str) -> str:
    """Wyciąga tekst z obsługiwanego dokumentu; uszkodzone pliki dają '' i ostrzeżenie w logu."""
    path = Path(p)
    s = path.suffix.lower()
    if s not in SUPPORTED_EXT:
        return ""
    try:
        if s in TEXT_EXT:
            return _read_txt(path)
        if s == ".pdf":
            return _read_pdf(path)
        if s == ".docx":
            return _read_docx(path)
        if s == ".odt":
            return _read_odt(path)
        if s == ".rtf":
            return _read_rtf(path)
        if s in (".html", ".htm"):
            return _read_html(path)
        if s == ".epub":
            return _read_epub(path)
        if s == ".pptx":
            return _read_pptx(path)
        if s == ".xlsx":
            return _read_xlsx(path)
    except Exception as e:
        log.warning("Nie udało się odczytać %s: %s", path, e)
        return ""
    return ""
