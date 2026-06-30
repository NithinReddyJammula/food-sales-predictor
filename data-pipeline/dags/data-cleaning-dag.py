import os
from datetime import datetime,timedelta
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator

default_args={
    'owner':'nithinreddyjammula',
    'depends_on_past': False,
    'email_on_failure':True,
    'email_on_retry': False,
    'retries':1,
    'retry_delay':timedelta(minutes=5)}

with DAG(dag_id='tft_fresh_food_data_cleaning',default_args=default_args,
    description='Orchestrates the TFT fresh food inventory data cleaning pipeline on Databricks',
    schedule_interval=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['tft', 'gold_layer', 'forecasting']) as dag:
    run_data_cleaning = DatabricksRunNowOperator(
        task_id="execute_spark_cleaning_pipeline",
        databricks_conn_id="databricks_default",
        job_id=int(os.getenv('DATABRICKS_JOB_ID', '495996754923268')))
