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

    workspace_path = os.getenv('DATABRICKS_WORKSPACE_PATH', '/Workspace/Users/2102c422-f75d-4b03-bb85-27784ee12c13/.bundle/food-sales-predictor/default/files')
    python_file_path = f"{workspace_path}/data-pipeline/Feature_transformation/Data-Transformation.py"
    config_file_path = f"{workspace_path}/data-pipeline/config/config.yaml"

    databricks_cluster_task = {
        'existing_cluster_id': os.getenv('DATABRICKS_CLUSTER_ID', '0630-020742-js27j99e'),
        'spark_python_task': {
            'python_file': python_file_path,
            'parameters': [
                '--config', config_file_path
            ]
        },
        'spark_env_vars': {
            'OTEL_EXPORTER_OTLP_ENDPOINT': os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'https://in-otel.hyperdx.io'),
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

    run_data_transformation
