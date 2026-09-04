"""
generate_data.py

Hauptskript für Phase 1: erzeugt den Master-Customer-Pool, leitet daraus
verzerrte Teilmengen für die drei Quellen ab, schreibt die Quelldateien
(CSV, JSON, PDF) und exportiert die Ground Truth für spätere Evaluation.

Aufruf:
    python generate_data.py
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

from shared_customer_pool import (
    build_master_pool,
    partition_pool_for_sources,
    inject_intra_source_duplicates,
)
from source_a_legacy_csv import generate_source_a
from source_b_crm_json import generate_source_b
from source_c_partner_pdf import generate_source_c
from contract_pool import generate_contract_truths
from contracts_source_a import generate_contracts_source_a
from contracts_source_b import generate_contracts_source_b
from contracts_source_c import generate_contracts_source_c

SEED = 42
OUT_DIR = Path(__file__).parent

# Größenordnung gemäß Phase-1-Datenmodell.
POOL_SIZE = 4500          # etwas größer als die Summe der Zielgrößen, damit
                          # auch Personen übrig bleiben, die in KEINER Quelle
                          # vorkommen (realistisch: nicht jeder im "Adressbuch"
                          # der Welt ist zwangsläufig Kunde).
N_A = 2500                # Quelle A (Legacy-CSV)
N_B = 1800                # Quelle B (CRM-JSON)
N_C = 700                 # Quelle C (Partner-PDFs)

# Explizit kontrollierter Overlap (statt Zufall) -> realistische ~15-17%
# der insgesamt vorkommenden Kunden sind in zwei Quellen vertreten:
#   - A/B-Overlap: Kunden, die vom Legacy-System ins neue CRM migriert wurden
#   - A/C-Overlap: Direktkunden, die zusätzlich über den Partnerkanal geführt werden
N_OVERLAP_AB = 600
N_OVERLAP_AC = 120
N_OVERLAP_BC = 0          # kein direkter CRM/Partner-Overlap in diesem Szenario

# Vertragsvolumen pro Quelle (aus dem Phase-1-Datenmodell)
N_CONTRACTS_A = 3000
N_CONTRACTS_B = 2200
N_CONTRACTS_C = 900


def main() -> None:
    print(f"Erzeuge Master-Pool mit {POOL_SIZE} Personen (seed={SEED})...")
    pool = build_master_pool(n=POOL_SIZE, seed=SEED)

    customers_a, customers_b, customers_c = partition_pool_for_sources(
        pool,
        seed=SEED,
        n_a=N_A,
        n_b=N_B,
        n_c=N_C,
        n_overlap_ab=N_OVERLAP_AB,
        n_overlap_ac=N_OVERLAP_AC,
        n_overlap_bc=N_OVERLAP_BC,
    )

    # Intra-Source-Duplikate: ~2% pro Quelle, simuliert versehentliche
    # Doppelanlage innerhalb desselben Systems (nicht zu verwechseln mit dem
    # Overlap ZWISCHEN den Quellen oben).
    dup_rng_a = random.Random(SEED + 10)
    dup_rng_b = random.Random(SEED + 11)
    dup_rng_c = random.Random(SEED + 12)
    customers_a = inject_intra_source_duplicates(customers_a, fraction=0.02, rng=dup_rng_a)
    customers_b = inject_intra_source_duplicates(customers_b, fraction=0.02, rng=dup_rng_b)
    customers_c = inject_intra_source_duplicates(customers_c, fraction=0.02, rng=dup_rng_c)

    print(f"  Quelle A (CSV):  {len(customers_a)} Kunden")
    print(f"  Quelle B (JSON): {len(customers_b)} Kunden")
    print(f"  Quelle C (PDF):  {len(customers_c)} Kunden, verteilt auf ~18 Tagesdateien")

    print("\nGeneriere Quelle A (Legacy-CSV)...")
    rows_a = generate_source_a(customers_a, seed=SEED, out_path=OUT_DIR / "source_a" / "kunden_export.csv")

    print("Generiere Quelle B (CRM-JSON)...")
    records_b = generate_source_b(customers_b, seed=SEED, out_path=OUT_DIR / "source_b" / "customers.json")

    print("Generiere Quelle C (Partner-PDFs)...")
    rows_c = generate_source_c(customers_c, seed=SEED, out_dir=OUT_DIR / "source_c")

    # --- Verträge: referenzieren die soeben erzeugten, quellinternen Kunden-IDs ---
    print("\nGeneriere Vertragsdaten...")
    ids_a = [r["kundennr"] for r in rows_a]
    ids_b = [r["customer_id"] for r in records_b]
    ids_c = [r["cust_no"] for r in rows_c]

    contracts_a_truth = generate_contract_truths(ids_a, N_CONTRACTS_A, seed=SEED)
    contracts_b_truth = generate_contract_truths(ids_b, N_CONTRACTS_B, seed=SEED + 1)
    contracts_c_truth = generate_contract_truths(ids_c, N_CONTRACTS_C, seed=SEED + 2)

    generate_contracts_source_a(
        contracts_a_truth, seed=SEED, out_path=OUT_DIR / "source_a" / "vertraege_export.csv"
    )
    generate_contracts_source_b(
        contracts_b_truth, seed=SEED, out_path=OUT_DIR / "source_b" / "contracts.json"
    )
    generate_contracts_source_c(
        contracts_c_truth, seed=SEED, out_dir=OUT_DIR / "source_c"
    )
    print(f"  Quelle A: {len(contracts_a_truth)} Verträge")
    print(f"  Quelle B: {len(contracts_b_truth)} Verträge")
    print(f"  Quelle C: {len(contracts_c_truth)} Verträge, verteilt auf ~18 Tagesdateien")

    # --- Ground Truth erzeugen ---
    print("\nSchreibe Ground Truth...")
    write_ground_truth(pool, customers_a, customers_b, customers_c)

    print("\nFertig. Dateien liegen unter:", OUT_DIR)


def write_ground_truth(pool, customers_a, customers_b, customers_c) -> None:
    """
    Schreibt eine Zuordnung master_id -> in welchen Quellen (mit welchen
    quellinternen IDs) diese Person vorkommt. Das ist die 'Lösung', gegen die
    später Entity Resolution evaluiert wird -- NIEMALS Teil der Pipeline-
    Eingabe, nur für die Auswertung.

    Pro Quelle wird eine LISTE quellinterner IDs geführt (nicht nur eine
    einzelne ID), da durch die Intra-Source-Duplikate eine Person auch
    MEHRFACH innerhalb derselben Quelle auftauchen kann.
    """
    gt_dir = OUT_DIR / "ground_truth"
    gt_dir.mkdir(parents=True, exist_ok=True)

    id_a: dict[str, list[str]] = defaultdict(list)
    id_b: dict[str, list[str]] = defaultdict(list)
    id_c: dict[str, list[str]] = defaultdict(list)
    for i, c in enumerate(customers_a):
        id_a[c.master_id].append(f"A-{i:05d}")
    for i, c in enumerate(customers_b):
        id_b[c.master_id].append(f"B-{i:05d}")
    for i, c in enumerate(customers_c):
        id_c[c.master_id].append(f"C-{i:05d}")

    matches = []
    for c in pool:
        occurrences = {}
        if c.master_id in id_a:
            occurrences["source_a"] = id_a[c.master_id]
        if c.master_id in id_b:
            occurrences["source_b"] = id_b[c.master_id]
        if c.master_id in id_c:
            occurrences["source_c"] = id_c[c.master_id]

        if occurrences:
            has_intra_dup = any(len(ids) > 1 for ids in occurrences.values())
            matches.append(
                {
                    "master_id": c.master_id,
                    "occurrences": occurrences,
                    "n_sources": len(occurrences),
                    "has_intra_source_duplicate": has_intra_dup,
                }
            )

    n_multi_source = sum(1 for m in matches if m["n_sources"] > 1)
    n_intra_dup = sum(1 for m in matches if m["has_intra_source_duplicate"])
    print(f"  {len(matches)} Personen insgesamt in mind. einer Quelle")
    print(f"  {n_multi_source} Personen in mehreren Quellen (= cross-source Entity-Resolution-Fälle)")
    print(f"  {n_intra_dup} Personen mit Intra-Source-Duplikat (= innerhalb derselben Quelle doppelt)")

    with (gt_dir / "customer_matches.json").open("w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)

    schema_mapping = {
        "customer_id": {"source_a": "kundennr", "source_b": "customer_id", "source_c": "cust_no (Cust.No.)"},
        "name": {
            "source_a": "nachname + vorname (getrennt)",
            "source_b": "full_name (zusammengesetzt: 'Nachname, Vorname')",
            "source_c": "name (zusammengesetzt: 'Vorname Nachname')",
        },
        "date_of_birth": {"source_a": "geburtsdatum", "source_b": "date_of_birth", "source_c": "geb_dat"},
        "address": {
            "source_a": "plz + ort + strasse (getrennt)",
            "source_b": "postal_code + city (keine Straße)",
            "source_c": "adresse (ein Freitextfeld, alles zusammen)",
        },
        "contract_id": {
            "source_a": "vertragsnr",
            "source_b": "contract_id",
            "source_c": "vertr_nr (Vertr.-Nr.)",
        },
        "contract_customer_ref": {
            "source_a": "kundennr (referenziert Quelle-A-Kunden-ID)",
            "source_b": "customer_id (referenziert Quelle-B-Kunden-ID)",
            "source_c": "cust_no (referenziert Quelle-C-Kunden-ID)",
        },
        "contract_start_date": {"source_a": "beginn", "source_b": "start_date", "source_c": "beginn"},
        "contract_category": {
            "source_a": "typ ('Typ A' / 'Typ B' / 'Typ C', gelegentlich Kleinschreibung)",
            "source_b": "category ('TYPA' / 'TYPB' / 'TYPC')",
            "source_c": "typ ('type_a' / 'type_b' / 'type_c')",
        },
        "contract_amount": {
            "source_a": "betrag (deutsches Zahlenformat als String, z.B. '1.234,56')",
            "source_b": "amount (echte Zahl, z.B. 1234.56)",
            "source_c": "betrag (deutsches Zahlenformat + Einheit als Freitext, z.B. '1.234,56 EUR')",
        },
        "contract_status": {
            "source_a": "status ('aktiv' / 'gekuendigt', gelegentlich leer)",
            "source_b": "status ('active' / 'cancelled')",
            "source_c": "status ('1' / '0', numerischer Code)",
        },
    }
    with (gt_dir / "schema_mapping.json").open("w", encoding="utf-8") as f:
        json.dump(schema_mapping, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
