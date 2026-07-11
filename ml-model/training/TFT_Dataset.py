from pyspark.sql import SparkSession, DataFrame
from config.util.azure_config import load_config
from Feature_transformation.DataTransformation import DataTransformation
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class LoadTrainingData:
    def __init__(self):
        self.spark = SparkSession.builder.getOrCreate()
        self.config = load_config()

    # ── Data loading ─────────────────────────────────────────────────────────
    def load_training_data(self) -> DataFrame:
        transformation = DataTransformation(self.config)
        _, transformed_data_location = transformation.get_table_urls()
        try:
            transformed_training_data = self.spark.read.table(transformed_data_location)
            return transformed_training_data
        except Exception as e:
            logger.error(f'Failed to read the table {transformed_data_location} got exception {e}')
            raise

    # ── Dynamic column resolution ─────────────────────────────────────────────
    def resolve_dynamic_columns(self, df: DataFrame) -> None:
        """
        Scans `df.columns` for any column whose name starts with a prefix
        listed under Features.tft_covariates.dynamic_column_prefixes in the
        config, then appends the matched names to the corresponding static
        covariate list in-place.

        Example config entry:
            dynamic_column_prefixes:
              time_varying_known_reals:
                - 'feature_promo_'
        """
        tft_cfg = self.config['Features']['tft_covariates']
        prefix_map: Dict[str, List[str]] = tft_cfg.get('dynamic_column_prefixes', {})

        if not prefix_map:
            logger.info("No dynamic_column_prefixes configured — skipping dynamic column resolution.")
            return

        df_cols = set(df.columns)

        for covariate_list_name, prefixes in prefix_map.items():
            matched: List[str] = []
            for prefix in prefixes:
                found = sorted(c for c in df_cols if c.startswith(prefix))
                if found:
                    logger.info(
                        f"resolve_dynamic_columns: found {len(found)} column(s) "
                        f"matching prefix '{prefix}' → injecting into "
                        f"tft_covariates.{covariate_list_name}")
                    matched.extend(found)
                else:
                    logger.warning(f"resolve_dynamic_columns: no columns found matching "
                        f"prefix '{prefix}' in the transformed dataframe.")

            if matched:
                existing: List[str] = tft_cfg.setdefault(covariate_list_name, [])
                # Avoid duplicates while preserving order.
                seen = set(existing)
                tft_cfg[covariate_list_name] = existing + [c for c in matched if c not in seen]

    # ── Dataset splitting ─────────────────────────────────────────────────────
    def split_training_data(self,transformed_training_data: DataFrame) -> Tuple[DataFrame, DataFrame, DataFrame]:
        # Step 1 — inject OHE and other prefix-matched columns into config.
        self.resolve_dynamic_columns(transformed_training_data)
        max_time_idx=(transformed_training_data.agg({'time_idx':'max'}).collect()[0][0])
        train_end=int(max_time_idx*0.70)
        val_end=int(max_time_idx*0.85)
        train_dataset=transformed_training_data.filter(transformed_training_data.time_idx<=train_end)
        val_dataset=transformed_training_data.filter(transformed_training_data.time_idx<=val_end)
        test_dataset=transformed_training_data.filter(transformed_training_data.time_idx>val_end)
        logger.info(f'Splitting of Dataset completed..')
        train_dataset.write.format('delta').mode('overwrite').option('overwriteSchema','true').option('delta.columnMapping.mode','name').option('delta.autoOptimize.optimizeWrite','true') \
                     .option('delta.autoOptimize.autoCompact','true').saveAsTable('training_dataset')
        return train_dataset, val_dataset, test_dataset

class TFTDataset:
    def __init__(self, config: Dict):
        self.config = config

    def build_dataset(self, df: DataFrame) -> "TimeSeriesDataSet":
        from pytorch_forecasting import TimeSeriesDataSet
        from pytorch_forecasting.data import GroupNormalizer

        # Pandas conversion is typically needed for PyTorch Forecasting
        pdf = df.toPandas() if isinstance(df, DataFrame) else df
        tft_cfg = self.config['Features']['tft_covariates']
        dataset = TimeSeriesDataSet(
            pdf,
            time_idx="time_idx",
            target=self.config['target'],
            group_ids=self.config['group_ids'],
            min_encoder_length=self.config['training'].get('min_encoder_length', 1),
            max_encoder_length=self.config['training']['max_encoder_length'],
            min_prediction_length=self.config['training'].get('min_prediction_length', 1),
            max_prediction_length=self.config['training']['max_prediction_length'],
            # ── 1. Static Covariates ──
            static_categoricals=tft_cfg['static_categoricals'],
            static_reals=tft_cfg['static_reals'],
            # ── 2. Time-Varying Known Inputs ──
            time_varying_known_categoricals=tft_cfg['time_varying_known_categoricals'],
            time_varying_known_reals=tft_cfg['time_varying_known_reals'],
            # ── 3. Time-Varying Unknown Inputs (Past-Observed) ──
            time_varying_unknown_categoricals=tft_cfg['time_varying_unknown_categoricals'],
            time_varying_unknown_reals=tft_cfg['time_varying_unknown_reals'],
            # Target normalizer (e.g. GroupNormalizer or EncoderNormalizer)
            target_normalizer=GroupNormalizer(groups=self.config['group_ids'], transformation="softplus"),
            add_relative_time_idx=True,
            add_target_scales=True,
            add_encoder_length=True)
        return dataset








































