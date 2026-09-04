"""
source_b_crm_json.py

Simuliert das neuere CRM/System (z.B. nach einer Migration): JSON-Export,
zusammengesetztes full_name-Feld statt getrennter Vor-/Nachname, ISO-Datum,
enthält (meistens) eine E-Mail-Adresse.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from shared_customer_pool import MasterCustomer, inject_name_typo


def render_customers(customers: list[MasterCustomer], rng: random.Random) -> list[dict]:
    records = []
    for i, c in enumerate(customers):
        nachname = c.nachname
        # ~5% Tippfehlerquote (etwas gepflegter als Quelle A, da neueres System)
        if rng.random() < 0.05:
            nachname = inject_name_typo(nachname, rng)

        records.append(
            {
                "customer_id": f"B-{i:05d}",
                "full_name": f"{nachname}, {c.vorname}",
                "date_of_birth": c.geburtsdatum,  # bereits ISO-Format
                "postal_code": c.plz,
                "city": c.ort,
                "email": c.email,  # kann None sein -> im JSON dann null
            }
        )
    return records


def write_json(records: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump({"customers": records}, f, ensure_ascii=False, indent=2)


def generate_source_b(
    customers: list[MasterCustomer],
    seed: int,
    out_path: Path,
) -> list[dict]:
    rng = random.Random(seed)
    records = render_customers(customers, rng)
    write_json(records, out_path)
    return records
