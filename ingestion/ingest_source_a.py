import pandas as pd

from . import config
from . import connections

SOURCE_A_DIR = config.PROJECT_ROOT / "data" / "synthetic" / "source_a"
DOWNLOAD_DIR = config.PROJECT_ROOT / "data" / "minio_downloads" / "source_a"

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
def _download_and_read_source_a_csv(filename: str) -> pd.DataFrame:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    local_path = DOWNLOAD_DIR / filename

    client = connections.get_minio_client()
    connections.download_file_from_minio(
        client=client,
        bucket_name=config.MINIO_RAW_BUCKET,
        object_key=f"source_a/{filename}",
        local_path=local_path,
    )
    return pd.read_csv(local_path, delimiter=";", encoding="utf-8")

def load_customers_to_postgres() -> None:
    df = _download_and_read_source_a_csv("kunden_export.csv")
    engine = connections.get_postgres_engine()
    df.to_sql("raw_source_a_customers", engine, if_exists="replace", index=False)

def load_contracts_to_postgres() -> None:
    df = _download_and_read_source_a_csv("vertraege_export.csv")
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