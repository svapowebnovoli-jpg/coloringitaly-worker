# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Contesto strategico

Il progetto produce **coloring book per adulti a tema italiano** venduti sul negozio Etsy **BagarreBazaar**, sezione **Ink & Roads**.

**Obiettivo:** automatizzare al 90% la pipeline di produzione — dall'immagine grezza al file pronto per Etsy/KDP — riducendo al minimo l'intervento manuale.

**Prossimi step pianificati:**
- Endpoint `/genera_cover` — generazione automatica della copertina
- Pipeline clipart — gestione e assemblaggio di elementi grafici riutilizzabili

## Cos'è questo servizio

A single-file Flask REST API that normalizes coloring-book images and assembles them into print-ready PDFs. The entire application is `app.py`. It runs as a Docker container and is called by n8n in response to Telegram bot commands.

## Commands

```bash
# Build and start
docker compose up -d --build

# Restart after editing app.py (the only file that changes)
docker compose up -d --build

# Live logs
docker compose logs -f

# Run locally (outside Docker) for quick iteration
pip install -r requirements.txt
JOBS_ROOT=/srv/coloringitaly/jobs WORKER_AUTH_TOKEN=... python app.py
```

## Environment variables (`.env`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `WORKER_AUTH_TOKEN` | `CHANGE_ME` | Bearer token for all authenticated endpoints |
| `JOBS_ROOT` | `/srv/coloringitaly/jobs` | Root folder where job directories are created |
| `CALLBACK_TIMEOUT` | `20` | Seconds before callback POST times out |
| `TMP_RETENTION_DAYS` | `14` | `/cleanup` removes jobs older than this |

## Architecture

```
n8n (workflow) ──HTTP──▶ Flask app (app.py, port 8000)
                              │
                              ▼
                    /srv/coloringitaly/jobs/<job_id>/
                      input/raw/          ← user uploads here
                      input/normalized/   ← written by /importa
                      output/             ← written by /confeziona
                      tmp/<variant>/      ← intermediate render frames
                      manifest.json
                      status.json
                      logs/worker.log
```

All job I/O is filesystem-based. The container mounts `/srv/coloringitaly` as a volume.

## API endpoints

All except `/health` require header `X-Auth-Token: <WORKER_AUTH_TOKEN>`.

- `GET /health` — liveness, no auth
- `GET /status[?job_id=<id>]` — read `status.json` for one job or list all
- `POST /importa` — scans `input/raw/`, normalizes to `input/normalized/`, writes `manifest.json`
- `POST /confeziona` — builds 4 PDFs + 1 ZIP from `input/normalized/`, writes to `output/`
- `POST /cleanup` — deletes jobs in `done`/`error` state older than `older_than_days`

Request body (JSON): `{ "job_id": "...", "chat_id": "...", "callback_url": "...", "book_title": "..." }`

On completion, `/importa` and `/confeziona` POST the `callback_url` with the result payload.

## Job state machine

```
importing → validated       (cover.png present)
          → cover_missing   (no cover.png)

packaging → done
          → error
```

## PDF output formats

| Variant | Canvas (px, 300 DPI) | Structure |
|---------|----------------------|-----------|
| `etsy_us_letter` | 2550 × 3300 | cover + pages |
| `etsy_a4` | 2480 × 3508 | cover + pages |
| `kdp_us_letter` | 2550 × 3300 | cover + art/blank interleaved |
| `kdp_a4` | 2480 × 3508 | cover + art/blank interleaved |

KDP variants insert a blank white page after every art page (required for physical POD to prevent bleed-through). The Etsy ZIP bundles the two Etsy PDFs.

All source images are fitted with `ImageOps.contain` onto a white RGB canvas (letterboxed, never cropped or stretched).

## Key functions in app.py

| Function | Lines | Purpose |
|----------|-------|---------|
| `copy_and_normalize_pages` | ~119 | Renames raw files to `page_NN.png`, copies cover |
| `fit_image_to_canvas` | ~156 | Letterboxes one image onto a white canvas at target size |
| `build_render_sequence` | ~173 | Assembles the ordered list of PNGs for a given variant |
| `generate_pdf_from_sequence` | ~217 | Converts PNG list → PDF via `img2pdf` |
| `update_status` | ~69 | Atomic read-modify-write of `status.json` |

## Dependencies

- `Flask` — HTTP server
- `Pillow` — image resizing and canvas composition
- `img2pdf` — lossless PNG-to-PDF conversion (preserves DPI metadata)
- `gunicorn` — production WSGI server (2 workers, 600 s timeout)
- `ghostscript` — installed in Docker image, used indirectly by img2pdf for some formats
