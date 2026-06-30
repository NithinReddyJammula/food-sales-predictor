import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator

default_args = {
    'owner': 'nithinreddyjammula',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    dag_id='tft_fresh_food_data_transformation',
    default_args=default_args,
    description='Orchestrates the TFT fresh food inventory data transformation pipeline on Databricks',
    schedule_interval=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['tft', 'gold_layer', 'forecasting']
) as dag:

    databricks_cluster_task = {
        'existing_cluster_id': os.getenv('DATABRICKS_CLUSTER_ID', '0527-054752-thnpzgrm'),
        'spark_python_task': {
            'python_file': 'dbfs:/Workspace/Feature_transformation/Data-Transformation.py',
            'parameters': [
                '--config', '/Workspace/Feature_transformation/config.yaml'
            ]
        },
        'libraries': [
            {'pypi': {'package': 'PyYAML==6.0.1'}},
            {'pypi': {'package': 'opentelemetry-api'}},
            {'pypi': {'package': 'opentelemetry-sdk'}},
            {'pypi': {'package': 'opentelemetry-exporter-otlp'}}
        ]
    }

    run_data_transformation = DatabricksSubmitRunOperator(
        task_id='execute_spark_transformation_pipeline',
        databricks_conn_id='databricks_default',
        json=databricks_cluster_task
    )

    run_data_transformation
