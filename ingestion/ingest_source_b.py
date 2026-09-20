import json

import pandas as pd

import connections
import config

SOURCE_B_DIR = config.PROJECT_ROOT / "data" / "synthetic" / "source_b"


def _read_source_b_json(filename: str, key: str) -> pd.DataFrame:
    json_path = SOURCE_B_DIR / filename
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data[key])


def read_customers_json() -> pd.DataFrame:
    return _read_source_b_json("customers.json", "customers")


def read_contracts_json() -> pd.DataFrame:
    return _read_source_b_json("contracts.json", "contracts")


def upload_raw_files_to_minio() -> None:
    client = connections.get_minio_client()

    filenames = ["customers.json", "contracts.json"]
    for filename in filenames:
        connections.upload_file_to_minio(
            client=client,
            bucket_name=config.MINIO_RAW_BUCKET,
            local_path=SOURCE_B_DIR / filename,
            object_key=f"source_b/{filename}",
        )


def load_customers_to_postgres() -> None:
    df = read_customers_json()
    engine = connections.get_postgres_engine()
    df.to_sql("raw_source_b_customers", engine, if_exists="replace", index=False)


def load_contracts_to_postgres() -> None:
    df = read_contracts_json()
    engine = connections.get_postgres_engine()
    df.to_sql("raw_source_b_contracts", engine, if_exists="replace", index=False)


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