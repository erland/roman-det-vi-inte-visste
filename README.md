# Det vi inte visste – Romanprojekt

Revisionslåst romanprojekt i Romanskaparens fasta struktur. Romanbibeln, synopsis och 35 detaljerade kapitelplaner finns här. Detta är ett eget romanprojekt och ska inte blandas med Gränslandet eller annan ZIP. Aktuell revision, kapitelinventering och nästa steg finns i manifest, projektstatus och project-index.

## Start
1. Läs `roman-bibel.md`, `kontinuitetsanteckningar.md`, `kapitelplan.md`, `tidslinje.md`, `stilguide.md` och relevanta karaktärsfiler.
2. Kontrollera: `python scripts/project_integrity.py verify .`
3. Läs den verifierade kapitelinventeringen och skapa endast nästa planerade `kapitel/kapitel-XX.md`; ändra samtidigt endast motiverade synkfiler. Tidigare kapitel skyddas byte-identiskt.
4. Kör `status` och `commit --expected-revision <källrevision> --zip-name <slug>-rNNNN-kapitel-XX.zip --allow ...` med exakt tillåten ändringslista enligt integritetsverktygets hjälp.
5. Paketera hela romanprojekt-trädet, återpacka upp och verifiera före leverans.

## Källor och avgränsning
Romanens inspirationsmaterial är eSams radarbild februari 2026 (ES2026-03) och användarens analys *Digital omställning i en föränderlig omvärld* daterad 2026-10-14. Berättelsen, myndigheten och händelserna är fiktiva. Materialet ger tematisk inramning, inte operativa instruktioner.

## Status
Titel: Det vi inte visste. Författare: Erland Lindmark. Undertitel ej fastställd. Genre: realistisk samtidsroman med organisationsdrama och spänning. Målgrupp: vuxna. Omslagsbild fastställd i `publishing/cover.png`. 35 kapitel planerade. Antal skrivna och godkända kapitel samt nästa kapitel hämtas från projektstatus, project-index och manifestet.
