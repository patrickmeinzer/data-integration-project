from pathlib import Path
from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)

# --- Postgres ---
POSTGRES_USER = os.getenv("POSTGRES_USER", "di_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "di_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "data_integration")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# --- MinIO ---
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "minio_admin")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "minio_password")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_RAW_BUCKET = "raw-data"

def get_postgres_connection_string() -> str:
    return (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )