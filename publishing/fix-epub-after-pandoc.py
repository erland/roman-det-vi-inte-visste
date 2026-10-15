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
    nav_done=0;heading_done=0;cover_done=0;cover_image_done=0
    for name,(info,data) in list(files.items()):
        if name.endswith('.opf'):
            root=ET.fromstring(data)
            manifest=root.find(f'{{{O}}}manifest')
            spine=root.find(f'{{{O}}}spine')
            if manifest is None or spine is None:raise SystemExit('Missing EPUB manifest/spine')
            cover_item=next((i for i in manifest.findall(f'{{{O}}}item') if i.get('href','').endswith('cover.xhtml')),None)
            if cover_item is None:raise SystemExit('Missing EPUB cover XHTML')
            cover_refs=[i for i in spine.findall(f'{{{O}}}itemref') if i.get('idref')==cover_item.get('id')]
            if len(cover_refs)!=1:raise SystemExit('Cover must occur once in EPUB spine')
            cover_ref=cover_refs[0]
            spine.remove(cover_ref);spine.insert(0,cover_ref);cover_ref.set('linear','yes');cover_done+=1
            for itemref in root.findall(f'.//{{{O}}}spine/{{{O}}}itemref'):
                ident=itemref.get('idref')
                match=root.find(f'.//{{{O}}}manifest/{{{O}}}item[@id="{ident}"]')
                if match is not None and 'nav' in match.get('properties','').split():
                    itemref.set('linear','no');nav_done+=1
            files[name]=(info,ET.tostring(root,encoding='utf-8',xml_declaration=True))
        if name.endswith('.xhtml') and 'nav.' not in name:
            root=ET.fromstring(data)
            if name.endswith('cover.xhtml'):
                cover_div=next((d for d in root.findall(f'.//{{{X}}}div') if d.get('id')=='cover-image'),None)
                if cover_div is None:raise SystemExit('Missing cover-image container')
                for child in list(cover_div):cover_div.remove(child)
                img=ET.SubElement(cover_div,f'{{{X}}}img',{'src':'../media/cover.png','alt':'Omslag: Det vi inte visste – Erland Lindmark'})
                cover_image_done+=1
            # The first paragraph after the heading gets no indent.
            for section in root.findall(f'.//{{{X}}}section'):
                if 'level1' not in section.get('class','').split():continue
                paragraphs=section.findall(f'{{{X}}}p')
                if paragraphs:paragraphs[0].set('class',(paragraphs[0].get('class','')+' first-paragraph').strip())

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
    if not cover_done or not cover_image_done:raise SystemExit('EPUB cover not normalized')
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
