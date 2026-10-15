#!/usr/bin/env python3
"""Minimal efterkontroll: skriv ut instruktion om Pandocs EPUB-nav.
Fullständig EPUB-efterbearbetning kräver validerat Pandoc-resultat."""
from pathlib import Path
import sys
if __name__ == '__main__':
    if len(sys.argv)!=2 or not Path(sys.argv[1]).is_file():
        raise SystemExit('Användning: python fix-epub-after-pandoc.py bok.epub')
    print('Kontrollera nav.xhtml (behåll navigationsindex; markera spine linear=no vid behov).')
