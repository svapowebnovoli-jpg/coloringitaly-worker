# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Preferenze di collaborazione

- Rispondere sempre **prima in italiano, poi in inglese** nella stessa risposta.

## Contesto strategico

Il progetto produce **coloring book per adulti a tema italiano** venduti sul negozio Etsy **BagarreBazaar**, sezione **Ink & Roads**.

**Obiettivo:** automatizzare al 90% la pipeline di produzione — dall'immagine grezza al file pronto per Etsy/KDP — riducendo al minimo l'intervento manuale.

**Prossimi step pianificati:**
- Endpoint `/genera_cover` — generazione automatica della copertina
- Pipeline clipart — gestione e assemblaggio di elementi grafici riutilizzabili

## Expertise Prodotti Digitali / Digital Products Expertise

---

### 1. Coloring Book Adulti

**IT — Specifiche tecniche:**
- Interior PDF: 300 DPI, trim size US Letter (8,5"×11") o A4, carta bianca (white, non cream), pagina bianca dopo ogni disegno
- Cover PDF: 300 DPI, full wrap con bleed 0,125" su tutti i lati
- Etsy digitale: max 20 MB per file, consegnare PDF+ZIP
- KDP: 24–828 pagine, max 650 MB interior

**IT — Nicchie top 2025:**
- Italia/viaggio/monumenti (la nostra nicchia attuale — alta domanda, bassa concorrenza italiana)
- Botanica/fiori/giardini vintage
- Mindfulness/mandala/zen
- Dark academia e gothic
- Cottagecore/funghi/natura
- Architettura line art (Roma, Venezia, Firenze)

**IT — Pricing strategy:**
- Etsy digitale singolo: €3–8
- Etsy bundle (2–3 libri): €8–15
- KDP fisico: €12–25 (royalty ~35%)
- Bundle Etsy US Letter + A4: €10–12

**IT — Automazione con AI:**
- Generazione disegni: Midjourney (stile line art, no fill, white background), Stable Diffusion
- Post-processing: conversione in B&W puro, rimozione grigi medi, upscaling a 300 DPI
- Cover: Canva + immagine AI + font serif elegante
- Descrizioni listing: Claude/GPT con keyword research Etsy integrata

---

**EN — Technical specs:** 300 DPI PDF interior (US Letter or A4), white paper, blank page after every art page, cover PDF full wrap with 0.125" bleed, Etsy max 20 MB.

**EN — Top 2025 niches:** Italy/travel/landmarks, botanical vintage, mindfulness/mandala, dark academia, cottagecore, architecture line art.

**EN — Pricing:** Etsy digital €3–8 single / €8–15 bundle; KDP print €12–25.

**EN — AI automation:** Midjourney line art → B&W post-processing → 300 DPI upscale → Canva cover → Claude listing copy.

---

### 2. Clipart SVG

**IT — Specifiche tecniche:**
- Formato principale: SVG vettoriale (scalabile infinitamente)
- Formato alternativo: PNG 300 DPI, sfondo trasparente, min 3000×3000 px per elemento singolo
- Consegna: ZIP con SVG + PNG (conta come 1 file su Etsy)
- Etsy: max 20 MB per file (5 file per listing) — per bundle grandi usare un unico ZIP
- Spazio colore: sRGB, no profili CMYK incorporati

**IT — Nicchie top 2025:**
- Italiana/mediterranea (limoni, ceramiche, architettura)
- Botanical vintage e illustrazione scientifica
- Halloween/witchy/dark floral
- Wedding/boho/eucalipto
- Elementi per digital planner (icone, sticker, washi tape)
- Sport e hobby specifici (ciclismo, cucina, gatto)

**IT — Pricing strategy:**
- Elemento singolo: €2–4
- Pack 10–20 elementi: €5–12
- Mega bundle 50+: €15–30
- Licenza commerciale (uso su prodotti in vendita): +50–100%

**IT — Automazione con AI:**
- Generazione: Midjourney con stile coerente su un unico prompt-template
- Vettorizzazione: Adobe Illustrator Live Trace, Vectorizer.ai, Inkscape auto-trace
- Rimozione sfondo: Remove.bg, Canva BG Remover
- Batch export: Illustrator scripting o Inkscape CLI

---

**EN — Technical specs:** SVG + transparent-background PNG (min 3000×3000 px, 300 DPI), delivered as ZIP. Etsy max 20 MB per file.

**EN — Top 2025 niches:** Italian/Mediterranean, botanical vintage, Halloween/witchy, wedding/boho, digital planner elements, niche hobbies.

**EN — Pricing:** Single €2–4 / pack €5–12 / mega bundle €15–30 / commercial license +50%.

**EN — AI automation:** Midjourney consistent style → Vectorizer.ai → batch export SVG+PNG → ZIP delivery.

---

### 3. Wall Art (Stampe Decorative)

**IT — Specifiche tecniche:**
- Formato: PDF o JPG/PNG alta risoluzione
- DPI: 300 minimo; 350–600 per stampe large format (poster 18"×24"+)
- Dimensioni standard da includere in bundle: 5×7", 8×10", 11×14", A4, A3, 18×24"
- Spazio colore: sRGB per Etsy digitale
- Consegna: ZIP con tutti i formati (conta come 1 file Etsy)
- Etsy: max 20 MB per ZIP — comprimere PNG con tinypng.com se necessario

**IT — Nicchie top 2025:**
- Citazioni motivazionali bilingue italiano/inglese
- Botanical prints in stile vintage/erbario
- Astronomia, costellazioni, mappe stellari
- Minimalismo scandinavo (line art di città)
- Architecture line art italiana (skyline di Roma, Venezia, Firenze)
- Nursery/cameretta bambini con illustrazioni morbide

**IT — Pricing strategy:**
- Print singola: €2–6
- Set coordinato 3–5 stampe: €6–15
- Bundle multiformat (tutti i formati in un ZIP): €8–20
- Collezione tematica 10+: €15–30

**IT — Automazione con AI:**
- Design base: Midjourney + upscaling con Magnific o Topaz
- Testo e layout: Canva con font pairing automatizzato
- Resize batch: Python (Pillow) o Photoshop Actions per generare tutti i formati
- Mockup automatici: Placeit API, Creative Fabrica

---

**EN — Technical specs:** 300+ DPI PDF/JPG/PNG, sRGB, standard sizes (5×7" to 18×24"), delivered as ZIP under 20 MB.

**EN — Top 2025 niches:** Bilingual motivational quotes, botanical vintage, astronomy/star maps, Scandinavian minimalism, Italian architecture line art, nursery prints.

**EN — Pricing:** Single €2–6 / set €6–15 / multi-format bundle €8–20.

**EN — AI automation:** Midjourney → Topaz upscaling → Python batch resize all formats → ZIP delivery.

---

### 4. Template Canva

**IT — Specifiche tecniche:**
- Formato consegnato: PDF preview (A4 o dimensione originale) + file TXT/PDF con link al template Canva condivisibile
- Etsy non supporta link diretti come file scaricabile: il link va incorporato in un PDF di istruzioni
- Il template Canva deve essere impostato come "usa template" (non modifica il file originale)
- Dimensioni per tipo: social 1080×1080 px, Story 1080×1920 px, A4 per stampa, Presentation 1920×1080 px
- Font: usare solo font gratuiti di Canva o caricare font free-license per evitare problemi legali

**IT — Nicchie top 2025:**
- Social media kit per piccole imprese e artigiani italiani
- Wedding invitation e stationery (inviti, menu, segnaposto)
- Digital planner 2025–2026 (GoodNotes, Notability)
- Presentation template per freelance e coach
- Resume/CV moderno bilingue

**IT — Pricing strategy:**
- Template singolo: €3–8
- Pack 5–10 template coordinati: €10–25
- Brand kit completo (logo placeholder + 20 template): €30–60
- Social media bundle mensile: €8–15

**IT — Automazione con AI:**
- Generazione varianti colore: Canva Brand Kit + sostituzione palette
- Copy e testo di esempio: Claude/GPT per placeholder realistici
- Preview mockup: screenshot Canva + mockup dispositivo su Placeit
- Traduzione IT/EN automatica dei testi nei template

---

**EN — Technical specs:** Deliver as PDF preview + PDF/TXT with Canva template link. Template must be set to "use template" mode. Use only free Canva fonts.

**EN — Top 2025 niches:** Italian small business social kits, wedding stationery, digital planners, freelance presentations, bilingual CVs.

**EN — Pricing:** Single €3–8 / pack €10–25 / brand kit €30–60.

**EN — AI automation:** Canva Brand Kit color variants → Claude copy → Placeit mockups.

---

### 5. Puzzle Books KDP

**IT — Specifiche tecniche:**
- Interior: PDF, 300 DPI, bianco/nero (massimizza royalty KDP)
- Trim size consigliati: 6"×9" (tascabile), 8"×10", 8,5"×11" (large print)
- Carta: white (non cream) per B&W
- Pagine minime: 24 — massime: 828
- Ogni sezione puzzle deve avere la soluzione (in appendice o pagina seguente)
- Cover: PDF full wrap, 300 DPI, bleed 0,125"
- Max file interior KDP: 650 MB

**IT — Nicchie top 2025:**
- Word search a tema italiano (cibo, città, storia, calcio)
- Sudoku brandizzato (copertina tematica, difficoltà graduata)
- Crossword puzzle bilingue italiano/inglese
- Libri di attività per anziani (large print, caratteri grandi)
- Mazes/labirinti tematici (architettura, natura)
- Crypto puzzles e logic puzzles per adulti

**IT — Pricing strategy:**
- KDP fisico: €8–18 (royalty ~35% sul prezzo di listino)
- Etsy PDF digitale: €3–7
- Large print edition (anziani): premium +20–30%
- Bundle KDP serie (es. Vol. 1 + Vol. 2): incrementa visibilità organica

**IT — Automazione con AI:**
- Word search: Python (`word-search` library) con lista parole generata da Claude
- Sudoku: generatori open source con livelli di difficoltà (easy/medium/hard/expert)
- Crossword: `crossword` Python library o Crossword Labs export
- Layout e impaginazione: Python `reportlab` o `WeasyPrint` per PDF automatico
- Copertina: Midjourney + Canva template + KDP cover calculator per dimensioni dorso

---

**EN — Technical specs:** B&W PDF interior, 300 DPI, white paper, 6×9"/8×10"/8.5×11" trim, 24–828 pages, solution section required, cover full wrap PDF with 0.125" bleed.

**EN — Top 2025 niches:** Italian-themed word search, branded sudoku, bilingual crossword, large-print for seniors, themed mazes, logic/crypto puzzles.

**EN — Pricing:** KDP print €8–18 / Etsy digital €3–7 / large print +20–30% premium.

**EN — AI automation:** Claude word lists → Python puzzle generators → reportlab PDF layout → Midjourney cover → KDP cover calculator.

---

## Comportamenti automatici / Automatic behaviors

**IT** — Regole che Claude Code deve seguire sempre in questo progetto:

1. **Nuovo prodotto** — Ogni volta che si inizia a lavorare su un nuovo prodotto digitale, chiedere sempre: *categoria* (coloring book, clipart, planner…), *nicchia target* (es. italiani all'estero, amanti del viaggio, adulti stress-relief), *piattaforma* (Etsy, KDP, o entrambe).

2. **Verifica tecnica preventiva** — Prima di generare qualsiasi file, verificare sempre che rispetti i limiti tecnici della piattaforma di destinazione (DPI, peso, margini, bleed, trim size) come documentato nella sezione "Specifiche tecniche Etsy e KDP".

3. **Suggerimenti post-prodotto** — Dopo ogni prodotto completato, suggerire sempre 3 varianti o prodotti correlati da creare (es. tema diverso, formato diverso, versione bundle).

4. **Bundle e cross-selling** — Se si individua un'opportunità di bundle (es. più coloring book insieme) o cross-selling (es. clipart abbinata al coloring book), segnalarla sempre esplicitamente.

5. **Pricing** — Proporre sempre un pricing di riferimento basato sulla categoria e sulla piattaforma, con range basso/medio/alto.

---

**EN** — Rules Claude Code must always follow in this project:

1. **New product** — Whenever starting work on a new digital product, always ask: *category* (coloring book, clipart, planner…), *target niche* (e.g. Italians abroad, travel lovers, adult stress-relief), *platform* (Etsy, KDP, or both).

2. **Pre-generation technical check** — Before generating any file, always verify it meets the platform's technical requirements (DPI, file size, margins, bleed, trim size) as documented in the "Specifiche tecniche Etsy e KDP" section.

3. **Post-product suggestions** — After every completed product, always suggest 3 variants or related products to create (e.g. different theme, different format, bundle version).

4. **Bundle and cross-selling** — If a bundle opportunity (e.g. multiple coloring books together) or cross-selling opportunity (e.g. matching clipart) is spotted, always flag it explicitly.

5. **Pricing** — Always suggest a reference pricing based on category and platform, with low/mid/high range.

---

## Specifiche tecniche Etsy e KDP

### Etsy — file digitali

| Parametro | Valore |
|-----------|--------|
| File massimi per listing | 5 |
| Peso massimo per file | **20 MB** |
| Formati accettati | PDF, PNG, JPG, ZIP, SVG, e altri |
| Formato consigliato coloring book | PDF (US Letter o A4) |
| DPI consigliato | 300 DPI minimo |

**Regole Etsy da non violare mai:**
- Nessun file può superare i **20 MB** — lo ZIP Etsy deve stare sotto questo limite.
- Il PDF non deve contenere link esterni, JavaScript o contenuti interattivi.
- Il file deve essere scaricabile immediatamente dopo l'acquisto: non usare link a servizi terzi come file consegnabile.

---

### Etsy — immagini listing e mockup

| Parametro | Valore |
|-----------|--------|
| Numero massimo foto per listing | 10 |
| Peso massimo per foto | 10 MB |
| Formati accettati | JPG, PNG |
| Dimensione minima consigliata | 2000 px sul lato corto |
| Dimensione ottimale | 2000 × 2000 px (quadrata) o 2700 × 2025 px (4:3) |
| Spazio colore | sRGB |

**Note mockup:**
- Le prime 1–3 foto determinano il CTR: usare mockup realistici (libro su tavolo, mano che colora).
- Etsy mostra le anteprime in formato quadrato 170 × 135 px nelle ricerche: il soggetto principale deve essere centrato.
- Non includere testo fuorviante o loghi di terze parti nelle immagini.

---

### KDP — interni (interior PDF)

| Parametro | Valore |
|-----------|--------|
| Formato pagina US Letter | 8,5" × 11" → **2550 × 3300 px** a 300 DPI ✓ |
| Formato pagina A4 | 8,27" × 11,69" → **2480 × 3508 px** a 300 DPI ✓ |
| DPI minimo | **300 DPI** |
| Spazio colore | RGB (per interni a colori) |
| Carta consigliata coloring book | White (bianca), non Cream |
| Pagine minime | 24 |
| Pagine massime | 828 |
| Peso massimo PDF interni | 650 MB |
| Bleed interni | Non richiesto (pagine coloring non usano bleed) |

**Margini minimi KDP interni** (distanza dal bordo taglio al contenuto):

| Numero di pagine | Margine interno (gutter) | Margine esterno | Alto/Basso |
|------------------|--------------------------|-----------------|------------|
| 24 – 150 | 0,375" (28 px a 300 DPI) | 0,25" (19 px) | 0,25" (19 px) |
| 151 – 300 | 0,500" (38 px) | 0,25" (19 px) | 0,25" (19 px) |
| 301 – 500 | 0,625" (47 px) | 0,25" (19 px) | 0,25" (19 px) |
| 501 – 700 | 0,750" (56 px) | 0,25" (19 px) | 0,25" (19 px) |

> I coloring book sotto i 60 disegni rientrano quasi sempre nella fascia 24–150 pagine (ricorda: ogni disegno genera 2 pagine — art + blank).

**Regole KDP interni da non violare mai:**
- Ogni pagina d'arte deve essere seguita da una **pagina bianca** (già implementato): evita che l'inchiostro traspaia sul retro.
- Le immagini non devono sforare nell'area dei margini: il contenuto deve restare nel "safe area".
- Il PDF deve avere dimensioni di pagina esatte al trim size — niente bleed sugli interni.
- Non incorporare font se il PDF è solo immagini raster (già il caso con img2pdf).

---

### KDP — copertina (cover PDF)

| Parametro | Valore |
|-----------|--------|
| DPI minimo | **300 DPI** |
| Bleed richiesto | **0,125"** (3,175 mm) su tutti e 4 i lati |
| Formato consegnato a KDP | PDF unico che include: retro + dorso + fronte + bleed |
| Ratio fronte copertina (US Letter) | 8,5" × 11" → rapporto **17:22** (circa 0,773:1, formato portrait) |
| Ratio fronte copertina (A4) | 8,27" × 11,69" → rapporto **1:1,414** (√2, formato portrait) |
| Larghezza dorso | dipende dal numero di pagine × spessore carta |

**Formula dorso KDP (carta bianca 60#):**
```
spessore_dorso_pollici = numero_pagine × 0,002252"
```
Esempio per 52 pagine: 52 × 0,002252" = **0,117"** di dorso

**Dimensioni cover completa (US Letter, 52 pagine):**
```
larghezza = 0,125" + 8,5" + 0,117" + 8,5" + 0,125" = 17,367"  →  5210 px a 300 DPI
altezza   = 0,125" + 11" + 0,125"                   = 11,25"   →  3375 px a 300 DPI
```

**Regole KDP cover da non violare mai:**
- Il titolo e gli elementi principali devono stare almeno **0,25"** (75 px a 300 DPI) dentro il bordo di taglio — la "safe zone".
- Il codice a barre KDP occupa l'angolo in basso a destra del retro: lasciare un'area libera di almeno **2" × 1,2"** (600 × 360 px).
- Il colore di sfondo deve estendersi fino al bleed — mai lasciare bordi bianchi.
- Non inserire elementi importanti sul dorso se è più stretto di **0,25"**: KDP può non garantire la stampa precisa.

---

### Regole assolute che non si possono mai violare

1. **Etsy:** nessun file digitale sopra 20 MB — controllare sempre prima del caricamento.
2. **KDP interni:** DPI mai sotto 300 — immagini sotto soglia vengono rifiutate o stampate sfocate.
3. **KDP interni:** pagine sempre al trim size esatto — niente bleed, niente dimensioni approssimate.
4. **KDP cover:** bleed di 0,125" obbligatorio su tutti i lati — senza bleed il file viene rifiutato.
5. **KDP cover:** safe zone di 0,25" rispettata per titolo e autore — elementi fuori safe zone vengono tagliati in stampa.
6. **Entrambe le piattaforme:** spazio colore RGB — CMYK può causare colori errati o rifiuto del file.
7. **KDP coloring book:** pagina bianca dopo ogni pagina d'arte — senza di essa l'inchiostro traspare sul retro (bleed-through).

---

## Cos'è questo servizio

Una Flask REST API a file singolo che normalizza immagini di coloring book e le assembla in PDF pronti per la stampa. L'intera applicazione è `app.py`. Gira come container Docker ed è invocata da n8n in risposta a comandi del bot Telegram.

## Comandi

```bash
# Build e avvio
docker compose up -d --build

# Riavvio dopo aver modificato app.py (l'unico file che cambia)
docker compose up -d --build

# Log in tempo reale
docker compose logs -f

# Esecuzione locale (fuori Docker) per iterazioni rapide
pip install -r requirements.txt
JOBS_ROOT=/srv/coloringitaly/jobs WORKER_AUTH_TOKEN=... python app.py
```

## Variabili d'ambiente (`.env`)

| Variabile | Default | Scopo |
|-----------|---------|-------|
| `WORKER_AUTH_TOKEN` | `CHANGE_ME` | Token di autenticazione per tutti gli endpoint protetti |
| `JOBS_ROOT` | `/srv/coloringitaly/jobs` | Cartella radice dove vengono creati i job |
| `CALLBACK_TIMEOUT` | `20` | Secondi prima del timeout della POST di callback |
| `TMP_RETENTION_DAYS` | `14` | `/cleanup` rimuove i job più vecchi di questo valore |

## Architettura

```
n8n (workflow) ──HTTP──▶ Flask app (app.py, porta 8000)
                              │
                              ▼
                    /srv/coloringitaly/jobs/<job_id>/
                      input/raw/          ← immagini caricate dall'utente
                      input/normalized/   ← scritto da /importa
                      output/             ← scritto da /confeziona
                      tmp/<variant>/      ← frame intermedi di rendering
                      manifest.json
                      status.json
                      logs/worker.log
```

Tutto l'I/O dei job è basato su filesystem. Il container monta `/srv/coloringitaly` come volume.

## Endpoint API

Tutti eccetto `/health` richiedono l'header `X-Auth-Token: <WORKER_AUTH_TOKEN>`.

- `GET /health` — liveness check, senza autenticazione
- `GET /status[?job_id=<id>]` — legge `status.json` di un job o lista tutti i job
- `POST /importa` — scansiona `input/raw/`, normalizza in `input/normalized/`, scrive `manifest.json`
- `POST /confeziona` — genera 4 PDF + 1 ZIP da `input/normalized/`, scrive in `output/`
- `POST /cleanup` — elimina i job in stato `done`/`error` più vecchi di `older_than_days`

Body della richiesta (JSON): `{ "job_id": "...", "chat_id": "...", "callback_url": "...", "book_title": "..." }`

Al termine, `/importa` e `/confeziona` fanno una POST al `callback_url` con il payload del risultato.

## Macchina a stati dei job

```
importing → validated       (cover.png presente)
          → cover_missing   (nessuna cover.png)

packaging → done
          → error
```

## Formati di output PDF

| Variante | Canvas (px, 300 DPI) | Struttura |
|----------|----------------------|-----------|
| `etsy_us_letter` | 2550 × 3300 | cover + pagine |
| `etsy_a4` | 2480 × 3508 | cover + pagine |
| `kdp_us_letter` | 2550 × 3300 | cover + art/blank intercalate |
| `kdp_a4` | 2480 × 3508 | cover + art/blank intercalate |

Le varianti KDP inseriscono una pagina bianca dopo ogni pagina d'arte (necessario per la stampa fisica POD per evitare trasparenza). Lo ZIP Etsy raggruppa i due PDF Etsy.

Tutte le immagini sorgente vengono adattate con `ImageOps.contain` su un canvas RGB bianco (letterboxed, mai ritagliate né stirate).

## Funzioni principali di app.py

| Funzione | Righe | Scopo |
|----------|-------|-------|
| `copy_and_normalize_pages` | ~119 | Rinomina i file raw in `page_NN.png`, copia la cover |
| `fit_image_to_canvas` | ~156 | Letterbox di un'immagine su canvas bianco alla dimensione target |
| `build_render_sequence` | ~173 | Assembla la lista ordinata di PNG per una data variante |
| `generate_pdf_from_sequence` | ~217 | Converte la lista di PNG in PDF tramite `img2pdf` |
| `update_status` | ~69 | Lettura-modifica-scrittura atomica di `status.json` |

## Dipendenze

- `Flask` — server HTTP
- `Pillow` — ridimensionamento immagini e composizione del canvas
- `img2pdf` — conversione PNG→PDF lossless (preserva i metadati DPI)
- `gunicorn` — server WSGI per produzione (2 worker, timeout 600 s)
- `ghostscript` — installato nell'immagine Docker, usato indirettamente da img2pdf per alcuni formati
