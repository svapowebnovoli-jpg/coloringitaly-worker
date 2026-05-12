#!/usr/bin/env python3
"""
Prompt Builder — Genera batch di 25 prompt Grok compilati per coloring book
Uso: python prompt_builder.py --country italy --theme vintage_vehicles --seq 001 --era 1970s
Output: italy_vintage_vehicles_001_prompts.md (pronto per copia-incolla su Grok.com)
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

# Soggetti matrix — Italy / Vintage Vehicles
SUBJECTS_MATRIX = {
    "italy_vintage_vehicles": {
        "era": "1970s",
        "hero_subjects": [
            ("Alfa Romeo Giulia Sprint GTA", "Via Veneto in Roma", "high performance iconic sedan"),
            ("Fiat 500 F", "cobblestone piazza with fountain", "tiny beloved city car"),
            ("Vespa 150 GS", "coastal Amalfi road", "legendary scooter"),
            ("Lancia Stratos HF", "snowy alpine pass", "wedge-shaped rally car"),
            ("Fiat 124 Spider", "Tuscan vineyard landscape", "open roadster"),
            ("Innocenti Mini Cooper", "narrow medieval Venetian alley", "british-origin tiny car"),
            ("Alfa Romeo Spider Duetto", "seaside promenade Portofino", "romantic convertible"),
            ("Fiat 850 Coupé", "Sicilian village street", "compact sport coupe"),
            ("Lancia Beta HPE", "mountain hairpin curve", "practical estate car"),
            ("Fiat 131 Abarth", "dirt gravel rally road", "homologation special"),
            ("Autobianchi A112 Abarth", "factory district outskirts", "tiny rally legend"),
            ("Fiat X1/9", "Milan street with modern architecture", "mid-engine sports car"),
            ("Lancia Fulvia HF", "forest road Apennines", "lightweight rally icon"),
            ("Fiat 132 GR", "suburban intersection traffic", "four-door family saloon"),
            ("Alfa Romeo Montreal", "exclusive parking Monaco street", "exotic 8-cylinder coupe"),
            ("Lancia Delta HF", "snowy forest road", "legendary future icon"),
            ("Fiat Ritmo 105 TC", "downtown parking garage", "hot hatch pioneer"),
            ("Innocenti 90", "historic center Florence", "1980s nostalgic"),
            ("Fiat 238", "village market square", "commercial van"),
            ("Fiat 127 Sport", "suburban school street", "70s hatchback"),
            ("Lancia Thema 8.32", "highway rest stop", "luxury executive"),
            ("Fiat Argenta", "industrial area factory", "practical sedan"),
            ("Alfa Romeo 6", "elegant villa entrance", "diplomatic luxury"),
            ("Fiat 500L", "rural country road Tuscany", "retro family car"),
            ("Vespa PX", "harbor fish market", "timeless scooter"),
        ],
        "signature_locations": [
            "Roman cobblestone piazza",
            "Tuscan vineyard landscape",
            "Amalfi coast hairpin",
            "Venetian medieval alley",
            "Alpine mountain pass",
            "Sicilian village street",
            "Milan industrial district",
            "Florence historic center",
            "Portofino harbor",
            "Apennine forest road",
        ],
    }
}

# Master Prompt Template (da grok-master-prompt-v1.md)
GROK_MASTER_TEMPLATE = """Printed adult coloring book page, single black ink on white paper, no gray values anywhere, no shading, no gradients, no halftones, binary black and white only — either pure black line or pure white space.

Variable line weight: thick 3pt bold outlines on foreground subject, thin 1pt delicate lines on background elements.

Iconic vintage {PAESE} vehicle as large foreground subject occupying at least 40% of frame, vehicle body composed of large open white areas ready for coloring. Precise mechanical details: visible grille, headlights, wheel spokes, badges and emblems clearly drawn, accurate body proportions of the specific model.

Sky must be pure white with minimal line clouds only, trees and vegetation drawn with sparse outline strokes only no texture fills, mountains drawn with simple contour lines only no shading, human figures as simple clean outline silhouettes only with no solid fills.

Recognizable specific location with identifiable architectural or landscape features, not generic background.

Strong compositional hierarchy: foreground subject dominates, background supports. Vertical portrait format 2:3 ratio.

Absolutely no cartoon style, no manga style, no children illustration. Editorial line art quality only, magazine-grade illustration, high contrast print-ready professional adult coloring book quality.

{SOGGETTO_AMBIENTAZIONE}"""


def get_subject_matrix(country, theme):
    """Recupera soggetti matrix per paese/tema."""
    key = f"{country}_{theme}"
    if key not in SUBJECTS_MATRIX:
        raise ValueError(f"Theme {key} not found. Available: {list(SUBJECTS_MATRIX.keys())}")
    return SUBJECTS_MATRIX[key]


def generate_prompts(country, theme, seq, era=None):
    """Genera lista di 25 prompt compilati (1 cover + 24 pagine)."""
    matrix = get_subject_matrix(country, theme)
    subjects = matrix["hero_subjects"]

    if era is None:
        era = matrix.get("era", "vintage")

    prompts = []

    # COVER (page 00)
    subject_name, location, description = subjects[0]
    soil_location = location

    prompt = GROK_MASTER_TEMPLATE.format(
        PAESE=country.capitalize(),
        SOGGETTO_AMBIENTAZIONE=f"{subject_name} parked in {soil_location}, {description}, {era} era"
    )

    prompts.append({
        "page": "COVER",
        "page_num": "00",
        "subject": subject_name,
        "location": location,
        "description": description,
        "prompt": prompt,
        "qa_notes": f"Verifica marcatura {subject_name} accurata, proporzioni corrette, era {era}"
    })

    # PAGINE INTERNI (01-24)
    for page_idx in range(1, 25):
        subject_idx = (page_idx % len(subjects))
        subject_name, location, description = subjects[subject_idx]

        prompt = GROK_MASTER_TEMPLATE.format(
            PAESE=country.capitalize(),
            SOGGETTO_AMBIENTAZIONE=f"{subject_name} in {location}, {description}, {era} era"
        )

        prompts.append({
            "page": f"PAGE {page_idx:02d}",
            "page_num": f"{page_idx:02d}",
            "subject": subject_name,
            "location": location,
            "description": description,
            "prompt": prompt,
            "qa_notes": f"Verifica veicolo occupa >=40% frame, linework editoriale, {era} style"
        })

    return prompts


def write_batch_file(country, theme, seq, prompts):
    """Scrive file markdown con batch di prompt."""
    job_id = f"{country}_{theme}_{seq}"
    output_file = Path(f"{job_id}_prompts.md")

    timestamp = datetime.utcnow().isoformat() + "Z"

    content = f"""# Prompt Batch — {country.capitalize()} {theme.replace('_', ' ').title()}

**Job ID:** {job_id}
**Generated:** {timestamp}
**Total Pages:** {len(prompts)} (1 cover + 24 interni)
**Format:** Binary black & white, editorial line art, 2:3 vertical

---

"""

    for item in prompts:
        content += f"## {item['page']}\n\n"
        content += f"**Subject:** {item['subject']}\n"
        content += f"**Location:** {item['location']}\n"
        content += f"**Description:** {item['description']}\n\n"
        content += f"### Prompt (copia-incolla su Grok.com)\n\n"
        content += f"```\n{item['prompt']}\n```\n\n"
        content += f"### QA Notes\n{item['qa_notes']}\n\n"
        content += "---\n\n"

    content += f"""## Summary

Total: {len(prompts)} prompt
- 1x COVER
- 24x PAGE (01-24)

Istruzioni:
1. Copia ogni prompt sopra
2. Incolla in Grok.com (grok.com/creations)
3. Genera immagine
4. Scarica PNG (nomina: cover.png, page_01.png, …, page_24.png)
5. Carica in `/srv/coloringitaly/jobs/{job_id}/input/raw/`
6. Esegui `python quality_checker.py --job_id {job_id}`
7. Se PASS, esegui `curl -X POST http://localhost:8000/importa -H "X-Auth-Token: ..." -d '{{"job_id": "{job_id}", "book_title": "..."}}'`
"""

    output_file.write_text(content)
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Genera batch di prompt Grok compilati per coloring book"
    )
    parser.add_argument("--country", required=True, help="es. italy, france, japan")
    parser.add_argument("--theme", required=True, help="es. vintage_vehicles, markets, villages")
    parser.add_argument("--seq", required=True, help="es. 001, 002")
    parser.add_argument("--era", default=None, help="es. 1970s, 1960s, modern (default: da matrix)")

    args = parser.parse_args()

    print(f"🎨 Generating prompts for {args.country.upper()} / {args.theme.upper()}")

    try:
        prompts = generate_prompts(args.country, args.theme, args.seq, args.era)
        output_file = write_batch_file(args.country, args.theme, args.seq, prompts)

        print(f"✅ {len(prompts)} prompts generated!")
        print(f"📄 File: {output_file.absolute()}")
        print(f"\n📋 Next steps:")
        print(f"   1. Apri il file: {output_file}")
        print(f"   2. Vai a grok.com/creations")
        print(f"   3. Copia il primo prompt, genera l'immagine")
        print(f"   4. Una volta scaricate tutte, esegui: python quality_checker.py --job_id {args.country}_{args.theme}_{args.seq}")

    except ValueError as e:
        print(f"❌ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
