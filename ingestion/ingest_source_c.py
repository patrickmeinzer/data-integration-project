from pathlib import Path

import pandas as pd
import pdfplumber

from . import connections
from . import config

SOURCE_C_DIR = config.PROJECT_ROOT / "data" / "synthetic" / "source_C"

def _read_single_pdf_table(pdf_path: Path) -> pd.DataFrame:
    all_rows = []
    header = None

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table is None:
                continue

            if header is None:
                header = table[0]
                all_rows.extend(table[1:])
            else:
                all_rows.extend(table)

    df = pd.DataFrame(all_rows, columns=header)
    df["source_file"] = pdf_path.name
    return df

def read_all_customer_pdfs() -> pd.DataFrame:
    pdf_paths = sorted(SOURCE_C_DIR.glob("partner_export_day*.pdf"))
    dataframes = [_read_single_pdf_table(p) for p in pdf_paths]
    return pd.concat(dataframes, ignore_index=True)

def read_all_contracts_pdfs() -> pd.DataFrame:
    pdf_paths = sorted(SOURCE_C_DIR.glob("partner_contracts_day*.pdf"))
    dataframes = [_read_single_pdf_table(p) for p in pdf_paths]
    return pd.concat(dataframes, ignore_index=True)

def upload_raw_files_to_minio() -> None:
    client = connections.get_minio_client()

    all_pdf_paths = sorted(SOURCE_C_DIR.glob("*.pdf"))
    for pdf_path in all_pdf_paths:
        connections.upload_file_to_minio(
            client=client,
            bucket_name=config.MINIO_RAW_BUCKET,
            local_path=pdf_path,
            object_key=f"source_c/{pdf_path.name}",
        )


def load_customers_to_postgres() -> None:
    df = read_all_customer_pdfs()
    engine = connections.get_postgres_engine()
    df.to_sql("raw_source_c_customers", engine, if_exists="replace", index=False)


def load_contracts_to_postgres() -> None:
    df = read_all_contracts_pdfs()
    engine = connections.get_postgres_engine()
    df.to_sql("raw_source_c_contracts", engine, if_exists="replace", index=False)


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