"""
shared_customer_pool.py

Erzeugt einen 'Master-Pool' an fiktiven Personen (die einzige 'Wahrheit' in
diesem Projekt) und leitet daraus gezielt verzerrte Teilmengen für die drei
Quellsysteme ab. Nur weil wir hier zentral wissen, welche Datensätze
'eigentlich' dieselbe Person sind, können wir später Entity Resolution und
Schema Matching überhaupt objektiv evaluieren (Ground Truth).

Wichtig: Dieses Modul ist die einzige Stelle, die die 'Wahrheit' kennt.
Die generierten Quelldateien selbst enthalten KEINE globale ID, die Personen
über Quellen hinweg verknüpft -- das wäre ja die Aufgabe, die die Pipeline
später lösen soll.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from faker import Faker


@dataclass
class MasterCustomer:
    """Eine 'wahre' Person im Master-Pool."""
    master_id: str          # NUR für Ground Truth, erscheint nie in echten Quelldaten
    vorname: str
    nachname: str
    geburtsdatum: str        # ISO-Format YYYY-MM-DD als kanonische Wahrheit
    strasse: str
    hausnummer: int
    plz: str
    ort: str
    email: Optional[str] = None


def build_master_pool(n: int, seed: int, locale: str = "de_DE") -> list[MasterCustomer]:
    """Erzeugt n eindeutige, fiktive Personen als Grundwahrheit."""
    fake = Faker(locale)
    Faker.seed(seed)
    rng = random.Random(seed)

    pool: list[MasterCustomer] = []
    for i in range(n):
        vorname = fake.first_name()
        nachname = fake.last_name()
        geburtsdatum = fake.date_of_birth(minimum_age=18, maximum_age=85).isoformat()
        strasse = fake.street_name()
        hausnummer = rng.randint(1, 180)
        plz = fake.postcode()
        ort = fake.city()
        email = fake.email() if rng.random() > 0.15 else None  # ~15% ohne E-Mail

        pool.append(
            MasterCustomer(
                master_id=f"MC-{i:06d}",
                vorname=vorname,
                nachname=nachname,
                geburtsdatum=geburtsdatum,
                strasse=strasse,
                hausnummer=hausnummer,
                plz=plz,
                ort=ort,
                email=email,
            )
        )
    return pool


# --- Verzerrungsfunktionen (bewusst einfach & nachvollziehbar gehalten) ---

_TYPO_SWAPS = {"e": "a", "a": "e", "i": "y", "y": "i"}


def inject_name_typo(name: str, rng: random.Random) -> str:
    """Simuliert einen einzelnen, plausiblen Tippfehler in einem Namen."""
    if len(name) < 4:
        return name
    idx = rng.randint(1, len(name) - 2)
    chars = list(name)
    ch = chars[idx].lower()
    if ch in _TYPO_SWAPS:
        chars[idx] = _TYPO_SWAPS[ch]
    else:
        chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
    return "".join(chars)


def format_strasse_variant(strasse: str, variant: int) -> str:
    """Erzeugt unterschiedliche Schreibweisen von '...straße'."""
    if variant == 1:
        return strasse.replace("straße", "str.").replace("Straße", "Str.")
    if variant == 2:
        return strasse.replace("straße", "strasse").replace("Straße", "Strasse")
    return strasse


def format_date_ddmmyyyy(iso_date: str) -> str:
    y, m, d = iso_date.split("-")
    return f"{d}.{m}.{y}"


def corrupt_encoding(text: str) -> str:
    """
    Simuliert einen klassischen Encoding-Fehler (Mojibake), wie er bei alten
    CSV-Exporten auftritt, wenn UTF-8-Text fälschlich als Latin-1
    interpretiert wird -- z.B. 'Müller' wird zu 'MÃ¼ller'.
    """
    try:
        return text.encode("utf-8").decode("latin-1")
    except UnicodeDecodeError:
        return text


def inject_intra_source_duplicates(
    customers: list[MasterCustomer],
    fraction: float,
    rng: random.Random,
) -> list[MasterCustomer]:
    """
    Ersetzt einen kleinen Anteil der Liste durch Duplikate anderer Einträge
    IN DERSELBEN Liste -- simuliert den Fall, dass derselbe Kunde versehentlich
    zweimal in dasselbe System eingegeben wurde (z.B. weil vor Neuanlage nicht
    nach dem bestehenden Datensatz gesucht wurde). Die Länge der Liste bleibt
    gleich; dafür kommt ein anderer, ursprünglich einzigartiger Kunde in
    dieser Quelle nicht mehr vor (realistisch: Duplikate 'verdrängen' echte
    Distinktheit, sie werden nicht einfach obendrauf addiert).
    """
    customers = customers[:]
    n = len(customers)
    k = int(n * fraction)
    if k == 0:
        return customers
    idxs_to_duplicate = rng.sample(range(n), k)
    for idx in idxs_to_duplicate:
        other_idx = rng.choice([i for i in range(n) if i != idx])
        customers[idx] = customers[other_idx]
    return customers


def partition_pool_for_sources(
    pool: list[MasterCustomer],
    seed: int,
    n_a: int,
    n_b: int,
    n_c: int,
    n_overlap_ab: int,
    n_overlap_ac: int,
    n_overlap_bc: int = 0,
) -> tuple[list[MasterCustomer], list[MasterCustomer], list[MasterCustomer]]:
    """
    Erzeugt drei Kundenlisten mit EXPLIZIT kontrolliertem Overlap, statt rein
    unabhängiger Zufallsziehungen (die würden bei diesen Größenordnungen einen
    viel zu hohen, unrealistischen Overlap erzeugen -- z.B. bei 60%/43%
    unabhängigen Ziehungen liegt der erwartete Overlap allein durch
    Wahrscheinlichkeit schon bei ~26%, nicht bei den gewünschten 15-20%).

    Jede Person landet in maximal zwei Quellen (kein Dreifach-Overlap, das
    würde die Ground Truth unnötig verkomplizieren, ohne zusätzlichen
    Lernwert für Entity Resolution zu bringen).
    """
    only_a = n_a - n_overlap_ab - n_overlap_ac
    only_b = n_b - n_overlap_ab - n_overlap_bc
    only_c = n_c - n_overlap_ac - n_overlap_bc

    for name, val in [("only_a", only_a), ("only_b", only_b), ("only_c", only_c)]:
        if val < 0:
            raise ValueError(f"{name} wurde negativ ({val}) -- Overlap-Werte zu hoch für die Zielgrößen.")

    total_needed = only_a + only_b + only_c + n_overlap_ab + n_overlap_ac + n_overlap_bc
    if total_needed > len(pool):
        raise ValueError(
            f"Pool zu klein: benötigt {total_needed} eindeutige Personen, "
            f"Pool hat nur {len(pool)}. Pool-Größe erhöhen."
        )

    rng = random.Random(seed)
    shuffled = pool[:]
    rng.shuffle(shuffled)

    idx = 0
    group_only_a = shuffled[idx: idx + only_a]; idx += only_a
    group_only_b = shuffled[idx: idx + only_b]; idx += only_b
    group_only_c = shuffled[idx: idx + only_c]; idx += only_c
    group_ab = shuffled[idx: idx + n_overlap_ab]; idx += n_overlap_ab
    group_ac = shuffled[idx: idx + n_overlap_ac]; idx += n_overlap_ac
    group_bc = shuffled[idx: idx + n_overlap_bc]; idx += n_overlap_bc

    customers_a = group_only_a + group_ab + group_ac
    customers_b = group_only_b + group_ab + group_bc
    customers_c = group_only_c + group_ac + group_bc

    # Jede Quelle bekommt ihre eigene, unabhängige Zufallsreihenfolge, damit
    # die Position im Pool nicht verrät, welche Person in mehreren Quellen
    # vorkommt (wäre ein unrealistisches "Leck" der Ground Truth).
    rng.shuffle(customers_a)
    rng.shuffle(customers_b)
    rng.shuffle(customers_c)

    return customers_a, customers_b, customers_c
