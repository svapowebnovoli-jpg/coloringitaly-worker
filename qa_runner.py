#!/usr/bin/env python3
"""
QA Runner — Valida output visivi (PDF, ZIP) di un job completato
Uso: python qa_runner.py --job_id italy_pasta_001
Output: qa_report_{job_id}.md + campo qa_status in status.json
"""

import argparse
import json
import os
import zipfile
from pathlib import Path
from datetime import datetime
from PyPDF2 import PdfReader

# Costanti (copiato da app.py)
JOBS_ROOT = Path(os.getenv("JOBS_ROOT", "/srv/coloringitaly/jobs"))
US_LETTER_PT = (612, 792)   # PDF points (8.5" × 11")
A4_PT = (595, 842)          # PDF points (210mm × 297mm)
PT_TOLERANCE = 2            # ±2pt tolerance

def status_path(job_id: str) -> Path:
    return JOBS_ROOT / job_id / "status.json"

def manifest_path(job_id: str) -> Path:
    return JOBS_ROOT / job_id / "manifest.json"

def output_dir(job_id: str) -> Path:
    return JOBS_ROOT / job_id / "output"

def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text())
    except:
        return default or {}

def save_json(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2))

# ============================================================================
# QA CHECK FUNCTIONS
# ============================================================================

def check_qa_001_output_files_present(job_id: str) -> dict:
    """QA-001: Tutti 5 file output presenti (4 PDF + ZIP)"""
    out_dir = output_dir(job_id)
    expected_files = [
        f"{job_id}_etsy_us_letter.pdf",
        f"{job_id}_etsy_a4.pdf",
        f"{job_id}_kdp_us_letter.pdf",
        f"{job_id}_kdp_a4.pdf",
        f"{job_id}_etsy.zip",
    ]

    missing = []
    for f in expected_files:
        if not (out_dir / f).exists():
            missing.append(f)

    if missing:
        return {
            "status": "fail",
            "detail": f"Missing files: {', '.join(missing)}"
        }
    return {
        "status": "pass",
        "detail": "All 5 output files present"
    }

def check_qa_002_naming_convention(job_id: str) -> dict:
    """QA-002: Naming convention: {job_id}_*.pdf e {job_id}_etsy.zip"""
    out_dir = output_dir(job_id)
    if not out_dir.exists():
        return {"status": "fail", "detail": "Output directory does not exist"}

    files = list(out_dir.glob(f"{job_id}_*.pdf")) + list(out_dir.glob(f"{job_id}_*.zip"))
    expected_count = 5

    if len(files) != expected_count:
        return {
            "status": "fail",
            "detail": f"Found {len(files)} files matching pattern, expected {expected_count}"
        }

    # Verify naming pattern exactly
    expected_names = {
        f"{job_id}_etsy_us_letter.pdf",
        f"{job_id}_etsy_a4.pdf",
        f"{job_id}_kdp_us_letter.pdf",
        f"{job_id}_kdp_a4.pdf",
        f"{job_id}_etsy.zip",
    }
    actual_names = {f.name for f in files}

    if actual_names != expected_names:
        return {
            "status": "fail",
            "detail": f"File names mismatch. Expected {expected_names}, got {actual_names}"
        }

    return {"status": "pass", "detail": "Naming convention correct"}

def check_qa_003_file_sizes(job_id: str) -> dict:
    """QA-003: File non vuoti (PDF > 10KB, ZIP > 1KB)"""
    out_dir = output_dir(job_id)

    pdf_files = list(out_dir.glob(f"{job_id}_*.pdf"))
    zip_files = list(out_dir.glob(f"{job_id}_*.zip"))

    min_pdf_size = 10 * 1024  # 10 KB
    min_zip_size = 1 * 1024   # 1 KB

    errors = []
    for pdf in pdf_files:
        size = pdf.stat().st_size
        if size < min_pdf_size:
            errors.append(f"{pdf.name}: {size} bytes (< {min_pdf_size})")

    for zf in zip_files:
        size = zf.stat().st_size
        if size < min_zip_size:
            errors.append(f"{zf.name}: {size} bytes (< {min_zip_size})")

    if errors:
        return {"status": "fail", "detail": "Files too small: " + "; ".join(errors)}

    return {"status": "pass", "detail": "All file sizes adequate"}

def check_qa_004_pdf_metadata(job_id: str) -> dict:
    """QA-004: Metadati PDF: /Title non vuoto, /Author = "Ink & Roads" """
    out_dir = output_dir(job_id)

    # Check first PDF (etsy_us_letter)
    pdf_path = out_dir / f"{job_id}_etsy_us_letter.pdf"
    if not pdf_path.exists():
        return {"status": "fail", "detail": "PDF file does not exist"}

    try:
        reader = PdfReader(pdf_path)
        metadata = reader.metadata

        if not metadata:
            return {"status": "fail", "detail": "No PDF metadata found"}

        title = metadata.get("/Title", "")
        author = metadata.get("/Author", "")
        creator = metadata.get("/Creator", "")

        errors = []
        if not title:
            errors.append("Missing /Title")
        if author != "Ink & Roads":
            errors.append(f"/Author mismatch (expected 'Ink & Roads', got '{author}')")
        if not creator:
            errors.append("Missing /Creator")

        if errors:
            return {"status": "fail", "detail": "; ".join(errors)}

        return {
            "status": "pass",
            "detail": f"/Title='{title}', /Author='Ink & Roads', /Creator='{creator}'"
        }

    except Exception as e:
        return {"status": "fail", "detail": f"Cannot read PDF metadata: {e}"}

def check_qa_005_page_count_etsy(job_id: str) -> dict:
    """QA-005: Conteggio pagine Etsy = pages_found + 1 (cover) + 1 (instructions se esiste)"""
    out_dir = output_dir(job_id)
    status = load_json(status_path(job_id))
    normalized_dir = JOBS_ROOT / job_id / "input" / "normalized"

    pages_found = status.get("pages_found", 0)
    has_instructions = (normalized_dir / "instructions.png").exists()
    expected_etsy_pages = pages_found + 1 + (1 if has_instructions else 0)  # cover + optional instructions

    # Check etsy_us_letter PDF
    pdf_path = out_dir / f"{job_id}_etsy_us_letter.pdf"
    if not pdf_path.exists():
        return {"status": "fail", "detail": "PDF file does not exist"}

    try:
        reader = PdfReader(pdf_path)
        actual_pages = len(reader.pages)

        if actual_pages != expected_etsy_pages:
            return {
                "status": "fail",
                "detail": f"Page count mismatch: expected {expected_etsy_pages}, got {actual_pages}"
            }

        instruction_note = " + instructions" if has_instructions else ""
        return {
            "status": "pass",
            "detail": f"Etsy PDF: {actual_pages} pages (pages_found={pages_found} + cover{instruction_note})"
        }

    except Exception as e:
        return {"status": "fail", "detail": f"Cannot read PDF: {e}"}

def check_qa_006_page_count_kdp(job_id: str) -> dict:
    """QA-006: Conteggio pagine KDP = 2 * pages_found + 1 (cover) + 1 (instructions se esiste)"""
    out_dir = output_dir(job_id)
    status = load_json(status_path(job_id))
    normalized_dir = JOBS_ROOT / job_id / "input" / "normalized"

    pages_found = status.get("pages_found", 0)
    has_instructions = (normalized_dir / "instructions.png").exists()
    # KDP: cover + optional instructions + (art + blank) × pages_found
    expected_kdp_pages = 1 + (1 if has_instructions else 0) + 2 * pages_found

    # Check kdp_us_letter PDF
    pdf_path = out_dir / f"{job_id}_kdp_us_letter.pdf"
    if not pdf_path.exists():
        return {"status": "fail", "detail": "PDF file does not exist"}

    try:
        reader = PdfReader(pdf_path)
        actual_pages = len(reader.pages)

        if actual_pages != expected_kdp_pages:
            return {
                "status": "fail",
                "detail": f"Page count mismatch: expected {expected_kdp_pages}, got {actual_pages}"
            }

        instruction_note = " + instructions" if has_instructions else ""
        return {
            "status": "pass",
            "detail": f"KDP PDF: {actual_pages} pages (cover{instruction_note} + art/blank alternating)"
        }

    except Exception as e:
        return {"status": "fail", "detail": f"Cannot read PDF: {e}"}

def check_qa_007_canvas_dimensions(job_id: str) -> dict:
    """QA-007: Dimensioni canvas: etsy_us_letter (612×792pt), etsy_a4 (595×842pt)"""
    out_dir = output_dir(job_id)

    checks = [
        (f"{job_id}_etsy_us_letter.pdf", US_LETTER_PT),
        (f"{job_id}_etsy_a4.pdf", A4_PT),
        (f"{job_id}_kdp_us_letter.pdf", US_LETTER_PT),
        (f"{job_id}_kdp_a4.pdf", A4_PT),
    ]

    errors = []
    for filename, expected_size in checks:
        pdf_path = out_dir / filename
        if not pdf_path.exists():
            errors.append(f"{filename}: not found")
            continue

        try:
            reader = PdfReader(pdf_path)
            if len(reader.pages) == 0:
                errors.append(f"{filename}: no pages")
                continue

            mediabox = reader.pages[0].mediabox
            w = float(mediabox.width)
            h = float(mediabox.height)
            actual_size = (w, h)

            # Check dimensions with tolerance
            w_expected, h_expected = expected_size
            if abs(w - w_expected) > PT_TOLERANCE or abs(h - h_expected) > PT_TOLERANCE:
                errors.append(f"{filename}: {w:.0f}×{h:.0f}pt (expected {w_expected}×{h_expected}pt)")

        except Exception as e:
            errors.append(f"{filename}: {e}")

    if errors:
        return {"status": "fail", "detail": "; ".join(errors)}

    return {"status": "pass", "detail": "All canvas dimensions correct"}

def check_qa_008_zip_contents(job_id: str) -> dict:
    """QA-008: ZIP contiene esattamente etsy_us_letter.pdf + etsy_a4.pdf"""
    out_dir = output_dir(job_id)

    zip_path = out_dir / f"{job_id}_etsy.zip"
    if not zip_path.exists():
        return {"status": "fail", "detail": "ZIP file does not exist"}

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()

            expected_files = {
                f"{job_id}_etsy_us_letter.pdf",
                f"{job_id}_etsy_a4.pdf",
            }

            actual_files = set(files)

            if actual_files != expected_files:
                return {
                    "status": "fail",
                    "detail": f"ZIP contents mismatch. Expected {expected_files}, got {actual_files}"
                }

            return {
                "status": "pass",
                "detail": f"ZIP contains exactly 2 files: {files}"
            }

    except Exception as e:
        return {"status": "fail", "detail": f"Cannot read ZIP: {e}"}

def check_qa_009_status_fields(job_id: str) -> dict:
    """QA-009: status.json: country + theme presenti e non vuoti"""
    status = load_json(status_path(job_id))

    country = status.get("country", "")
    theme = status.get("theme", "")

    errors = []
    if not country:
        errors.append("country missing or empty")
    if not theme:
        errors.append("theme missing or empty")

    if errors:
        return {"status": "fail", "detail": "; ".join(errors)}

    return {"status": "pass", "detail": f"country='{country}', theme='{theme}'"}

def check_qa_010_manifest_coherence(job_id: str) -> dict:
    """QA-010: Manifest coerente: pages_found conta solo pagine art, non cover/instructions"""
    status = load_json(status_path(job_id))
    manifest = load_json(manifest_path(job_id))

    pages_found = status.get("pages_found", 0)
    normalized_files = status.get("normalized_files", [])
    manifest_pages = manifest.get("pages_found", 0)

    errors = []

    # normalized_files should be: cover.png + optional instructions.png + pages_found pages
    expected_normalized_count = 1 + pages_found  # cover + pages
    if "instructions.png" in normalized_files:
        expected_normalized_count += 1

    if len(normalized_files) != expected_normalized_count:
        errors.append(f"len(normalized_files)={len(normalized_files)}, expected {expected_normalized_count} (cover + {'instructions + ' if 'instructions.png' in normalized_files else ''}{pages_found} pages)")

    if pages_found != manifest_pages:
        errors.append(f"status.pages_found={pages_found} != manifest.pages_found={manifest_pages}")

    if errors:
        return {"status": "fail", "detail": "; ".join(errors)}

    return {
        "status": "pass",
        "detail": f"pages_found={pages_found}, normalized_files={len(normalized_files)} (cover + {'instructions + ' if 'instructions.png' in normalized_files else ''}{pages_found} pages)"
    }

# ============================================================================
# MAIN QA RUNNER
# ============================================================================

def run_qa(job_id: str) -> dict:
    """Esegui tutti i 10 check QA e ritorna report."""

    checks = [
        ("QA-001", check_qa_001_output_files_present),
        ("QA-002", check_qa_002_naming_convention),
        ("QA-003", check_qa_003_file_sizes),
        ("QA-004", check_qa_004_pdf_metadata),
        ("QA-005", check_qa_005_page_count_etsy),
        ("QA-006", check_qa_006_page_count_kdp),
        ("QA-007", check_qa_007_canvas_dimensions),
        ("QA-008", check_qa_008_zip_contents),
        ("QA-009", check_qa_009_status_fields),
        ("QA-010", check_qa_010_manifest_coherence),
    ]

    results = {}
    blockers = []
    warnings = []

    for check_id, check_func in checks:
        try:
            result = check_func(job_id)
            results[check_id] = result

            # Severity mapping
            if check_id in ["QA-001", "QA-002", "QA-003", "QA-004", "QA-008"]:
                severity = "BLOCKING"
            else:
                severity = "CRITICAL"

            if result["status"] == "fail":
                if severity == "BLOCKING":
                    blockers.append(f"{check_id} ({severity}): {result['detail']}")
                else:
                    warnings.append(f"{check_id} ({severity}): {result['detail']}")

        except Exception as e:
            results[check_id] = {"status": "fail", "detail": f"Exception: {e}"}
            blockers.append(f"{check_id}: Exception - {e}")

    # Determine overall status
    overall = "pass" if len(blockers) == 0 else "fail"

    qa_report = {
        "overall": overall,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": results,
        "blockers": blockers,
        "warnings": warnings,
    }

    return qa_report

def write_report(job_id: str, qa_report: dict):
    """Scrivi report markdown nella job directory."""
    job_dir = JOBS_ROOT / job_id
    report_path = job_dir / f"qa_report_{job_id}.md"

    timestamp = qa_report["timestamp"]
    overall = qa_report["overall"].upper()

    content = f"""# QA Report — {job_id}

**Timestamp:** {timestamp}
**Overall Status:** {'✅ PASS' if overall == 'PASS' else '❌ FAIL'}

---

## Check Results

| ID | Check | Status | Detail |
|---|---|---|---|
"""

    for check_id in sorted(qa_report["checks"].keys()):
        result = qa_report["checks"][check_id]
        status = "✅ PASS" if result["status"] == "pass" else "❌ FAIL"
        detail = result["detail"][:100]  # Truncate for table
        content += f"| {check_id} | {check_id} | {status} | {detail}... |\n"

    content += f"""

---

## Blockers (MUST PASS)

"""
    if qa_report["blockers"]:
        for blocker in qa_report["blockers"]:
            content += f"- ❌ {blocker}\n"
    else:
        content += "- ✅ None\n"

    content += f"""

## Warnings (CRITICAL)

"""
    if qa_report["warnings"]:
        for warning in qa_report["warnings"]:
            content += f"- ⚠️ {warning}\n"
    else:
        content += "- ✅ None\n"

    content += f"""

---

## Summary

- **Overall:** {'✅ PASS' if overall == 'PASS' else '❌ FAIL'}
- **Blockers:** {len(qa_report['blockers'])}
- **Warnings:** {len(qa_report['warnings'])}

## Next Steps

{'Ready for upload to Etsy/KDP' if overall == 'PASS' else 'Fix blockers and re-run'}
"""

    report_path.write_text(content)
    return report_path

def main():
    parser = argparse.ArgumentParser(description="QA Runner — valida output visivi job")
    parser.add_argument("--job_id", required=True, help="es. italy_pasta_001")

    args = parser.parse_args()
    job_id = args.job_id

    job_dir = JOBS_ROOT / job_id
    if not job_dir.exists():
        print(f"❌ Job directory not found: {job_dir}")
        exit(1)

    print(f"🔍 Running QA for {job_id}...")

    qa_report = run_qa(job_id)
    report_path = write_report(job_id, qa_report)

    print(f"\n{'✅' if qa_report['overall'] == 'pass' else '❌'} QA completed: {qa_report['overall'].upper()}")
    print(f"📄 Report: {report_path}")
    print(f"📊 Blockers: {len(qa_report['blockers'])}, Warnings: {len(qa_report['warnings'])}")

    if qa_report["blockers"]:
        print("\n❌ BLOCKERS:")
        for b in qa_report["blockers"]:
            print(f"  - {b}")

    if qa_report["warnings"]:
        print("\n⚠️ WARNINGS:")
        for w in qa_report["warnings"]:
            print(f"  - {w}")

    # Update status.json with qa_status
    status = load_json(status_path(job_id))
    status["qa_status"] = qa_report
    save_json(status_path(job_id), status)
    print(f"✅ status.json updated with qa_status")

if __name__ == "__main__":
    main()
