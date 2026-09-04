"""
contract_pool.py

Erzeugt 'wahre' Vertragsdatensätze, die auf bereits generierte, quellinterne
Kunden-IDs verweisen (z.B. 'A-00042'). Bewusst PRO QUELLE separat aufgerufen,
da Verträge in der Praxis im jeweiligen Quellsystem gegen dessen eigene
Kunden-ID verknüpft sind -- nicht gegen eine globale ID, die es in der
Realität so nicht gäbe.

Kategorie- und Status-Werte werden hier als 'wahre', kanonische Werte
festgelegt; die eigentliche Verzerrung (andere Schreibweise pro Quelle)
passiert erst in den source_*-Rendering-Funktionen.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

TRUE_CATEGORIES = ["Typ A", "Typ B", "Typ C"]
TRUE_STATUSES = ["active", "cancelled"]


@dataclass
class ContractTruth:
    seq: int
    customer_ref: str   # quellinterne Kunden-ID (z.B. 'A-00042')
    start_date: str      # ISO-Format YYYY-MM-DD als kanonische Wahrheit
    category: str         # einer von TRUE_CATEGORIES
    amount: float
    status: str            # einer von TRUE_STATUSES


def generate_contract_truths(
    customer_ids: list[str],
    target_count: int,
    seed: int,
) -> list[ContractTruth]:
    """
    Verteilt target_count Verträge auf die gegebenen Kunden-IDs. Die meisten
    Kunden bekommen genau einen Vertrag, manche keinen, wenige zwei -- das
    ist realistischer als 'jeder Kunde hat exakt einen Vertrag'.
    """
    rng = random.Random(seed)

    assignments: list[str] = []
    for cid in customer_ids:
        n_contracts = rng.choices([0, 1, 2], weights=[20, 65, 15])[0]
        assignments.extend([cid] * n_contracts)
    rng.shuffle(assignments)

    if len(assignments) > target_count:
        assignments = assignments[:target_count]
    elif len(assignments) < target_count:
        deficit = target_count - len(assignments)
        assignments.extend(rng.choices(customer_ids, k=deficit))

    truths = []
    for i, cid in enumerate(assignments):
        year = rng.randint(2015, 2026)
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        truths.append(
            ContractTruth(
                seq=i,
                customer_ref=cid,
                start_date=f"{year:04d}-{month:02d}-{day:02d}",
                category=rng.choices(TRUE_CATEGORIES, weights=[45, 35, 20])[0],
                amount=round(rng.uniform(150, 5000), 2),
                status=rng.choices(TRUE_STATUSES, weights=[80, 20])[0],
            )
        )
    return truths


def format_amount_de(x: float) -> str:
    """Deutsches Zahlenformat: Tausenderpunkt, Komma als Dezimaltrennzeichen."""
    s = f"{x:,.2f}"          # z.B. '1,234.56' (englisches Format als Zwischenschritt)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s                  # -> '1.234,56'
