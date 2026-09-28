from dagster import Definitions

from pipelines import assets_source_a
from pipelines import assets_source_b

defs = Definitions(
    assets=[
        assets_source_a.source_a_files_in_minio,
        assets_source_a.raw_source_a_customers,
        assets_source_a.raw_source_a_contracts,
        assets_source_b.source_b_files_in_minio,
        assets_source_b.raw_source_b_customers,
        assets_source_b.raw_source_b_contracts,
    ],
)