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
    'retry_delay': timedelta(minutes=1)
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

    workspace_path = os.getenv('DATABRICKS_WORKSPACE_PATH')
    python_file_path = f"{workspace_path}/data-pipeline/Feature_transformation/DataTransformation.py"
    config_file_path = f"{workspace_path}/data-pipeline/config/config.yaml"

    databricks_cluster_task = {
        'existing_cluster_id': os.getenv('DATABRICKS_CLUSTER_ID'),
        'spark_python_task': {
            'python_file': python_file_path,
            'parameters': [
                '--config', config_file_path
            ]
        },
        'spark_env_vars': {
            'OTEL_EXPORTER_OTLP_ENDPOINT': os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'),
            'OTEL_EXPORTER_OTLP_HEADERS': os.getenv('OTEL_EXPORTER_OTLP_HEADERS', '')
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
