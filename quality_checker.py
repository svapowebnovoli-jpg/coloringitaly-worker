#!/usr/bin/env python3
"""
Quality Checker — Valida immagini PNG scaricate da Grok
Uso: python quality_checker.py --job_id italy_vintage_vehicles_001
Output: quality_report_italy_vintage_vehicles_001.md
"""

import argparse
import os
from pathlib import Path
from datetime import datetime
from PIL import Image

JOBS_ROOT = Path(os.getenv("JOBS_ROOT", "/srv/coloringitaly/jobs"))
MIN_SIZE = 1024
ASPECT_RATIO_TOLERANCE = 0.1  # 10% tolerance around 2:3
TARGET_RATIO = 2 / 3


def load_image(path):
    """Carica immagine PNG."""
    try:
        return Image.open(path)
    except Exception as e:
        return None


def check_dimensions(img):
    """Controlla dimensioni minime."""
    w, h = img.size
    if w < MIN_SIZE or h < MIN_SIZE:
        return False, f"Size {w}×{h} is too small (min {MIN_SIZE})"
    return True, f"Size {w}×{h} ✓"


def check_aspect_ratio(img):
    """Controlla aspect ratio (deve essere ~2:3 portrait)."""
    w, h = img.size
    actual_ratio = w / h

    # Portrait deve essere meno di 1 (width < height)
    if w >= h:
        return False, f"Aspect ratio {w}:{h} — not portrait (width >= height)"

    # Check if close to 2:3
    lower_bound = TARGET_RATIO - ASPECT_RATIO_TOLERANCE
    upper_bound = TARGET_RATIO + ASPECT_RATIO_TOLERANCE

    if lower_bound <= actual_ratio <= upper_bound:
        return True, f"Aspect ratio {actual_ratio:.2f} ✓ (target 2:3)"
    else:
        return False, f"Aspect ratio {actual_ratio:.2f} — expected ~0.67 (2:3)"


def check_bw_score(img):
    """Valuta quanto è 'binary black & white' l'immagine.

    Ritorna score 0-100% dove 100% = perfetto binary B&W.
    Score = percentuale di pixel che sono vicini a nero (0) o bianco (255).
    """
    gray_img = img.convert("L")  # Grayscale
    pixels = list(gray_img.getdata())

    # Pixel "nero" = 0-50, Pixel "bianco" = 205-255
    black_count = sum(1 for p in pixels if p <= 50)
    white_count = sum(1 for p in pixels if p >= 205)
    total_pixels = len(pixels)

    bw_score = ((black_count + white_count) / total_pixels) * 100

    # Valutazione
    if bw_score >= 90:
        status = "✅ EXCELLENT"
    elif bw_score >= 80:
        status = "✅ GOOD"
    elif bw_score >= 70:
        status = "⚠️ ACCEPTABLE"
    else:
        status = "❌ NEEDS REVIEW"

    return bw_score, status


def validate_file_sequence(raw_dir):
    """Controlla naming convention: cover.png + page_01.png ... page_24.png"""
    expected_files = {"cover.png"}
    for i in range(1, 25):
        expected_files.add(f"page_{i:02d}.png")

    actual_files = {f.name for f in raw_dir.glob("*.png")}
    missing = expected_files - actual_files
    extra = actual_files - expected_files

    return {
        "expected": expected_files,
        "actual": actual_files,
        "missing": missing,
        "extra": extra,
        "complete": len(missing) == 0,
    }


def generate_quality_report(job_id, results):
    """Genera report markdown."""
    timestamp = datetime.utcnow().isoformat() + "Z"

    report = f"""# Quality Report — {job_id}

**Date:** {timestamp}
**Total Images Checked:** {len(results['images'])}

---

## Image Analysis

| File | Size | Ratio | BW Score | Dimensions | Aspect | Status | Action |
|------|------|-------|----------|------------|--------|--------|--------|
"""

    pass_count = 0
    review_count = 0
    fail_count = 0

    for result in results["images"]:
        status = result["status"]
        action = result["action"]

        # Count
        if status == "✅ PASS":
            pass_count += 1
        elif status == "⚠️ REVIEW":
            review_count += 1
        else:
            fail_count += 1

        report += f"| {result['file']} | {result['size']} | {result['ratio']} | {result['bw_score']}% | {result['dim_check']} | {result['ratio_check']} | {status} | {action} |\n"

    report += f"""

---

## Summary

- **PASS:** {pass_count}/25 ✅
- **REVIEW:** {review_count}/25 ⚠️
- **FAIL:** {fail_count}/25 ❌

"""

    if fail_count == 0 and review_count == 0:
        report += "✅ **All images pass quality check!** Ready for `/importa`\n"
    elif fail_count == 0:
        report += "⚠️ **All images PASS, but review these marked REVIEW for potential issues**\n"
    else:
        report += f"❌ **{fail_count} images FAIL quality check. Regenerate and re-check.**\n"

    report += f"""

---

## Next Steps

1. **If all PASS:**
   ```bash
   curl -X POST http://localhost:8000/importa \\
     -H "X-Auth-Token: YOUR_TOKEN" \\
     -H "Content-Type: application/json" \\
     -d '{{"job_id": "{job_id}", "book_title": "Italy Vintage Vehicles", "country": "italy", "theme": "vintage_vehicles"}}'
   ```

2. **If FAIL:** Regenerate failed images on Grok.com, re-download, re-check

3. **If REVIEW:** Manually inspect images for edge cases (aspect ratio slightly off, BW score borderline)
"""

    return report, pass_count, review_count, fail_count


def main():
    parser = argparse.ArgumentParser(
        description="Valida immagini PNG scaricate da Grok per coloring book"
    )
    parser.add_argument("--job_id", required=True, help="es. italy_vintage_vehicles_001")

    args = parser.parse_args()
    job_id = args.job_id

    # Percorsi
    job_dir = JOBS_ROOT / job_id
    raw_dir = job_dir / "input" / "raw"

    if not job_dir.exists():
        print(f"❌ Job directory not found: {job_dir}")
        print(f"📁 Create it first: mkdir -p {raw_dir}")
        exit(1)

    if not raw_dir.exists():
        print(f"❌ Raw input directory not found: {raw_dir}")
        print(f"📁 Create it first: mkdir -p {raw_dir}")
        exit(1)

    png_files = sorted(raw_dir.glob("*.png"))
    if not png_files:
        print(f"❌ No PNG files found in {raw_dir}")
        exit(1)

    print(f"🔍 Checking {len(png_files)} PNG files in {raw_dir}")

    # Valida sequenza file
    seq_check = validate_file_sequence(raw_dir)
    if not seq_check["complete"]:
        print(f"⚠️ File sequence incomplete:")
        if seq_check["missing"]:
            print(f"   Missing: {seq_check['missing']}")
        if seq_check["extra"]:
            print(f"   Extra (unexpected): {seq_check['extra']}")

    # Analizza ogni immagine
    results = {"images": []}

    for png_file in png_files:
        img = load_image(png_file)

        if img is None:
            results["images"].append({
                "file": png_file.name,
                "size": "?",
                "ratio": "?",
                "bw_score": "?",
                "dim_check": "❌ LOAD FAILED",
                "ratio_check": "?",
                "status": "❌ FAIL",
                "action": "File corrupted or unreadable — regenerate on Grok.com",
            })
            continue

        w, h = img.size
        size_str = f"{w}×{h}"

        # Check dimensioni
        dim_ok, dim_msg = check_dimensions(img)

        # Check aspect ratio
        ratio_ok, ratio_msg = check_aspect_ratio(img)

        # Check B&W
        bw_score, bw_status = check_bw_score(img)

        # Determina status
        if dim_ok and ratio_ok and bw_score >= 80:
            status = "✅ PASS"
            action = "OK"
        elif dim_ok and ratio_ok and bw_score >= 70:
            status = "⚠️ REVIEW"
            action = "Check manually (borderline BW score)"
        else:
            status = "❌ FAIL"
            actions = []
            if not dim_ok:
                actions.append("too small")
            if not ratio_ok:
                actions.append("wrong aspect ratio")
            if bw_score < 70:
                actions.append(f"not binary enough ({bw_score:.0f}%)")
            action = "Regenerate — " + ", ".join(actions)

        results["images"].append({
            "file": png_file.name,
            "size": size_str,
            "ratio": f"{(w/h):.2f}",
            "bw_score": f"{bw_score:.0f}",
            "dim_check": "✓" if dim_ok else "✗",
            "ratio_check": "✓" if ratio_ok else "✗",
            "status": status,
            "action": action,
        })

    # Genera report
    report, pass_count, review_count, fail_count = generate_quality_report(job_id, results)

    # Salva file
    report_file = job_dir / f"quality_report_{job_id}.md"
    report_file.write_text(report)

    print(f"\n✅ Report saved: {report_file}")
    print(f"\n📊 Summary: {pass_count} PASS, {review_count} REVIEW, {fail_count} FAIL")
    print(report)


if __name__ == "__main__":
    main()
