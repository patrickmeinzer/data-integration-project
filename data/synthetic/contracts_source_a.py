"""
contracts_source_a.py

Verträge aus dem Legacy-System: CSV, deutsches Datumsformat, deutsches
Zahlenformat für Beträge, gelegentlich fehlender Status.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

from contract_pool import ContractTruth, format_amount_de
from shared_customer_pool import format_date_ddmmyyyy

COLUMNS = ["vertragsnr", "kundennr", "beginn", "typ", "betrag", "status"]

_STATUS_DISPLAY = {"active": "aktiv", "cancelled": "gekuendigt"}


def render_contracts(contracts: list[ContractTruth], rng: random.Random) -> list[dict]:
    rows = []
    for i, c in enumerate(contracts):
        typ = c.category
        # ~10% Groß-/Kleinschreibungs-Inkonsistenz, wie im echten Altsystem üblich
        if rng.random() < 0.10:
            typ = typ.lower()

        status = _STATUS_DISPLAY[c.status]
        # ~3% fehlender Status
        if rng.random() < 0.03:
            status = ""

        rows.append(
            {
                "vertragsnr": f"AV-{i:05d}",
                "kundennr": c.customer_ref,
                "beginn": format_date_ddmmyyyy(c.start_date),
                "typ": typ,
                "betrag": format_amount_de(c.amount),
                "status": status,
            }
        )
    return rows


def write_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def generate_contracts_source_a(
    contracts: list[ContractTruth],
    seed: int,
    out_path: Path,
) -> list[dict]:
    rng = random.Random(seed)
    rows = render_contracts(contracts, rng)
    write_csv(rows, out_path)
    return rows
