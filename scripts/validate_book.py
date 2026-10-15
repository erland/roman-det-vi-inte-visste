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
