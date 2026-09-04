"""
source_a_legacy_csv.py

Simuliert das alte Kernsystem: CSV-Export, deutsche Datumsformate,
getrennte Vor-/Nachnamen-Spalten, gelegentliche Tippfehler und fehlende PLZ.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

from shared_customer_pool import (
    MasterCustomer,
    corrupt_encoding,
    format_date_ddmmyyyy,
    inject_name_typo,
)

COLUMNS = ["kundennr", "nachname", "vorname", "geburtsdatum", "plz", "ort", "strasse"]


def render_customers(customers: list[MasterCustomer], rng: random.Random) -> list[dict]:
    rows = []
    for i, c in enumerate(customers):
        nachname = c.nachname
        # ~8% der Datensätze bekommen einen Tippfehler im Nachnamen
        if rng.random() < 0.08:
            nachname = inject_name_typo(nachname, rng)

        ort = c.ort
        strasse = c.strasse
        # ~5% Encoding-Fehler (Mojibake) -- klassisches Legacy-CSV-Problem,
        # unabhängig vom Tippfehler oben, kann also auch gemeinsam auftreten.
        # Betrifft bevorzugt Felder mit Umlauten.
        if rng.random() < 0.05:
            nachname = corrupt_encoding(nachname)
            ort = corrupt_encoding(ort)
            strasse = corrupt_encoding(strasse)

        plz = c.plz
        # ~5% fehlende PLZ (klassische Datenqualitätslücke, hier als leerer String)
        if rng.random() < 0.05:
            plz = ""

        rows.append(
            {
                "kundennr": f"A-{i:05d}",
                "nachname": nachname,
                "vorname": c.vorname,
                "geburtsdatum": format_date_ddmmyyyy(c.geburtsdatum),
                "plz": plz,
                "ort": ort,
                "strasse": f"{strasse} {c.hausnummer}",
            }
        )
    return rows


def write_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def generate_source_a(
    customers: list[MasterCustomer],
    seed: int,
    out_path: Path,
) -> list[dict]:
    rng = random.Random(seed)
    rows = render_customers(customers, rng)
    write_csv(rows, out_path)
    return rows
