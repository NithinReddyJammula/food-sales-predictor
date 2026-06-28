# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Ingestion Notebook
# MAGIC Ingests raw device sensor telemetry data and writes it to the Bronze Delta table.

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, rand, expr

spark = SparkSession.builder.getOrCreate()

# COMMAND ----------

# Simulate ingestion by generating synthetic raw data
# In production, this would read from an external source like ADLS, S3, or Kafka
raw_df = spark.range(1, 1000) \
    .withColumn("device_id", expr("int(rand() * 10) + 1")) \
    .withColumn("temperature", expr("rand() * 40 + 10")) \
    .withColumn("humidity", expr("rand() * 60 + 30")) \
    .withColumn("timestamp", expr("current_timestamp() - cast(rand() * 3600 as interval second)")) \
    .withColumn("raw_payload", expr("to_json(struct(*))"))

# Add metadata columns for lineage/audit
bronze_df = raw_df.select("device_id", "timestamp", "raw_payload") \
    .withColumn("ingested_at", current_timestamp()) \
    .withColumn("source_file", expr("'synthetic_sensor_stream'"))

# COMMAND ----------

# Save to Bronze Delta table
dbName = "telemetry_db"
spark.sql(f"CREATE DATABASE IF NOT EXISTS {dbName}")
spark.sql(f"USE {dbName}")

bronze_df.write \
    .format("delta") \
    .mode("append") \
    .saveAsTable("bronze_sensor_data")

print("Successfully ingested raw telemetry data into bronze_sensor_data.")