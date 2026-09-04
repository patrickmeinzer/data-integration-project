"""
contracts_source_b.py

Verträge aus dem neueren CRM: JSON, ISO-Datum, Beträge als echte Zahlen
(kein String), Kategorie als kompakter Großbuchstaben-Code ohne Leerzeichen.
Insgesamt die 'sauberste' Quelle, analog zu den Kundendaten.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from contract_pool import ContractTruth

_CATEGORY_DISPLAY = {"Typ A": "TYPA", "Typ B": "TYPB", "Typ C": "TYPC"}


def render_contracts(contracts: list[ContractTruth], rng: random.Random) -> list[dict]:
    records = []
    for i, c in enumerate(contracts):
        category = _CATEGORY_DISPLAY[c.category]
        # ~4% fehlende Kategorie -- hier als echtes JSON-null, im Gegensatz zu
        # Quelle A (leerer String) und Quelle C (Text-Platzhalter). Das zwingt
        # die Ingestion-Logik, mehrere verschiedene 'das bedeutet eigentlich
        # NULL'-Repräsentationen zu erkennen.
        if rng.random() < 0.04:
            category = None

        records.append(
            {
                "contract_id": f"BV-{i:05d}",
                "customer_id": c.customer_ref,
                "start_date": c.start_date,          # bereits ISO
                "category": category,
                "amount": c.amount,                    # echte Zahl, kein String
                "status": c.status,                     # 'active' / 'cancelled', direkt
            }
        )
    return records


def write_json(records: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump({"contracts": records}, f, ensure_ascii=False, indent=2)


def generate_contracts_source_b(
    contracts: list[ContractTruth],
    seed: int,
    out_path: Path,
) -> list[dict]:
    rng = random.Random(seed)
    records = render_contracts(contracts, rng)
    write_json(records, out_path)
    return records
