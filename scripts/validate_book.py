#!/usr/bin/env python3
"""Check book outputs without changing sources or the project manifest."""
from __future__ import annotations
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--project-root", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--format", choices=["epub", "pdf", "both"], default="both")
    a = p.parse_args()
    root, out = a.project_root.resolve(), a.output_dir.resolve()
    manifest = json.loads((root / "project-manifest.json").read_text(encoding="utf-8"))
    count = manifest["chapters"]["count"]
    if count < 1:
        raise SystemExit("No chapters to validate")
    if a.format in ("epub", "both"):
        f = out / "roman.epub"
        with zipfile.ZipFile(f) as z:
            if z.testzip() is not None or z.read("mimetype") != b"application/epub+zip":
                raise SystemExit("Invalid EPUB archive")
            names = z.namelist()
            # The cover must be an actual first reading-order document,
            # not merely a cover-image property for library thumbnails.
            opfs=[n for n in names if n.endswith('.opf')]
            if len(opfs)!=1: raise SystemExit('Expected one EPUB package file')
            opf=ET.fromstring(z.read(opfs[0]))
            ns={'o':'http://www.idpf.org/2007/opf'}
            items={i.get('id'):i for i in opf.findall('.//o:manifest/o:item',ns)}
            refs=opf.findall('.//o:spine/o:itemref',ns)
            if not refs or refs[0].get('idref') not in items:
                raise SystemExit('Missing first EPUB spine item')
            cover=items[refs[0].get('idref')]
            if not cover.get('href','').endswith('cover.xhtml') or refs[0].get('linear')=='no':
                raise SystemExit('EPUB must open with a linear cover page')
            css_text='\n'.join(z.read(n).decode('utf-8') for n in names if n.endswith('.css'))
            if 'section.level1 p {text-indent:1.15em;' not in css_text:
                raise SystemExit('Missing readable novel paragraph indentation')
            cover_name=next(n for n in names if n.endswith('cover.xhtml'))
            cover_xhtml=z.read(cover_name)
            if b'<img ' not in cover_xhtml or b'../media/cover.png' not in cover_xhtml:
                raise SystemExit('EPUB cover must be a visible XHTML image, not SVG only')

            navs = [name for name in names if name.endswith("nav.xhtml")]
            if not navs:
                raise SystemExit("Missing EPUB navigation")
            nav = z.read(navs[0])
            ET.fromstring(nav)
            references = re.findall(rb'href="[^"]+\.xhtml(?:#[^"]*)?"', nav)
            if len(references) < count:
                raise SystemExit("EPUB has too few navigation links")
    if a.format in ("pdf", "both"):
        b = (out / "roman.pdf").read_bytes()
        if not b.startswith(b"%PDF-") or b"%%EOF" not in b[-2048:]:
            raise SystemExit("Invalid PDF")
        from pypdf import PdfReader
        pdf = PdfReader(str(out / "roman.pdf"))
        if not pdf.pages or len(pdf.pages[0].images) == 0:
            raise SystemExit("PDF does not start with cover image")
        if count and len(pdf.pages) < count:
            raise SystemExit("PDF has fewer pages than chapters")
    print(f"BOOK VALIDATION: PASS ({count} chapters, {a.format})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
