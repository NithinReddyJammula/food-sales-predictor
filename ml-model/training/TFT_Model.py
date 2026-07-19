from TFT_Dataset import TFTDataset, LoadTransformedData
from pyspark.sql import SparkSession , DataFrame

class TimeSeriesDataset:
    def __init__(self):
        self.loader = LoadTransformedData()
        self.config = self.loader.config

    def get_dataset_tables(self):
        catalog = self.config["databricks"]["catalog"]
        schema = self.config["schemas"]["processed"]
        train_table = f"{catalog}.`{schema}`.training_dataset"
        val_table = f"{catalog}.`{schema}`.validation_dataset"
        test_table = f"{catalog}.`{schema}`.test_dataset"
        return train_table, val_table, test_table

    def build_timeseries_datasets(self):
        spark= SparkSession.builder.getOrCreate()
        train_table, val_table, test_table = self.get_dataset_tables()
        train_dataset = spark.read.table(train_table)
        val_dataset= spark.read.table(val_table)
        builder=TFTDataset(self.config)
        train_timeseries_dataset = builder.build_dataset(train_dataset)
        val_timeseries_dataset = builder.build_dataset(val_dataset)
        return train_timeseries_dataset, val_timeseries_dataset

    
