from databricks.connect import DatabricksSession
import logging
from config.util.azure_config import load_config

config=load_config()
SOURCE_SCHEMA=config['schemas']['source']
TARGET_SCHEMA=config['schemas']['base']
cluster_id=config['databricks']['cluster-id']

def load_tpcds_to_store_data_schema():
    logging.info(f'Starting the data load from the source({SOURCE_SCHEMA}) to target({TARGET_SCHEMA}) location..')
    spark=DatabricksSession.builder.clusterId(cluster_id).getOrCreate()
    spark.sql(f'CREATE SCHEMA IF NOT EXISTS {SOURCE_SCHEMA}')
    logging.info('fetching all tables from Source table..')
    tables_df=spark.sql(f'show tables in {SOURCE_SCHEMA}')
    tables_df = spark.sql("SHOW TABLES IN samples.tpcds_sf1")
    tables_df.printSchema()
    tables_df.show()
    tables_list=[row['tableName'] for row in tables_df.collect()]
    logging.info(f'Found {len(tables_list)} to process')
    for table in tables_list:
        logging.info(f'Processing table..{table}')
        df=spark.read.table(f'{SOURCE_SCHEMA}.{table}')
        catalog, schema = TARGET_SCHEMA.split('.')
        target_table_path = f'{catalog}.`{schema}`.{table}'
        df.write.mode('overwrite').saveAsTable(target_table_path)
        logging.info(f'Successfully loaded {target_table_path}')

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    load_tpcds_to_store_data_schema()



