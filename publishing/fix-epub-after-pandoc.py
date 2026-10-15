#!/usr/bin/env python3
"""EPUB3 efterbearbetning: osynligt nav i läsflödet, centrerad titelsida och kapitelsättning."""
from __future__ import annotations
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

X='http://www.w3.org/1999/xhtml'; O='http://www.idpf.org/2007/opf'
ET.register_namespace('',X)

def transform(path: Path) -> None:
    with zipfile.ZipFile(path) as source:
        files={i.filename:(i,source.read(i.filename)) for i in source.infolist()}
    nav_done=0;heading_done=0
    for name,(info,data) in list(files.items()):
        if name.endswith('.opf'):
            root=ET.fromstring(data)
            for itemref in root.findall(f'.//{{{O}}}spine/{{{O}}}itemref'):
                ident=itemref.get('idref')
                match=root.find(f'.//{{{O}}}manifest/{{{O}}}item[@id="{ident}"]')
                if match is not None and 'nav' in match.get('properties','').split():
                    itemref.set('linear','no');nav_done+=1
            files[name]=(info,ET.tostring(root,encoding='utf-8',xml_declaration=True))
        if name.endswith('.xhtml') and 'nav.' not in name:
            root=ET.fromstring(data)
            for h1 in root.findall(f'.//{{{X}}}h1'):
                txt=''.join(h1.itertext()).strip()
                m=re.match(r'^(\d+)\.\s+(.+)$',txt)
                if not m:continue
                h1.clear() if False else None
                for ch in list(h1):h1.remove(ch)
                h1.text=None
                a=ET.SubElement(h1,f'{{{X}}}span',{'class':'chapter-number'});a.text=m.group(1)
                b=ET.SubElement(h1,f'{{{X}}}span',{'class':'chapter-title'});b.text=m.group(2)
                heading_done+=1
            files[name]=(info,ET.tostring(root,encoding='utf-8',xml_declaration=True))
    if not nav_done:raise SystemExit('EPUB navigation manifest item missing in spine')
    if not heading_done:raise SystemExit('No chapter headings formatted')
    with tempfile.NamedTemporaryFile(suffix='.epub',dir=path.parent,delete=False) as tmp: dest=Path(tmp.name)
    try:
        with zipfile.ZipFile(dest,'w') as out:
            for name,(info,data) in files.items():
                compress=zipfile.ZIP_STORED if name=='mimetype' else zipfile.ZIP_DEFLATED
                out.writestr(info,data,compress_type=compress)
        dest.replace(path)
    finally:
        if dest.exists():dest.unlink()
    print(f'EPUB POSTPROCESS: {heading_done} chapters, {nav_done} nav spine items hidden')

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: fix-epub-after-pandoc.py file.epub')
    transform(Path(sys.argv[1]))
