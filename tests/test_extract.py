"""Testy ekstraktorów dokumentów (uruchamialne przez `python tests\\test_extract.py` oraz `pytest`)."""
from __future__ import annotations

import io
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sejf.extract import MAX_XLSX_ROWS, SUPPORTED_EXT, read_text  # noqa: E402
from sejf.retriever_simple import Index, read_text as retriever_read_text  # noqa: E402
from sejf.webapi import UPLOAD_EXT, safe_upload_name  # noqa: E402

PL = "zażółć gęślą jaźń"


def _make_odt(path: Path, code: str) -> None:
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0">
  <office:automatic-styles><style:style xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" style:name="IgnorowanyStyl"/></office:automatic-styles>
  <office:body>
    <office:text>
      <text:h text:outline-level="1">Nagłówek ODT {code}</text:h>
      <text:p>Tekst polski: {PL}<text:s text:c="2"/>koniec<text:tab/>tabulacja<text:line-break/>nowa linia</text:p>
      <text:list>
        <text:list-item><text:p>Element listy pierwszy</text:p></text:list-item>
        <text:list-item><text:p>Element listy drugi</text:p></text:list-item>
      </text:list>
      <table:table>
        <table:table-row>
          <table:table-cell><text:p>Kolumna A</text:p></table:table-cell>
          <table:table-cell><text:p>Wartość 123</text:p></table:table-cell>
        </table:table-row>
      </table:table>
    </office:text>
  </office:body>
</office:document-content>"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/vnd.oasis.opendocument.text")
        zf.writestr("content.xml", content.encode("utf-8"))


def _make_rtf(path: Path, code: str) -> None:
    # Zawiera: fonttbl/colortbl/stylesheet/info/pict oraz \*\destination, \'b3\'f3, \u322? i cp1250
    rtf = (
        r"{\rtf1\ansi\ansicpg1250\uc1 "
        r"{\fonttbl{\f0 Arial;}}"
        r"{\colortbl;\red0\green0\blue0;}"
        r"{\stylesheet{\s0 Normal;}}"
        r"{\info{\title Ignorowany Tytul}}"
        r"{\pict\pngblip 89504e47}"
        r"{\*\generator IgnorowanyGenerator}"
        r"Kod RTF: " + code + r"\par "
        r"za\'bf\'f3\u322?\'e6 g\'ea\'9cl\'b9 ja\'9f\'f1\line "
        r"Kolumna1\tab Kolumna2\par "
        r"Kom\'f3rka1\cell Kom\'f3rka2\cell\row"
        r"}"
    )
    path.write_bytes(rtf.encode("ascii"))


def _make_html(path: Path, code: str) -> None:
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="cp1250">
  <title>Ignorowany tytuł</title>
  <style>body {{ color: red; }}</style>
  <script>var secret = "TO_NIE_MA_BYC_WIDOCZNE_{code}";</script>
</head>
<body>
  <nav><a href="/">Menu nawigacji</a></nav>
  <main>
    <h1>Tytuł HTML {code}</h1>
    <p>Polskie znaki: {PL} &amp; encje &#322;&#243;d&#378;.</p>
    <div>Blok pierwszy<br>po złamaniu</div>
    <ul><li>Punkt pierwszy</li><li>Punkt drugi</li></ul>
    <section><article>Sekcja artykułu</article></section>
    <table>
      <tr><th>Nazwa</th><th>Kwota</th></tr>
      <tr><td>Usługa</td><td>450 zł</td></tr>
    </table>
  </main>
  <footer>Stopka strony</footer>
</body>
</html>"""
    path.write_bytes(html.encode("cp1250"))


def _make_epub(path: Path, code: str) -> None:
    container = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
    opf = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <manifest>
    <item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1"/>
    <itemref idref="ch2"/>
  </spine>
</package>"""
    ch1 = f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>R1</title><script>var hide="UKRYTY_SKRYPT_EPUB";</script></head>
<body><h1>Rozdział pierwszy {code}</h1><p>{PL}</p></body>
</html>"""
    ch2 = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body><p>Rozdział drugi po pierwszym</p><table><tr><td>A</td><td>B</td></tr></table></body>
</html>"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", container.encode("utf-8"))
        zf.writestr("OEBPS/content.opf", opf.encode("utf-8"))
        zf.writestr("OEBPS/ch1.xhtml", ch1.encode("utf-8"))
        zf.writestr("OEBPS/ch2.xhtml", ch2.encode("utf-8"))


def _make_pptx(path: Path, code: str) -> None:
    def slide_xml(body: str) -> bytes:
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            f"<p:cSld><p:spTree>{body}</p:spTree></p:cSld></p:sld>"
        ).encode("utf-8")

    s1 = slide_xml(f"<p:sp><p:txBody><a:p><a:r><a:t>Pierwszy {code}</a:t></a:r></a:p>"
                   f"<a:p><a:r><a:t>{PL}</a:t></a:r></a:p></p:txBody></p:sp>")
    s2 = slide_xml("<p:sp><p:txBody><a:p><a:r><a:t>Drugi slajd</a:t></a:r></a:p></p:txBody></p:sp>")
    s10 = slide_xml("<p:sp><p:txBody><a:p><a:r><a:t>Dziesiąty slajd</a:t></a:r></a:p></p:txBody></p:sp>")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Celowo zapisujemy w kolejności 1, 10, 2, aby sprawdzić sortowanie numeryczne
        zf.writestr("ppt/slides/slide1.xml", s1)
        zf.writestr("ppt/slides/slide10.xml", s10)
        zf.writestr("ppt/slides/slide2.xml", s2)


def _make_xlsx(path: Path, code: str, extra_rows: int = 0) -> None:
    workbook = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Faktury" sheetId="1" r:id="rId1"/>
    <sheet name="Podsumowanie" sheetId="2" r:id="rId2"/>
  </sheets>
</workbook>"""
    rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="/xl/worksheets/sheet2.xml"/>
</Relationships>"""
    shared = f"""<?xml version="1.0" encoding="UTF-8"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="2" uniqueCount="2">
  <si><t>{PL}</t></si>
  <si><r><t>Kod </t></r><r><t>{code}</t></r></si>
</sst>"""
    rows1 = [
        '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c><c r="C1"><v>2026</v></c></row>',
        '<row r="2"><c r="A2" t="inlineStr"><is><t>Pozycja inline</t></is></c><c r="B2" t="n"><v>99.5</v></c></row>',
    ]
    for idx in range(extra_rows):
        rnum = idx + 3
        rows1.append(f'<row r="{rnum}"><c r="A{rnum}" t="inlineStr"><is><t>wiersz_{idx}</t></is></c></row>')
    sheet1 = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
        + "".join(rows1)
        + "</sheetData></worksheet>"
    )
    sheet2 = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
        '<row r="1"><c r="A1" t="inlineStr"><is><t>Suma końcowa</t></is></c><c r="B1"><v>500</v></c></row>'
        "</sheetData></worksheet>"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("xl/workbook.xml", workbook.encode("utf-8"))
        zf.writestr("xl/_rels/workbook.xml.rels", rels.encode("utf-8"))
        zf.writestr("xl/sharedStrings.xml", shared.encode("utf-8"))
        zf.writestr("xl/worksheets/sheet1.xml", sheet1.encode("utf-8"))
        zf.writestr("xl/worksheets/sheet2.xml", sheet2.encode("utf-8"))


def _make_docx(path: Path, code: str) -> None:
    import docx

    d = docx.Document()
    d.add_paragraph(f"Akapit pierwszy {code}: {PL}")
    tbl = d.add_table(rows=2, cols=2)
    tbl.cell(0, 0).text = "Komórka A1"
    tbl.cell(0, 1).text = "Komórka B1"
    tbl.cell(1, 0).text = "Komórka A2"
    tbl.cell(1, 1).text = "Komórka B2"
    d.add_paragraph("Akapit po tabeli")
    d.save(str(path))


def test_all_formats_and_polish_chars():
    with tempfile.TemporaryDirectory(prefix="sejf_ext_") as tmp:
        d = Path(tmp)

        txt_p = d / "stary.txt"
        txt_p.write_bytes(f"Kod TXT_CP1250: {PL}\n".encode("cp1250"))
        assert PL in read_text(txt_p) and "TXT_CP1250" in read_text(txt_p)

        md_p = d / "notatka.md"
        md_p.write_bytes(f"\ufeff# Nagłówek MD_BOM: {PL}\n".encode("utf-8"))
        md_txt = read_text(md_p)
        assert md_txt.startswith("# Nagłówek MD_BOM") and PL in md_txt

        odt_p = d / "dokument.odt"
        _make_odt(odt_p, "KOD_ODT_11")
        odt_txt = read_text(odt_p)
        assert "Nagłówek ODT KOD_ODT_11" in odt_txt
        assert f"Tekst polski: {PL}  koniec\ttabulacja\nnowa linia" in odt_txt
        assert "Element listy pierwszy" in odt_txt
        assert "Kolumna A | Wartość 123" in odt_txt

        rtf_p = d / "pismo.rtf"
        _make_rtf(rtf_p, "KOD_RTF_22")
        rtf_txt = read_text(rtf_p)
        assert "KOD_RTF_22" in rtf_txt
        assert PL in rtf_txt
        assert "Kolumna1\tKolumna2" in rtf_txt
        assert "Komórka1 | Komórka2" in rtf_txt
        assert "Ignorowany" not in rtf_txt and "89504e47" not in rtf_txt

        html_p = d / "strona.html"
        _make_html(html_p, "KOD_HTML_33")
        html_txt = read_text(html_p)
        assert "Tytuł HTML KOD_HTML_33" in html_txt
        assert f"Polskie znaki: {PL} & encje łódź." in html_txt
        assert "Blok pierwszy\npo złamaniu" in html_txt
        assert "Nazwa | Kwota" in html_txt and "Usługa | 450 zł" in html_txt
        assert "TO_NIE_MA_BYC_WIDOCZNE" not in html_txt
        assert "Menu nawigacji" not in html_txt
        assert "Stopka strony" not in html_txt
        assert "Ignorowany tytuł" not in html_txt

        htm_p = d / "krotka.htm"
        htm_p.write_bytes(f"<p>KOD_HTM_34 {PL}</p>".encode("utf-8"))
        assert "KOD_HTM_34" in read_text(htm_p) and PL in read_text(htm_p)

        epub_p = d / "ksiazka.epub"
        _make_epub(epub_p, "KOD_EPUB_44")
        epub_txt = read_text(epub_p)
        assert "Rozdział pierwszy KOD_EPUB_44" in epub_txt
        assert PL in epub_txt
        assert "A | B" in epub_txt
        assert "UKRYTY_SKRYPT_EPUB" not in epub_txt
        assert epub_txt.index("Rozdział pierwszy") < epub_txt.index("Rozdział drugi")

        pptx_p = d / "prezentacja.pptx"
        _make_pptx(pptx_p, "KOD_PPTX_55")
        pptx_txt = read_text(pptx_p)
        assert "Slajd 1" in pptx_txt and "Slajd 2" in pptx_txt and "Slajd 10" in pptx_txt
        assert f"Pierwszy KOD_PPTX_55\n{PL}" in pptx_txt
        assert pptx_txt.index("Slajd 1") < pptx_txt.index("Slajd 2") < pptx_txt.index("Slajd 10")

        xlsx_p = d / "arkusz.xlsx"
        _make_xlsx(xlsx_p, "KOD_XLSX_66")
        xlsx_txt = read_text(xlsx_p)
        assert "Arkusz: Faktury" in xlsx_txt and "Arkusz: Podsumowanie" in xlsx_txt
        assert f"{PL} | Kod KOD_XLSX_66 | 2026" in xlsx_txt
        assert "Pozycja inline | 99.5" in xlsx_txt
        assert "Suma końcowa | 500" in xlsx_txt

        docx_p = d / "umowa.docx"
        _make_docx(docx_p, "KOD_DOCX_77")
        docx_txt = read_text(docx_p)
        assert f"Akapit pierwszy KOD_DOCX_77: {PL}" in docx_txt
        assert "Komórka A1 | Komórka B1" in docx_txt
        assert "Komórka A2 | Komórka B2" in docx_txt
        assert docx_txt.index("Akapit pierwszy") < docx_txt.index("Komórka A1") < docx_txt.index("Akapit po tabeli")

        # Delegacja retriever_simple.read_text i spójność Index._files()
        assert retriever_read_text(odt_p) == odt_txt
        (d / "stary.doc").write_bytes(b"binary doc")
        (d / "~$blokada.docx").write_bytes(b"temp")
        fake_idx = Index.__new__(Index)
        fake_idx.folder = d
        found = {p.name for p in fake_idx._files()}
        assert found == {
            "stary.txt", "notatka.md", "dokument.odt", "pismo.rtf",
            "strona.html", "krotka.htm", "ksiazka.epub", "prezentacja.pptx", "arkusz.xlsx", "umowa.docx",
        }
        assert UPLOAD_EXT == SUPPORTED_EXT
        assert safe_upload_name("pismo.odt") == "pismo.odt"
        assert safe_upload_name("stary.doc") is None
        assert safe_upload_name("arkusz.ods") is None


def test_corrupted_empty_and_limits():
    with tempfile.TemporaryDirectory(prefix="sejf_bad_") as tmp:
        d = Path(tmp)
        for ext in sorted(SUPPORTED_EXT):
            empty = d / f"pusty{ext}"
            empty.write_bytes(b"")
            assert read_text(empty) == "", ext

            broken = d / f"zepsuty{ext}"
            broken.write_bytes(b"\x00\xff\xfe\x81not-a-valid-file-content")
            res = read_text(broken)
            assert isinstance(res, str)
            if ext not in (".txt", ".md", ".csv", ".tsv", ".html", ".htm"):
                assert res == "", ext

        # Zip-bomba (członek deklarujący > 200 MB w nagłówku central directory)
        decl_bomb = d / "deklaracja_bomba.odt"
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.xml", b"<office:document-content/>")
        raw_zip = bytearray(buf.getvalue())
        # Podmieniamy rozmiar nieskompresowany w nagłówku central directory (PK\x01\x02, offset +24)
        cd_pos = raw_zip.rfind(b"PK\x01\x02")
        assert cd_pos >= 0
        raw_zip[cd_pos + 24:cd_pos + 28] = (500 * 1024 * 1024).to_bytes(4, "little")
        decl_bomb.write_bytes(bytes(raw_zip))
        assert read_text(decl_bomb) == ""

        # Zip-bomba (ODT z content.xml > 200 MB po rozpakowaniu)
        bomb_odt = d / "bomba.odt"
        big_xml = b"<office:document-content>" + (b" " * (205 * 1024 * 1024)) + b"</office:document-content>"
        with zipfile.ZipFile(bomb_odt, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.xml", big_xml)
        assert read_text(bomb_odt) == ""

        # Zip-bomba (zbyt wiele plików w archiwum)
        many_odt = d / "duzo.odt"
        with zipfile.ZipFile(many_odt, "w", zipfile.ZIP_STORED) as zf:
            for k in range(10_005):
                zf.writestr(f"f{k}.txt", b"x")
            zf.writestr("content.xml", b"<office:document-content/>")
        assert read_text(many_odt) == ""

        # Limit 20 000 wierszy w .xlsx
        huge_xlsx = d / "ogromny.xlsx"
        _make_xlsx(huge_xlsx, "LIMIT", extra_rows=MAX_XLSX_ROWS + 50)
        huge_txt = read_text(huge_xlsx)
        assert f"wiersz_{MAX_XLSX_ROWS - 3}" in huge_txt
        assert f"wiersz_{MAX_XLSX_ROWS}" not in huge_txt


if __name__ == "__main__":
    test_all_formats_and_polish_chars()
    test_corrupted_empty_and_limits()
    print("OK: test_extract")
