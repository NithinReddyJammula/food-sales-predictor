# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Cleaning Notebook
# MAGIC Reads raw data from Bronze Delta table, parses payloads, validates quality rules, and writes clean data to Silver.

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp
from pyspark.sql.types import StructType, StructField, IntegerType, DoubleType, TimestampType

spark = SparkSession.builder.getOrCreate()

# COMMAND ----------

# Schema for parsing raw payload
payload_schema = StructType([
    StructField("device_id", IntegerType(), True),
    StructField("temperature", DoubleType(), True),
    StructField("humidity", DoubleType(), True),
    StructField("timestamp", TimestampType(), True)
])

# Read from Bronze Delta table
bronze_df = spark.read.table("telemetry_db.bronze_sensor_data")

# COMMAND ----------

# Parse payload and clean data
cleaned_df = bronze_df \
    .withColumn("parsed_payload", from_json(col("raw_payload"), payload_schema)) \
    .select(
        col("parsed_payload.device_id").alias("device_id"),
        col("parsed_payload.temperature").alias("temperature"),
        col("parsed_payload.humidity").alias("humidity"),
        col("parsed_payload.timestamp").alias("reading_time"),
        col("ingested_at")
    ) \
    .filter(col("device_id").isNotNull()) \
    .filter(col("temperature").between(-10, 100)) # Filter out extreme outliers

# Add processing metadata
silver_df = cleaned_df \
    .withColumn("processed_at", current_timestamp())

# COMMAND ----------

# Write to Silver Delta table
silver_df.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("telemetry_db.silver_sensor_data")

print("Successfully cleaned and wrote data to silver_sensor_data.")