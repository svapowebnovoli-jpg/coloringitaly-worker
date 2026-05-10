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
