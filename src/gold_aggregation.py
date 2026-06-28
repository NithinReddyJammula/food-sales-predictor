# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Aggregation Notebook
# MAGIC Aggregates metrics from the Silver table to calculate average temperature and humidity per device per hour.

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, window, avg, current_timestamp

spark = SparkSession.builder.getOrCreate()

# COMMAND ----------

# Read from Silver Delta table
silver_df = spark.read.table("telemetry_db.silver_sensor_data")

# COMMAND ----------

# Compute hourly aggregates
gold_df = silver_df \
    .groupBy(
        col("device_id"),
        window(col("reading_time"), "1 hour").alias("hour_window")
    ) \
    .agg(
        avg("temperature").alias("avg_temperature"),
        avg("humidity").alias("avg_humidity")
    ) \
    .select(
        col("device_id"),
        col("hour_window.start").alias("window_start"),
        col("hour_window.end").alias("window_end"),
        col("avg_temperature"),
        col("avg_humidity")
    ) \
    .withColumn("aggregated_at", current_timestamp())

# COMMAND ----------

# Write to Gold Delta table
gold_df.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("telemetry_db.gold_sensor_hourly_stats")

print("Successfully aggregated hourly telemetry metrics into gold_sensor_hourly_stats.")