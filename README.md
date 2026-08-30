# Automatisierte Dateintegration mit ML-Unterstützung

> Status: 🚧 in Entwicklung — Phase 0 (Setup)

## Motivation

Während eines Praktikums bei Munich Re habe ich beobachtet, dass die Integration
von Daten aus unterschiedlichen internen Quellen teilweise noch manuell erfolgt.
Dieses Projekt ist der Versuch, diesen Prozess in einem realistischen, wenn auch
verkleinerten Rahmen zu automatisieren — von der Ingestion heterogener,
unsauberer Daten bis zur analysebereiten, konsolidierten Sicht.

## Business Case

Ein Unternehmen erhält täglich Daten aus mehreren Quellsystemen. Diese Daten sind:
- **unvollständig** (fehlende Werte, Pflichtfelder leer)
- **uneinheitlich** (unterschiedliche Schemas, Formate, Bezeichnungen für dieselbe Information)
- **teilweise fehlerhaft** (Tippfehler, Duplikate über Quellen hinweg)

Ziel ist die möglichst weitgehende Automatisierung der Integration dieser Daten
sowie deren Bereitstellung für nachgelagerte Analysen.

## Architektur

_(Diagramm folgt in Phase 5 — vorläufige Textbeschreibung:)_

```
[Quelle A: CSV]  [Quelle B: JSON/API]  [Quelle C: CSV]
        \               |                  /
         \              |                 /
          v             v                v
              Ingestion (Dagster)
                       |
                       v
            Raw Layer (MinIO / Parquet)
                       |
              Schema Matching (ML)
                       |
                       v
            Staging Layer (Postgres, via dbt)
                       |
            Entity Resolution (ML)
                       |
                       v
            Konsolidierte / analysebereite Daten
                       |
              Data Quality Checks (Great Expectations)
```

## Tech-Stack & Begründung

| Komponente        | Wahl                  | Warum |
|--------------------|-----------------------|-------|
| Orchestrierung      | Dagster               | Moderneres Asset-basiertes Modell, gute lokale DX, zunehmend nachgefragt |
| Transformation      | dbt                   | Testbare, versionierte SQL-Transformationen statt verstreuter Skripte |
| Data Quality        | Great Expectations    | Deklarative, wiederverwendbare Datenqualitätschecks |
| Data Lake (raw)     | MinIO (S3-kompatibel) | Realistische Objektspeicher-Simulation ohne Cloud-Kosten |
| Warehouse           | Postgres              | Verbreitetes, realistisches Zielsystem für dbt-Transformationen |
| ML: Schema Matching | sentence-transformers, rapidfuzz | Pretrained Embeddings ausreichend, kein Trainingsdatensatz nötig |
| ML: Entity Resolution | scikit-learn / xgboost | Klassisches Klassifikationsproblem auf Similarity-Features |

_(Wird in den jeweiligen Phasen weiter ausgeführt und begründet, inkl. bewusst
NICHT mit ML gelöster Schritte wie Datentyperkennung und Kategorisierung.)_

## Projektstruktur

```
.
├── ingestion/       # Einlese-Logik pro Quellsystem
├── transform/        # dbt-Projekt
├── ml/                # Schema Matching & Entity Resolution
├── pipelines/         # Dagster-Definitionen (Jobs, Assets, Schedules)
├── data/synthetic/    # Generierte synthetische Rohdaten (nicht committed)
├── tests/             # Unit-/Integrationstests
├── docs/              # Architekturdiagramme, weiterführende Doku
├── docker-compose.yml # Lokale Dev-Umgebung (Postgres, MinIO)
└── requirements.txt   # Python-Abhängigkeiten
```

## Setup (lokal)

```bash
# 1. Repository klonen und Python-Umgebung anlegen
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Umgebungsvariablen konfigurieren
cp .env.example .env

# 3. Postgres & MinIO starten
docker compose up -d

# 4. (folgt in Phase 1) Synthetische Daten generieren
# 5. (folgt in Phase 2) Dagster starten: dagster dev
```

## Projektphasen

- [x] Phase 0 — Setup & Grundgerüst
- [ ] Phase 1 — Synthetische Daten generieren
- [ ] Phase 2 — Basis-Pipeline ohne ML
- [ ] Phase 3 — Schema Matching mit ML
- [ ] Phase 4 — Entity Resolution mit ML
- [ ] Phase 5 — Qualitätssicherung, Monitoring & Dokumentation

## Trade-offs & bewusste Entscheidungen

_(Wird laufend ergänzt — Beispiel:)_

- **Dagster statt Airflow:** Für ein Solo-Projekt dieser Größe bietet Dagster
  durch das Asset-Modell und die lokale Entwicklungserfahrung Vorteile; Airflow
  ist im Enterprise-Umfeld weiter verbreitet, wurde aber bewusst nicht gewählt,
  um stattdessen die zunehmend nachgefragte Alternative zu zeigen.
- **Kein eigenes ML-Training für Schema Matching:** Pretrained Embeddings plus
  Feature-Engineering reichen für diesen Anwendungsfall aus; ein eigenes
  Trainingsverfahren hätte einen gelabelten Datensatz in einer Größenordnung
  erfordert, die für ein Portfolio-Projekt nicht sinnvoll aufzubauen ist.
