from kyros_plotly_common.core import dbx_client, redis_client
from kyros_plotly_common.layout.catalog import CatalogInitializer

catalog_initializer = CatalogInitializer(
    dbx_client=dbx_client,
    redis_client=redis_client,
    table_schema='mix',
    app_name="MixShift"
)