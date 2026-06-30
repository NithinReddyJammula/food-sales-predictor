import logging
import sys
from pathlib import Path

# Add data-pipeline directory to python path to resolve config package
try:
    script_dir = Path(__file__).resolve().parent
except NameError:
    import inspect
    import os
    frame = inspect.currentframe()
    co_filename = frame.f_code.co_filename if frame else None
    if co_filename and not co_filename.startswith('<'):
        script_dir = Path(co_filename).resolve().parent
    else:
        script_dir = Path(os.getcwd())

parent_dir = str(script_dir.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import yaml
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

class DatasetCleaning:
    def __init__(self,tracer):
        self.tracer=tracer

    def load_config(self,config_path:str) -> dict:
        logging.info('Loading the Configuration File..')
        try:
            from config.util.azure_config import load_config as load_interpolated_config
            return load_interpolated_config(config_path)
        except Exception as e:
            logging.error(f'Error loading configuration file from {config_path}: {str(e)}')
            raise

    def clean_data(self,config_path:str):
        with self.tracer.start_as_current_span('data_cleaning_pipeline'):
            config = self.load_config(config_path)
            db_config = config['databricks']
            schemas = config['schemas']
            features = config['Features']
            encoding = features['categorical_encoding']
            source_location = config['training_data_location']['dataset']
            target_location = config['transformed_target_table']
            target_catalog = db_config['catalog']
            target_schema = schemas['base']
            target_table = f'{target_catalog}.{target_schema}.{target_location}'
            app_name = db_config.get('app_name')
            spark = SparkSession.builder.appName(app_name).getOrCreate()
            logging.info(f'Loading raw dataset from {source_location}')
            df_raw = spark.read.format("csv").option('header', True).option('inferSchema', 'true').load(source_location)
            drop_columns = [col for col in config.get('drop_columns', []) if col in df_raw.columns]
            df = df_raw.drop(*drop_columns)
            categorical_cols = encoding.get('columns', [])
            for col_name in categorical_cols:
                if col_name in df.columns:
                    df = df.withColumn(col_name, F.upper(F.trim(F.col(col_name))))
            if 'transaction_timestamp' in df.columns:
                df = df.withColumn('transaction_timestamp', F.to_timestamp(F.col('transaction_timestamp')))
            if 'day_date' in df.columns:
                df = df.withColumn('day_date', F.to_date(F.col('day_date')))
            numerical_cols = features.get('numerical', [])
            for num_col in numerical_cols:
                if num_col in df.columns:
                    df = df.withColumn(num_col, F.col(num_col).cast('double'))
            group_keys = config.get('group_ids', ['store_id', 'Item Slin'])
            original_time_col = 'transaction_timestamp'
            if all(k in df.columns for k in group_keys) and original_time_col in df.columns:
                logging.info("Executing Time-Series Aggregation with Promo Feature Flags...")
                df = df.withColumn('hourly_time_index', F.date_trunc('hour', F.col(original_time_col)))
                promo_pivot_df = df.groupBy(*group_keys, 'hourly_time_index').pivot('promotion_id').sum('promo_quantity')
                promo_pivot_df = promo_pivot_df.na.fill(0)
                for col in promo_pivot_df.columns:
                    if col not in group_keys and col != 'hourly_time_index':
                        promo_pivot_df = promo_pivot_df.withColumnRenamed(col, f'feature_promo_{col}')
                agg_keys = group_keys + ['hourly_time_index']
                aggregations = []
                target_col = config['target']
                for col_name in df.columns:
                    # Skip the grouping keys, the promo ID, AND the old raw timestamp
                    if col_name in agg_keys or col_name == 'promotion_id' or col_name == original_time_col:
                        continue
                    elif col_name in [target_col, 'Gross_sales', 'promo_amount']:
                        aggregations.append(F.sum(col_name).alias(col_name))
                    elif col_name in ['avg_sell_price', 'PRODUCTION_QUANTITY', 'HOLD_TIME']:
                        aggregations.append(F.avg(col_name).alias(col_name))
                    else:
                        aggregations.append(F.first(col_name, ignorenulls=True).alias(col_name))
                main_agg_df = df.groupBy(*agg_keys).agg(*aggregations)
                df_final = main_agg_df.join(promo_pivot_df, on=agg_keys, how='left')
                df = df_final.withColumn(original_time_col, F.col('hourly_time_index')).drop('hourly_time_index')
                logging.info('Enforcing operational business rule validation gates..')
                if target_col in df.columns:
                    df = df.filter(F.col(target_col) >= 0)
                if 'Gross_sales' in df.columns:
                    df = df.filter(F.col('Gross_sales') >= 0)
                if 'avg_sell_price' in df.columns:
                    df = df.filter((F.col('avg_sell_price') >= 0) | F.col('avg_sell_price').isNull())
                logging.info('Applying Null Imputation rules from config..')
                fill_na_rules = encoding.get('fill_na', {})
                active_fills = {k: v for k, v in fill_na_rules.items() if k in df.columns}
                if active_fills:
                    df = df.na.fill(active_fills)
                string_cols = [f.name for f in df.schema.fields if isinstance(f.dataType,StringType)]
                default_string_fills = {c: 'UNKNOWN' for c in string_cols if c in categorical_cols and c not in active_fills}
                if default_string_fills:
                    df = df.na.fill(default_string_fills)

                logging.info(f'Writing clean data to Databricks Unity Catalog: {target_table}')
                df.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').option(
                    'delta.autooptimize.optimizeWrite', 'true').option("delta.autoOptimize.autoCompact",
                                                                       "true").saveAsTable(target_table)
                logging.info("Data cleaning stage completed successfully.")



if __name__=="__main__":
    import argparse
    import sys
    from config.util.monitoring import Observability

    Observability.initialize()
    tracer=Observability.get_tracer(__name__)
    parser=argparse.ArgumentParser(description='TFT Data Cleaning Pipeline')
    parser.add_argument('--config',type=str,required=True)
    args=parser.parse_args()
    cleaner=DatasetCleaning(tracer)
    cleaner.clean_data(args.config)




                    



























