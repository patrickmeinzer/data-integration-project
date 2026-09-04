"""
source_c_partner_pdf.py

Simuliert den externen Partnerkanal: mehrere kleine PDF-'Tagesabgaben' mit
jeweils einer Tabelle. Adresse als zusammengesetztes Freitextfeld (typisch für
Exporte aus alten Reporting-Tools), Name als ein Feld statt getrennter
Vor-/Nachname-Spalten.

Nutzt fpdf2 (leichtgewichtig, ausreichend für einfache Tabellen-Layouts).
"""

from __future__ import annotations

import random
from pathlib import Path

from fpdf import FPDF

from shared_customer_pool import (
    MasterCustomer,
    format_date_ddmmyyyy,
    format_strasse_variant,
    inject_name_typo,
)

COLUMN_HEADERS = ["Cust.No.", "Name", "Geb.-Dat.", "Adresse"]
COLUMN_WIDTHS = [25, 45, 30, 90]


def render_customers(customers: list[MasterCustomer], rng: random.Random) -> list[dict]:
    rows = []
    for i, c in enumerate(customers):
        vorname = c.vorname
        nachname = c.nachname
        if rng.random() < 0.10:  # Partnerkanal hat die schlechteste Datenqualität
            nachname = inject_name_typo(nachname, rng)

        strasse_variant = rng.choice([0, 1, 2])
        strasse = format_strasse_variant(c.strasse, strasse_variant)
        adresse = f"{strasse} {c.hausnummer}, {c.plz} {c.ort}"

        rows.append(
            {
                "cust_no": f"C-{i:05d}",
                "name": f"{vorname} {nachname}",
                "geb_dat": format_date_ddmmyyyy(c.geburtsdatum),
                "adresse": adresse,
            }
        )
    return rows


def _build_pdf(rows: list[dict], title: str) -> FPDF:
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, title, ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    for header, width in zip(COLUMN_HEADERS, COLUMN_WIDTHS):
        pdf.cell(width, 8, header, border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for row in rows:
        pdf.cell(COLUMN_WIDTHS[0], 7, row["cust_no"], border=1)
        pdf.cell(COLUMN_WIDTHS[1], 7, row["name"], border=1)
        pdf.cell(COLUMN_WIDTHS[2], 7, row["geb_dat"], border=1)
        pdf.cell(COLUMN_WIDTHS[3], 7, row["adresse"], border=1)
        pdf.ln()

    return pdf


def generate_source_c(
    customers: list[MasterCustomer],
    seed: int,
    out_dir: Path,
    n_daily_files: int = 18,
) -> list[dict]:
    """Verteilt die Kunden auf n_daily_files einzelne PDF-'Tagesabgaben'."""
    rng = random.Random(seed)
    rows = render_customers(customers, rng)

    out_dir.mkdir(parents=True, exist_ok=True)

    # Kunden gleichmäßig (mit etwas Zufall in der Größe) auf Tagesdateien verteilen
    shuffled = rows[:]
    rng.shuffle(shuffled)
    chunk_size = max(1, len(shuffled) // n_daily_files)

    for day_idx in range(n_daily_files):
        start = day_idx * chunk_size
        end = start + chunk_size if day_idx < n_daily_files - 1 else len(shuffled)
        chunk = shuffled[start:end]
        if not chunk:
            continue
        title = f"Partnerkanal - Tagesabgabe {day_idx + 1:02d}"
        pdf = _build_pdf(chunk, title)
        out_path = out_dir / f"partner_export_day{day_idx + 1:02d}.pdf"
        pdf.output(str(out_path))

    return rows
