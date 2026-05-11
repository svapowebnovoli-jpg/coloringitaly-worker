import os
import re
import json
import time
import shutil
import traceback
from pathlib import Path
from functools import wraps

import requests
import img2pdf
import subprocess
import zipfile
from flask import Flask, request, jsonify
from PIL import Image, ImageOps, ImageDraw, ImageFont

app = Flask(__name__)

APP_NAME = "coloringitaly-packaging-worker"
APP_VERSION = "1.0.0"
START_TIME = time.time()
JOBS_ROOT = Path(os.getenv("JOBS_ROOT", "/srv/coloringitaly/jobs"))
AUTH_TOKEN = os.getenv("WORKER_AUTH_TOKEN", "CHANGE_ME")
CALLBACK_TIMEOUT = int(os.getenv("CALLBACK_TIMEOUT", "20"))
TMP_RETENTION_DAYS = int(os.getenv("TMP_RETENTION_DAYS", "14"))

US_LETTER = (2550, 3300)
A4 = (2480, 3508)

TEMPLATES_ROOT = Path(os.getenv("TEMPLATES_ROOT", "/srv/coloringitaly/templates"))
OVAL_X = int(os.getenv("OVAL_X", "500"))
OVAL_Y = int(os.getenv("OVAL_Y", "300"))
OVAL_W = int(os.getenv("OVAL_W", "1550"))
OVAL_H = int(os.getenv("OVAL_H", "1800"))
COVER_FONT_SIZE  = int(os.getenv("COVER_FONT_SIZE", "100"))
BRAND_FONT_SIZE  = int(os.getenv("BRAND_FONT_SIZE", "55"))
COVER_FONT_PATH  = os.getenv("COVER_FONT_PATH", str(TEMPLATES_ROOT / "fonts" / "cover-title.ttf"))


def ensure_job_dirs(job_id: str):
    base = JOBS_ROOT / job_id
    dirs = {
        "base": base,
        "raw": base / "input" / "raw",
        "normalized": base / "input" / "normalized",
        "output": base / "output",
        "mockups": base / "mockups",
        "logs": base / "logs",
        "tmp": base / "tmp",
    }
    for p in dirs.values():
        p.mkdir(parents=True, exist_ok=True)
    return dirs


def status_path(job_id: str) -> Path:
    return JOBS_ROOT / job_id / "status.json"


def manifest_path(job_id: str) -> Path:
    return JOBS_ROOT / job_id / "manifest.json"


def load_json(path: Path, default=None):
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {} if default is None else default


def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def update_status(job_id: str, **fields):
    current = load_json(status_path(job_id), default={"job_id": job_id})
    current.update(fields)
    current["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    save_json(status_path(job_id), current)
    return current


def log_event(job_id: str, message: str):
    dirs = ensure_job_dirs(job_id)
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n"
    with open(dirs["logs"] / "worker.log", "a", encoding="utf-8") as f:
        f.write(line)


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Auth-Token", "")
        if token != AUTH_TOKEN:
            return jsonify({"ok": False, "error": "unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper


def natural_key(path: Path):
    parts = re.split(r"(\d+)", path.stem.lower())
    out = []
    for p in parts:
        if p.isdigit():
            out.append(int(p))
        else:
            out.append(p)
    return out


def is_cover(path: Path) -> bool:
    return path.stem.lower() == "cover"


def list_pngs(folder: Path):
    return [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".png"]


def list_page_candidates(folder: Path):
    pngs = list_pngs(folder)
    pages = [p for p in pngs if not is_cover(p)]
    return sorted(pages, key=natural_key)


def copy_and_normalize_pages(job_id: str):
    dirs = ensure_job_dirs(job_id)
    raw = dirs["raw"]
    normalized = dirs["normalized"]

    for p in normalized.glob("*.png"):
        p.unlink(missing_ok=True)

    pages = list_page_candidates(raw)
    cover_present = False
    cover_src = raw / "cover.png"
    if cover_src.exists():
        shutil.copy2(cover_src, normalized / "cover.png")
        cover_present = True
    else:
        alt_cover = next((p for p in list_pngs(raw) if p.stem.lower() == "cover"), None)
        if alt_cover:
            shutil.copy2(alt_cover, normalized / "cover.png")
            cover_present = True

    normalized_names = []
    for idx, src in enumerate(pages, start=1):
        dst = normalized / f"page_{idx:02d}.png"
        shutil.copy2(src, dst)
        normalized_names.append(dst.name)

    manifest = {
        "job_id": job_id,
        "pages_found": len(pages),
        "cover_present": cover_present,
        "raw_files": [p.name for p in pages],
        "normalized_files": normalized_names,
    }
    save_json(manifest_path(job_id), manifest)
    return manifest


def fit_image_to_canvas(src_path: Path, size: tuple[int, int], dst_path: Path):
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src_path).convert("RGB") as im:
        bg = Image.new("RGB", size, (255, 255, 255))
        fitted = ImageOps.contain(im, size)
        x = (size[0] - fitted.size[0]) // 2
        y = (size[1] - fitted.size[1]) // 2
        bg.paste(fitted, (x, y))
        bg.save(dst_path, format="PNG", dpi=(300, 300))


def create_blank_page(size: tuple[int, int], dst_path: Path):
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    blank = Image.new("RGB", size, (255, 255, 255))
    blank.save(dst_path, format="PNG", dpi=(300, 300))


def build_render_sequence(job_id: str, variant: str, page_size: tuple[int, int]):
    dirs = ensure_job_dirs(job_id)
    normalized = dirs["normalized"]
    tmp_variant = dirs["tmp"] / variant
    if tmp_variant.exists():
        shutil.rmtree(tmp_variant)
    tmp_variant.mkdir(parents=True, exist_ok=True)

    cover = normalized / "cover.png"
    pages = sorted(normalized.glob("page_*.png"))
    if not cover.exists():
        raise FileNotFoundError("cover.png mancante")
    if not pages:
        raise FileNotFoundError("nessuna pagina normalizzata trovata")

    rendered = []

    cover_dst = tmp_variant / "000_cover.png"
    fit_image_to_canvas(cover, page_size, cover_dst)
    rendered.append(cover_dst)

    if variant.startswith("etsy"):
        for i, page in enumerate(pages, start=1):
            dst = tmp_variant / f"{i:03d}_page.png"
            fit_image_to_canvas(page, page_size, dst)
            rendered.append(dst)

    elif variant.startswith("kdp"):
        counter = 1
        for page in pages:
            art_dst = tmp_variant / f"{counter:03d}_art.png"
            fit_image_to_canvas(page, page_size, art_dst)
            rendered.append(art_dst)
            counter += 1
            blank_dst = tmp_variant / f"{counter:03d}_blank.png"
            create_blank_page(page_size, blank_dst)
            rendered.append(blank_dst)
            counter += 1
    else:
        raise ValueError(f"variant non supportata: {variant}")

    return rendered


def generate_pdf_from_sequence(sequence: list[Path], pdf_path: Path):
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with open(pdf_path, "wb") as f:
        f.write(img2pdf.convert([str(p) for p in sequence]))



def format_size(num_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024 or unit == "GB":
            return f"{num_bytes:.1f} {unit}" if unit != "B" else f"{num_bytes} B"
        num_bytes /= 1024


def callback(callback_url: str | None, payload: dict):
    if not callback_url:
        return
    try:
        requests.post(callback_url, json=payload, timeout=CALLBACK_TIMEOUT)
    except Exception:
        pass


def generate_cover(template_path: Path, artwork_path: Path, book_title: str, brand_name: str = "Ink & Roads") -> Image.Image:
    template = Image.open(template_path).convert("RGBA")
    canvas_w, canvas_h = template.size
    oval_box = (OVAL_X, OVAL_Y, OVAL_X + OVAL_W, OVAL_Y + OVAL_H)

    # Ellipse mask for the artwork area
    mask = Image.new("L", (canvas_w, canvas_h), 0)
    ImageDraw.Draw(mask).ellipse(oval_box, fill=255)

    # Artwork resized to fit oval bounding box (letterbox)
    with Image.open(artwork_path).convert("RGBA") as art:
        art_resized = ImageOps.contain(art, (OVAL_W, OVAL_H))

    # Place artwork centred inside the oval on a white canvas
    artwork_layer = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
    x_off = OVAL_X + (OVAL_W - art_resized.size[0]) // 2
    y_off = OVAL_Y + (OVAL_H - art_resized.size[1]) // 2
    artwork_layer.paste(art_resized, (x_off, y_off))

    # Composite: white → artwork clipped to oval → template on top
    result = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
    result.paste(artwork_layer, (0, 0), mask)
    result = Image.alpha_composite(result, template)

    # Text rendering
    draw = ImageDraw.Draw(result)
    try:
        font_title = ImageFont.truetype(COVER_FONT_PATH, COVER_FONT_SIZE)
        font_brand = ImageFont.truetype(COVER_FONT_PATH, BRAND_FONT_SIZE)
    except (IOError, OSError):
        font_title = ImageFont.load_default()
        font_brand = ImageFont.load_default()

    # Title centred below oval
    text_y = OVAL_Y + OVAL_H + 80
    title_bbox = draw.textbbox((0, 0), book_title, font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((canvas_w - title_w) // 2, text_y), book_title, fill=(0, 0, 0), font=font_title)

    # Brand name below title
    brand_y = text_y + COVER_FONT_SIZE + 20
    brand_bbox = draw.textbbox((0, 0), brand_name, font=font_brand)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text(((canvas_w - brand_w) // 2, brand_y), brand_name, fill=(0, 0, 0), font=font_brand)

    return result.convert("RGB")


@app.get("/health")
def health():
    JOBS_ROOT.mkdir(parents=True, exist_ok=True)
    return jsonify({
        "ok": True,
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
        "jobs_root": str(JOBS_ROOT),
        "queue_size": 0,
        "uptime_seconds": int(time.time() - START_TIME),
    })


@app.get("/status")
@require_auth
def status():
    job_id = request.args.get("job_id", "").strip()
    if job_id:
        return jsonify(load_json(status_path(job_id), default={"job_id": job_id, "status": "not_found"}))

    jobs = []
    if JOBS_ROOT.exists():
        for p in sorted(JOBS_ROOT.iterdir()):
            if p.is_dir():
                jobs.append(load_json(p / "status.json", default={"job_id": p.name, "status": "unknown"}))
    return jsonify({"count": len(jobs), "jobs": jobs})


@app.post("/importa")
@require_auth
def importa():
    body = request.get_json(force=True, silent=True) or {}
    job_id = str(body.get("job_id", "")).strip()
    callback_url = body.get("callback_url")
    chat_id = str(body.get("chat_id", "")).strip()

    if not job_id:
        return jsonify({"ok": False, "error": "job_id mancante"}), 400

    try:
        dirs = ensure_job_dirs(job_id)
        update_status(job_id, status="importing", chat_id=chat_id)
        log_event(job_id, f"/importa avviato su {dirs['raw']}")

        manifest = copy_and_normalize_pages(job_id)
        cover_present = manifest["cover_present"]
        status_value = "validated" if cover_present else "cover_missing"
        save = update_status(
            job_id,
            status=status_value,
            chat_id=chat_id,
            pages_found=manifest["pages_found"],
            cover_present=cover_present,
            normalized_files=manifest["normalized_files"],
            error="",
        )
        payload = {
            "status": status_value,
            "job_id": job_id,
            "chat_id": chat_id,
            "pages_found": manifest["pages_found"],
            "cover_present": cover_present,
            "pages_generated": manifest["pages_found"],
            "book_title": body.get("book_title", "ColoringItaly")
        }
        callback(callback_url, payload)
        return jsonify({"ok": True, **save})
    except Exception as e:
        err = update_status(job_id, status="error", error=str(e), chat_id=chat_id)
        log_event(job_id, traceback.format_exc())
        callback(callback_url, {"status": "error", "job_id": job_id, "chat_id": chat_id, "error": str(e)})
        return jsonify({"ok": False, **err}), 500


@app.post("/genera_cover")
@require_auth
def genera_cover():
    body = request.get_json(force=True, silent=True) or {}
    job_id       = str(body.get("job_id", "")).strip()
    callback_url = body.get("callback_url")
    chat_id      = str(body.get("chat_id", "")).strip()
    book_title   = str(body.get("book_title", "")).strip()

    if not job_id:
        return jsonify({"ok": False, "error": "job_id mancante"}), 400
    if not book_title:
        return jsonify({"ok": False, "error": "book_title mancante"}), 400

    try:
        dirs          = ensure_job_dirs(job_id)
        template_path = TEMPLATES_ROOT / "cover_template.png"
        artwork_path  = dirs["normalized"] / "cover.png"

        if not template_path.exists():
            raise FileNotFoundError(f"Template non trovato: {template_path}")
        if not artwork_path.exists():
            raise FileNotFoundError("cover.png non trovato in input/normalized — esegui prima /importa")

        update_status(job_id, status="cover_generating", chat_id=chat_id)
        log_event(job_id, "/genera_cover avviato")

        cover_img = generate_cover(template_path, artwork_path, book_title)
        out_path  = dirs["output"] / "cover_final.png"
        cover_img.save(out_path, format="PNG", dpi=(300, 300))

        size_str = format_size(out_path.stat().st_size)
        final = update_status(
            job_id, status="cover_ready", chat_id=chat_id,
            book_title=book_title, cover_final=out_path.name,
            cover_size=size_str, error="",
        )
        log_event(job_id, f"/genera_cover completato → {out_path.name} ({size_str})")
        callback(callback_url, {
            "status": "cover_ready", "job_id": job_id, "chat_id": chat_id,
            "book_title": book_title, "cover_file": out_path.name, "cover_size": size_str,
        })
        return jsonify({"ok": True, **final})
    except Exception as e:
        err = update_status(job_id, status="error", error=str(e), chat_id=chat_id)
        log_event(job_id, traceback.format_exc())
        callback(callback_url, {"status": "error", "job_id": job_id, "chat_id": chat_id, "error": str(e)})
        return jsonify({"ok": False, **err}), 500


@app.post("/confeziona")
@require_auth
def confeziona():
    body = request.get_json(force=True, silent=True) or {}
    job_id = str(body.get("job_id", "")).strip()
    callback_url = body.get("callback_url")
    chat_id = str(body.get("chat_id", "")).strip()
    book_title = body.get("book_title", "ColoringItaly")

    if not job_id:
        return jsonify({"ok": False, "error": "job_id mancante"}), 400

    try:
        dirs = ensure_job_dirs(job_id)
        normalized = dirs["normalized"]
        pages = sorted(normalized.glob("page_*.png"))
        cover = normalized / "cover.png"

        if not pages:
            raise FileNotFoundError("Nessuna pagina trovata in input/normalized. Esegui prima /importa.")
        if not cover.exists():
            raise FileNotFoundError("cover.png mancante. Carica la cover e rilancia /importa.")

        update_status(job_id, status="packaging", chat_id=chat_id, book_title=book_title)
        log_event(job_id, "/confeziona avviato")

        variants = {
            "etsy_us_letter": US_LETTER,
            "etsy_a4": A4,
            "kdp_us_letter": US_LETTER,
            "kdp_a4": A4,
        }
        files = {}
        for variant, page_size in variants.items():
            seq = build_render_sequence(job_id, variant, page_size)
            pdf_path = dirs["output"] / f"coloring_book_{variant}.pdf"
            generate_pdf_from_sequence(seq, pdf_path)
            files[pdf_path.name] = format_size(pdf_path.stat().st_size)

        # Crea ZIP con i 2 PDF Etsy
        zip_path = dirs["output"] / "coloring_book_etsy.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for variant in ["etsy_us_letter", "etsy_a4"]:
                pdf = dirs["output"] / f"coloring_book_{variant}.pdf"
                zf.write(pdf, pdf.name)
        files["coloring_book_etsy.zip"] = format_size(zip_path.stat().st_size)

        callback(callback_url, {
            "status": "pdf_ready",
            "job_id": job_id,
            "chat_id": chat_id,
            "book_title": book_title,
            "files": files,
        })

        final = update_status(job_id, status="done", chat_id=chat_id, book_title=book_title, outputs=files, pdf_sizes=files, error="")
        callback(callback_url, {
            "status": "done",
            "job_id": job_id,
            "chat_id": chat_id,
            "book_title": book_title,
            "pdf_sizes": files,
            "mockup_ids": {}
        })
        log_event(job_id, "/confeziona completato")
        return jsonify({"ok": True, **final})
    except Exception as e:
        err = update_status(job_id, status="error", error=str(e), chat_id=chat_id)
        log_event(job_id, traceback.format_exc())
        callback(callback_url, {"status": "error", "job_id": job_id, "chat_id": chat_id, "error": str(e)})
        return jsonify({"ok": False, **err}), 500


@app.post("/cleanup")
@require_auth
def cleanup():
    body = request.get_json(force=True, silent=True) or {}
    older_than_days = int(body.get("older_than_days", TMP_RETENTION_DAYS))
    cutoff = time.time() - older_than_days * 86400
    removed = []

    if JOBS_ROOT.exists():
        for job_dir in JOBS_ROOT.iterdir():
            if not job_dir.is_dir():
                continue
            st = load_json(job_dir / "status.json", default={})
            status_value = st.get("status")
            mtime = job_dir.stat().st_mtime
            if status_value in {"done", "error"} and mtime < cutoff:
                shutil.rmtree(job_dir, ignore_errors=True)
                removed.append(job_dir.name)

    return jsonify({"ok": True, "removed": removed, "count": len(removed)})


if __name__ == "__main__":
    JOBS_ROOT.mkdir(parents=True, exist_ok=True)
    app.run(host="0.0.0.0", port=8000)
