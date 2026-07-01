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

from typing import Dict, List, Tuple
import yaml
from pyspark.ml.feature import StringIndexer
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
import math


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TFT-Transformation-Pipeline")

# Cyclical period bounds for sin/cos encoding.
# Any extracted component listed here will be encoded as two new columns
# (<col>_sin, <col>_cos) instead of keeping the raw integer.
CYCLICAL_PERIODS = {
    'hour':        24,
    'dayofweek':    7,
    'month':       12,
    'weekofyear':  52,
    'dayofmonth':  31,
}

class DataTransformation:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self.load_config(config_path)
        self.spark = self.init_spark()

    def load_config(self, config_path: str) -> Dict:
        logger.info('Loading the Configuration File..')
        try:
            from config.util.azure_config import load_config as load_interpolated_config
            return load_interpolated_config(config_path)
        except Exception as e:
            logger.error(f'Error loading configuration file from {config_path}: {e}')
            raise e

    def init_spark(self) -> SparkSession:
        if 'spark' in globals():
            logger.info('Acquired active cloud Databricks Spark environment context.')
            return globals()['spark']
        app_name = self.config['databricks'].get('app-name', 'TFT_Feature_Transformation') + '_Engine'
        logger.info(f'Initializing local fallback Sparksession context instance: {app_name}')
        return SparkSession.builder.appName(app_name) \
            .config('spark.sql.execution.arrow.pyspark.enabled', 'true') \
            .config('spark.sql.adaptive.enabled', 'true') \
            .getOrCreate()

    def get_table_urls(self) -> Tuple[str, str]:
        db_config = self.config['databricks']
        catalog = db_config['catalog']

        source_schema = self.config['schemas']['base']
        source_table = self.config['transformed_target_table']
        source_uri = f"{catalog}.`{source_schema}`.{source_table}"

        target_schema = self.config['schemas']['processed']
        target_uri = f"{catalog}.`{target_schema}`.{source_table}_final"

        return source_uri, target_uri

    def extract_datetime_features(self, df: DataFrame) -> DataFrame:
        """
        Extracts calendar features from datetime columns and applies cyclical
        (sin/cos) encoding to periodic components so that the TFT attention
        blocks can recognise proximity across period boundaries
        (e.g. hour 23 ≈ hour 0, December ≈ January).

        Raw integer extracts are retained alongside their sin/cos pairs only
        for non-cyclical components (quarter, year). All cyclical components
        produce *only* the sin/cos pair — keeping the raw integer would give
        the model a redundant and ordinally-misleading signal.
        """
        logger.info("Executing calendar and operational timestamp token feature extraction...")
        dt_configs = self.config['Features'].get('date_time_features', {})

        for base_col, config in dt_configs.items():
            if base_col not in df.columns:
                logger.warning(
                    f'Configured base date timestamp column {base_col} missing '
                    f'from target dataframe. Skipping.'
                )
                continue

            extract_targets = config.get('extract', [])
            for target in extract_targets:
                raw_col = f'{base_col}_{target}'

                # ── Step 1: extract the raw integer component ────────────────
                if target == 'hour':
                    df = df.withColumn(raw_col, F.hour(F.col(base_col)))
                elif target == 'dayofweek':
                    df = df.withColumn(raw_col, F.dayofweek(F.col(base_col)))
                elif target == 'dayofmonth':
                    df = df.withColumn(raw_col, F.dayofmonth(F.col(base_col)))
                elif target == 'month':
                    df = df.withColumn(raw_col, F.month(F.col(base_col)))
                elif target == 'quarter':
                    df = df.withColumn(raw_col, F.quarter(F.col(base_col)))
                elif target == 'year':
                    df = df.withColumn(raw_col, F.year(F.col(base_col)))
                elif target == 'weekofyear':
                    df = df.withColumn(raw_col, F.weekofyear(F.col(base_col)))
                elif target in ('isweekend', 'is_weekend'):
                    # Binary flag — no cyclical encoding needed.
                    df = df.withColumn(
                        raw_col,
                        F.when(F.dayofweek(F.col(base_col)).isin([1, 7]), 1).otherwise(0)
                    )

                # ── Step 2: apply cyclical sin/cos encoding where applicable ─
                if target in CYCLICAL_PERIODS:
                    period = CYCLICAL_PERIODS[target]
                    logger.info(
                        f"Applying cyclical encoding to {raw_col} (period={period})."
                    )
                    df = df.withColumn(
                        f'{raw_col}_sin',
                        F.sin(2 * math.pi * F.col(raw_col) / period)
                    ).withColumn(
                        f'{raw_col}_cos',
                        F.cos(2 * math.pi * F.col(raw_col) / period)
                    )
                    # Drop the raw integer so the model only sees the
                    # continuous cyclical representation.
                    df = df.drop(raw_col)

        return df

    def extract_binary_features(self, df: DataFrame) -> DataFrame:
        """Vectorizes retail flag indicators from operational strings to strict binary mappings."""
        logger.info("Transforming corporate structural indicator flags to binary arrays...")
        binary_config = self.config['Features']['categorical_encoding'].get('binary_encoding', {})
        mapping = binary_config.get('map', {'Y': 1, 'N': 0})
        columns = binary_config.get('columns', [])
        true_val = list(mapping.keys())[0] if mapping else 'Y'
        true_target = mapping.get(true_val, 1)
        false_target = 0 if true_target == 1 else 1
        for col_name in columns:
            if col_name in df.columns:
                df = df.withColumn(
                    col_name,
                    F.when(
                        F.upper(F.trim(F.col(col_name))) == str(true_val).upper(),
                        true_target
                    ).otherwise(false_target)
                )
        return df

    def scale_features(self, df: DataFrame) -> DataFrame:
        """
        Executes distributed feature normalization.

        Execution order:
          1. log1p on the target (sales_unit_qty) to stabilise its skewed
             distribution, then immediately z-score it so it lives on the
             same scale as every other real-valued covariate.
          2. Standard (z-score) scaling on all remaining continuous features
             listed under numerical_scaling.columns — excluding binary flags
             (PERISHABLE, snap_*) which must stay as 0/1 integers.
        """
        covariates = self.config['Features'].get('tft_covariates', {})
        transformations = covariates.get('transformations', {})

        # ── 1. Target: log1p then z-score ────────────────────────────────────
        target_config = transformations.get('target_scaling', {})
        target_col = target_config.get('column')
        if target_col and target_col in df.columns and target_config.get('method') == 'log1p':
            logger.info(f'Applying log1p to target column: {target_col}')
            df = df.withColumn(target_col, F.log1p(F.col(target_col).cast('double')))

        # ── 2. Standard scaling for continuous features ───────────────────────
        # Binary flag columns must NOT be standard-scaled; doing so destroys
        # the 0/1 semantics that the TFT embedding layers depend on.
        binary_cols = set(
            self.config['Features']['categorical_encoding']
            .get('binary_encoding', {})
            .get('columns', [])
        )
        # snap_* and PERISHABLE are binary flags even though they may appear
        # elsewhere in the config — guard them explicitly.
        binary_cols.update({'snap_CA', 'snap_TX', 'snap_WI', 'PERISHABLE'})

        numeric_config = transformations.get('numerical_scaling', {})
        if numeric_config and numeric_config.get('method') == 'standard':
            # Build the full scaling list: configured columns PLUS the target
            # (post-log1p), minus any binary flags.
            configured_cols = numeric_config.get('columns', [])
            scaling_candidate = configured_cols + ([target_col] if target_col else [])
            scaling_cols = [
                c for c in scaling_candidate
                if c in df.columns and c not in binary_cols
            ]
            # Deduplicate while preserving order.
            seen = set()
            scaling_cols = [c for c in scaling_cols if not (c in seen or seen.add(c))]

            logger.info(
                f"Computing distributed statistics (Mean, StdDev) for "
                f"{len(scaling_cols)} features..."
            )
            agg_exprs = []
            for c in scaling_cols:
                agg_exprs.append(F.mean(c).alias(f'{c}_avg'))
                agg_exprs.append(F.stddev(c).alias(f'{c}_std'))
            stats = df.groupBy().agg(*agg_exprs).collect()[0]

            for c in scaling_cols:
                mean_val = stats[f'{c}_avg']
                std_val  = stats[f'{c}_std']
                if std_val and std_val != 0:
                    df = df.withColumn(
                        c, (F.col(c) - F.lit(mean_val)) / F.lit(std_val)
                    )
                else:
                    logger.warning(
                        f'Invariance detected in column {c} (StdDev=0). '
                        f'Nullifying variance drift.'
                    )
                    df = df.withColumn(c, F.col(c) - F.lit(mean_val))

        return df

    def encode_categorical_features(self, df: DataFrame) -> DataFrame:
        logger.info('Executing label encoding for Categorical variables..')
        category_config = self.config['Features'].get('categorical_encoding', {})
        if category_config.get('method') == 'label':
            categorical_cols = category_config.get('columns', [])
            # Only encode columns that actually exist in the dataframe;
            # columns listed in both categorical_encoding and drop_columns
            # (e.g. zone_name) will already be absent — skip silently.
            valid_cols = [c for c in categorical_cols if c in df.columns]
            if valid_cols:
                logger.info(f'Applying StringIndexer to {len(valid_cols)} categorical columns..')
                out_cols = [f'{c}_idx' for c in valid_cols]
                indexer = StringIndexer(inputCols=valid_cols, outputCols=out_cols, handleInvalid='keep')
                model = indexer.fit(df)
                df = model.transform(df)
                for c in valid_cols:
                    df = df.withColumn(c, F.col(f'{c}_idx').cast('integer')).drop(f'{c}_idx')
        return df

    def execute_pipeline(self) -> None:
        source_uri, target_uri = self.get_table_urls()
        logger.info(f'Ingesting working dataset from Source Catalog Layer: {source_uri}')

        df_cleaned = self.spark.read.table(source_uri)
        df_transformed = df_cleaned.transform(self.extract_datetime_features) \
            .transform(self.extract_binary_features) \
            .transform(self.scale_features) \
            .transform(self.encode_categorical_features)

        logger.info(f'Writing transformed dataset to Target Catalog Layer: {target_uri}')
        df_transformed.write.format('delta') \
            .mode('overwrite') \
            .option('overwriteSchema', 'true') \
            .option('delta.columnMapping.mode', 'name') \
            .option('delta.autooptimize.optimizeWrite', 'true') \
            .option('delta.autoOptimize.autoCompact', 'true') \
            .saveAsTable(target_uri)
        logger.info("Data transformation stage completed successfully.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='TFT Data Transformation Pipeline')
    default_config_path = str(script_dir.parent / 'config/config.yaml')
    parser.add_argument('--config', type=str, default=default_config_path)
    args = parser.parse_args()
    transformer = DataTransformation(args.config)
    transformer.execute_pipeline()