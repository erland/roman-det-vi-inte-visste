#!/usr/bin/env python3
"""Revisionssäker bokexport enligt Romanskaparens PDF/EPUB-standard."""
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
HEADING = re.compile(r"^#\s+(\d+)\.\s+(.+?)\s*$", re.M)

def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)

def latex_escape(s: str) -> str:
    return re.sub(r'[\\&%$#_{}~^]', lambda m: {'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}[m.group()], s)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--project-root', type=Path, default=ROOT)
    ap.add_argument('--output-dir', type=Path, required=True)
    ap.add_argument('--format', choices=['epub','pdf','both'], default='both')
    args = ap.parse_args()
    root, out = args.project_root.resolve(), args.output_dir.resolve()
    if root == out or root in out.parents:
        raise SystemExit('Export output directory must be outside tracked project tree')
    run([sys.executable, str(root/'scripts/project_integrity.py'),'verify',str(root)])
    manifest = json.loads((root/'project-manifest.json').read_text(encoding='utf-8'))
    chapters = sorted((root/'kapitel').glob('kapitel-*.md'))
    nums = [int(CHAPTER.fullmatch(f.name).group(1)) for f in chapters if CHAPTER.fullmatch(f.name)]
    if len(chapters) != len(nums) or nums != list(range(1,len(nums)+1)) or len(nums) != manifest['chapters']['count']:
        raise SystemExit('Invalid chapter ordering or inventory')
    metadata = root/'publishing/metadata.yaml'
    meta = metadata.read_text(encoding='utf-8')
    def value(key):
        m = re.search(r'^'+re.escape(key)+r':\s*["\']?(.*?)["\']?\s*$',meta,re.M)
        return m.group(1).strip('"\' ') if m else ''
    title, author = value('title'), value('author')
    if not title or not author: raise SystemExit('Title and author required')
    cover = root/'publishing/cover.png'
    if not cover.is_file(): raise SystemExit('Approved cover missing: publishing/cover.png')
    source_text = '\n\n'.join(p.read_text(encoding='utf-8') for p in chapters)
    headings = HEADING.findall(source_text)
    if len(headings) != len(nums) or [int(n) for n,_ in headings] != nums:
        raise SystemExit('Chapter headings must be # N. Chapter title')
    out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp)
        source=d/'book.md';source.write_text(source_text,encoding='utf-8')
        opts=['pandoc',str(source),'--standalone','--metadata-file',str(metadata),'--resource-path',str(root)]
        if args.format in ('epub','both'):
            epub=out/'roman.epub'
            run(opts+['--to=epub3','--toc','--toc-depth=1','--split-level=1','--css',str(root/'publishing/epub.css'),'-o',str(epub)],cwd=root)
            run([sys.executable,str(root/'publishing/fix-epub-after-pandoc.py'),str(epub)])
        if args.format in ('pdf','both'):
            # Manually construct PDF front matter before the TOC, without Pandoc's default title.
            # H1 chapter headings become unnumbered LaTeX chapters with proper TOC and links.
            def chapter(m):
                n,name=m.group(1),latex_escape(m.group(2))
                label=latex_escape(n+'. '+m.group(2))
                return '\\clearpage\n\\phantomsection\n\\addcontentsline{toc}{chapter}{'+label+'}\n\\chapter*{\\centering\\normalfont '+n+r'\\[0.2em]'+name+'}\n'
            pdf_body=HEADING.sub(chapter,source_text)
            front = (r'\begin{titlepage}'+'\n'+r'\pagenumbering{gobble}'+'\n'+r'\thispagestyle{empty}'+'\n'+r'\centering'+'\n'
                +r'\includegraphics[width=\paperwidth,height=0.96\paperheight,keepaspectratio]{'+str(cover)+'}\n'+r'\end{titlepage}'+'\n'
                +r'\begin{titlepage}\thispagestyle{empty}\centering\vspace*{0.30\textheight}'+'\n'
                +r'{\Huge\bfseries '+latex_escape(title)+r'\par}'+'\n'+r'\vspace{2em}'+'\n'
                +r'{\Large '+latex_escape(author)+r'\par}'+'\n'+r'\end{titlepage}'+'\n'
                +r'\tableofcontents'+'\n'+r'\clearpage'+'\n'+r'\pagenumbering{arabic}'+'\n')
            pdf_input=d/'book-pdf.md';pdf_input.write_text(front+'\n'+pdf_body,encoding='utf-8')
            header=d/'header.tex';header.write_text(r'\usepackage{graphicx}'+'\n'+r'\usepackage{titlesec}'+'\n'+r'\titlespacing*{\chapter}{0pt}{0.8em}{0.7em}'+'\n',encoding='utf-8')
            run(['pandoc',str(pdf_input),'--include-in-header',str(header),'--standalone','--from=markdown+raw_tex',
                '--pdf-engine=xelatex','--top-level-division=chapter',
                '--metadata=title:','--metadata=author:',
                '-V','documentclass=book','-V','classoption=oneside,openany','-V','papersize=a5',
                '-V','geometry:margin=18mm','-V','fontsize=11pt',
                '--output',str(out/'roman.pdf')],cwd=root)
            # Pandoc/book's generated empty leading leaf is not a legitimate cover.
            # Strip only if first page contains no content and next page has the cover image.
            from pypdf import PdfReader, PdfWriter
            pdf_path=out/'roman.pdf'
            pdf=PdfReader(str(pdf_path))
            if len(pdf.pages)>1 and not (pdf.pages[0].extract_text() or '').strip() and len(pdf.pages[1].images)>0:
                writer=PdfWriter()
                for page in pdf.pages[1:]:writer.add_page(page)
                staged=d/'trimmed.pdf'
                with staged.open('wb') as stream:writer.write(stream)
                staged.replace(pdf_path)

    run([sys.executable,str(root/'scripts/project_integrity.py'),'verify',str(root)])
    return 0

if __name__=='__main__':raise SystemExit(main())
