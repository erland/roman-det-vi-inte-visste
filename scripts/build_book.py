#!/usr/bin/env python3
"""Read-only, repeatable EPUB/PDF export from a verified Romanskaparen project."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = re.compile(r"kapitel-(\d{2,})\.md$")

def run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, check=True, cwd=cwd)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--format", choices=["epub", "pdf", "both"], default="both")
    args = parser.parse_args()
    root = args.project_root.resolve()
    output = args.output_dir.resolve()
    if root == output or root in output.parents:
        raise SystemExit("Output directory must be outside the tracked project tree")
    run([sys.executable, str(root / "scripts/project_integrity.py"), "verify", str(root)])
    manifest = json.loads((root / "project-manifest.json").read_text(encoding="utf-8"))
    chapters = sorted((root / "kapitel").glob("kapitel-*.md"))
    numbers = [int(CHAPTER.fullmatch(p.name).group(1)) for p in chapters if CHAPTER.fullmatch(p.name)]
    if not numbers or len(numbers) != len(chapters) or numbers != list(range(1, len(numbers) + 1)):
        raise SystemExit("Missing, duplicate, or noncanonical chapter files")
    if len(numbers) != manifest["chapters"]["count"]:
        raise SystemExit("Chapter inventory differs from manifest")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "book.md"
        source.write_text("\n\n".join(p.read_text(encoding="utf-8") for p in chapters), encoding="utf-8")
        title = root / "publishing/metadata.yaml"
        css = root / "publishing/epub.css"
        options = ["pandoc", str(source), "--standalone", "--toc", "--toc-depth=1", "--metadata=lang:sv-SE"]
        if title.exists():
            options += ["--metadata-file", str(title)]
        if args.format in ("epub", "both"):
            target = output / "roman.epub"
            cmd = options + ["--split-level=1", "--to=epub3", "--output", str(target)]
            if css.exists():
                cmd += ["--css", str(css)]
            run(cmd, cwd=root)
            fixer = root / "publishing/fix-epub-after-pandoc.py"
            if fixer.exists():
                # The project-local checker accepts one argument and does not rewrite the EPUB.
                run([sys.executable, str(fixer), str(target)])
        if args.format in ("pdf", "both"):
            target = output / "roman.pdf"
            cmd = options + ["--pdf-engine=xelatex", "--top-level-division=chapter",
                              "-V", "documentclass=book", "-V", "papersize=a5",
                              "-V", "geometry:margin=18mm", "-V", "fontsize=11pt",
                              "--output", str(target)]
            header = root / "publishing/pdf-template.tex"
            # The project PDF file is a full LaTeX template, not a header fragment.
            # Use Pandoc default template to preserve its generated TOC.
            # It must not be passed as --include-in-header.
            run(cmd, cwd=root)
    run([sys.executable, str(root / "scripts/project_integrity.py"), "verify", str(root)])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
