import pandas as pd

from . import config
from . import connections

SOURCE_A_DIR = config.PROJECT_ROOT / "data" / "synthetic" / "source_a"

def _read_source_a_csv(filename: str) -> pd.DataFrame:
    csv_path = SOURCE_A_DIR / filename
    return pd.read_csv(csv_path, delimiter=";", encoding="utf-8")

def read_customers_csv() -> pd.DataFrame:
    return _read_source_a_csv("kunden_export.csv")

def read_contracts_csv() -> pd.DataFrame:
    return _read_source_a_csv("vertraege_export.csv")

def upload_raw_files_to_minio() -> None:
    client = connections.get_minio_client()

    filenames = ["kunden_export.csv", "vertraege_export.csv"]
    for filename in filenames:
        connections.upload_file_to_minio(
            client=client,
            bucket_name=config.MINIO_RAW_BUCKET,
            local_path=SOURCE_A_DIR / filename,
            object_key=f"source_a/{filename}",
        )

def load_customers_to_postgres() -> None:
    df = read_customers_csv()
    engine = connections.get_postgres_engine()
    df.to_sql("raw_source_a_customers", engine, if_exists="replace", index=False)

def load_contracts_to_postgres() -> None:
    df = read_contracts_csv()
    engine = connections.get_postgres_engine()
    df.to_sql("raw_source_a_contracts", engine, if_exists="replace", index=False)

def main() -> None:
    print("Lade Rohdateien nach MinIO hoch...")
    upload_raw_files_to_minio()

    print("Lade Kundendaten nach Postgres...")
    load_customers_to_postgres()

    print("Lade Vertragsdaten nach Postgres...")
    load_contracts_to_postgres()

    print("Fertig.")


if __name__ == "__main__":
    main()