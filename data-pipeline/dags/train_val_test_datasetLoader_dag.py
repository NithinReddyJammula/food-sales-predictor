import os
from datetime import datetime,timedelta
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator

default_args={
    'owner':'Nithin Reddy Jammula',
    'retries':False,
    'depends_on_past': False,
    'email_on_failure':True,
}

with DAG(dag_id='train_val_test_datasetLoader_dag',default_args=default_args,description='DAG for loading train,val,test datasets',schedule_interval=None,start_date=datetime(2026,1,1),catchup=False,tags=['train_dataset_loader','val_dataset_loader','test_dataset_loader']) as dag:
    workspace_path=os.getenv('DATABRICKS_WORKSPACE_PATH')
    file_path=f'{workspace_path}/ml-model/training/TFT_Dataset.py'
    config_file_path=f"{workspace_path}/data-pipeline/config/config.yaml"
    databricks_cluster_task={
        'existing_cluster_id' : os.getenv('DATABRICKS_CLUSTER_ID'),
        'spark_python_task': {
            'python_file': file_path,
            'parameters': ['--config',config_file_path]
        },
        'spark_env_vars':{
            'OTEL_EXPORTER_OTLP_ENDPOINT': os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'),
            'OTEL_EXPORTER_OTLP_HEADERS': os.getenv('OTEL_EXPORTER_OTLP_HEADERS', '')},
        'libraries': [
            {'pypi': {'package': 'PyYAML==6.0.1'}},
            {'pypi': {'package': 'opentelemetry-api'}},
            {'pypi': {'package': 'opentelemetry-sdk'}},
            {'pypi': {'package': 'opentelemetry-exporter-otlp'}}
        ]
    }
    load_datasets = DatabricksSubmitRunOperator(task_id='load_datasets',databricks_conn_id='databricks_default',json=databricks_cluster_task)

