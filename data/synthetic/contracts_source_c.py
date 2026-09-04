"""
contracts_source_c.py

Verträge aus dem Partnerkanal: PDF-Tagesabgaben, Kategorie als snake_case-Code,
Status als numerischer Code (1/0) statt Text, Betrag mit Einheit als Freitext.
Insgesamt die unsauberste Quelle, analog zu den Kundendaten.
"""

from __future__ import annotations

import random
from pathlib import Path

from fpdf import FPDF

from contract_pool import ContractTruth, format_amount_de
from shared_customer_pool import format_date_ddmmyyyy

COLUMN_HEADERS = ["Vertr.-Nr.", "Cust.No.", "Beginn", "Typ", "Betrag", "Status"]
COLUMN_WIDTHS = [25, 25, 25, 30, 35, 20]

_CATEGORY_DISPLAY = {"Typ A": "type_a", "Typ B": "type_b", "Typ C": "type_c"}
_STATUS_DISPLAY = {"active": "1", "cancelled": "0"}


def render_contracts(contracts: list[ContractTruth], rng: random.Random) -> list[dict]:
    rows = []
    for i, c in enumerate(contracts):
        status = _STATUS_DISPLAY[c.status]
        # ~4% fehlender Status -- hier als Text-Platzhalter 'n/a', im
        # Gegensatz zu Quelle A (leerer String) und Quelle B (JSON-null).
        # Dritte, wieder andere Repräsentation für 'fehlt'.
        if rng.random() < 0.04:
            status = "n/a"

        rows.append(
            {
                "vertr_nr": f"CV-{i:05d}",
                "cust_no": c.customer_ref,
                "beginn": format_date_ddmmyyyy(c.start_date),
                "typ": _CATEGORY_DISPLAY[c.category],
                "betrag": f"{format_amount_de(c.amount)} EUR",
                "status": status,
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
        pdf.cell(COLUMN_WIDTHS[0], 7, row["vertr_nr"], border=1)
        pdf.cell(COLUMN_WIDTHS[1], 7, row["cust_no"], border=1)
        pdf.cell(COLUMN_WIDTHS[2], 7, row["beginn"], border=1)
        pdf.cell(COLUMN_WIDTHS[3], 7, row["typ"], border=1)
        pdf.cell(COLUMN_WIDTHS[4], 7, row["betrag"], border=1)
        pdf.cell(COLUMN_WIDTHS[5], 7, row["status"], border=1)
        pdf.ln()

    return pdf


def generate_contracts_source_c(
    contracts: list[ContractTruth],
    seed: int,
    out_dir: Path,
    n_daily_files: int = 18,
) -> list[dict]:
    rng = random.Random(seed)
    rows = render_contracts(contracts, rng)

    out_dir.mkdir(parents=True, exist_ok=True)

    shuffled = rows[:]
    rng.shuffle(shuffled)
    chunk_size = max(1, len(shuffled) // n_daily_files)

    for day_idx in range(n_daily_files):
        start = day_idx * chunk_size
        end = start + chunk_size if day_idx < n_daily_files - 1 else len(shuffled)
        chunk = shuffled[start:end]
        if not chunk:
            continue
        title = f"Partnerkanal - Vertragsabgabe {day_idx + 1:02d}"
        pdf = _build_pdf(chunk, title)
        out_path = out_dir / f"partner_contracts_day{day_idx + 1:02d}.pdf"
        pdf.output(str(out_path))

    return rows
