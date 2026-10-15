# Publiceringsanteckningar

Export av EPUB/PDF görs först när manuskapitel finns. Läs enbart godkända kapitelfiler i nummerordning; använd projektets metadata och EPUB-CSS/PDF-mall; kontrollera klickbart navigeringsindex, sidbrytningar och separat titelsida. Exportera inte romanbibel, projektloggar eller kapitelnoteringar som skönlitterär text. `publishing/fix-epub-after-pandoc.py` kan bearbeta en Pandoc-genererad EPUB om detta behövs.


## Provläsningsbygge r114 (2026-10-15)
Källa: revision 113, 35 kapitel; källfiler ändrades inte. EPUB genererad med Pandoc EPUB3 och postprocessad för kapitelrubriker på två rader samt `nav.xhtml` som icke-linjärt spine-innehåll. PDF skapad från samma Pandoc-Markdown med XeLaTeX, A5-format, Noto Serif, separat titelsida och tvåsidig innehållsförteckning. EPUB/PDF är provläsningsutgåvor utan fastställt författarnamn och utan omslag. PDF: 311 sidor.

## Omslagsbild r117 (2026-10-15)
Omslagsbilden är fastställd och lagd som `publishing/cover.png`. `publishing/metadata.yaml` pekar nu på bilden via `cover-image`. Nästa EPUB/PDF-export ska använda denna bild utan att ändra kapiteltexten.
