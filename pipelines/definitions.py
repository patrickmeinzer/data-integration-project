from dagster import Definitions

from pipelines import assets_source_a
from pipelines import assets_source_b
from pipelines import assets_source_c

defs = Definitions(
    assets=[
        assets_source_a.source_a_files_in_minio,
        assets_source_a.raw_source_a_customers,
        assets_source_a.raw_source_a_contracts,
        assets_source_b.source_b_files_in_minio,
        assets_source_b.raw_source_b_customers,
        assets_source_b.raw_source_b_contracts, 
        assets_source_c.source_c_files_in_minio,
        assets_source_c.raw_source_c_customers,
        assets_source_c.raw_source_c_contracts, 
    ],
)