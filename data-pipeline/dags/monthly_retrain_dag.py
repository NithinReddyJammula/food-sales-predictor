"""
Monthly Retrain DAG
At the end of each month:
1. Creates a training batch from the past month's data
2. Compares AI predictions vs actual sales
3. Retrains the neural network with the new data
4. Deploys the updated model
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.redshift_sql import RedshiftSQLHook
import json
import subprocess
import logging

logger = logging.getLogger(__name__)

default_args = {
    "owner": "food-sales-team",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "start_date": datetime(2026, 1, 1),
}

REDSHIFT_CONN_ID = "redshift_default"
MODEL_DIR = "/opt/ml-model"
MODEL_REGISTRY = "/opt/ml-model/registry"


def create_monthly_batch(**context):
    """Create a training batch from the past month's data."""
    execution_date = context["execution_date"]

    # Calculate the previous month's date range
    first_of_current = execution_date.replace(day=1)
    last_of_previous = first_of_current - timedelta(days=1)
    first_of_previous = last_of_previous.replace(day=1)

    batch_month = first_of_previous.strftime("%Y-%m")
    start_date = first_of_previous.strftime("%Y-%m-%d")
    end_date = last_of_previous.strftime("%Y-%m-%d")

    hook = RedshiftSQLHook(redshift_conn_id=REDSHIFT_CONN_ID)

    # Create batch record
    hook.run(f"""
        INSERT INTO retrain_batches (batch_month, start_date, end_date, status)
        VALUES ('{batch_month}', '{start_date}', '{end_date}', 'processing')
    """)

    # Extract training data
    training_data_sql = f"""
        SELECT
            date,
            prediction_slot,
            item_type,
            item_subtype,
            total_quantity,
            total_revenue,
            transaction_count,
            EXTRACT(DOW FROM date) as day_of_week,
            EXTRACT(MONTH FROM date) as month
        FROM sales_by_slot
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY date, prediction_slot, item_type, item_subtype
    """

    results = hook.get_records(training_data_sql)

    # Get count
    count_result = hook.get_first(f"""
        SELECT COUNT(*) FROM sales_by_slot
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
    """)

    total_records = count_result[0] if count_result else 0

    # Update batch record
    hook.run(f"""
        UPDATE retrain_batches
        SET total_records = {total_records}
        WHERE batch_month = '{batch_month}'
    """)

    context["ti"].xcom_push(key="batch_month", value=batch_month)
    context["ti"].xcom_push(key="start_date", value=start_date)
    context["ti"].xcom_push(key="end_date", value=end_date)
    context["ti"].xcom_push(key="total_records", value=total_records)

    logger.info(
        f"Created monthly batch for {batch_month}: "
        f"{total_records} records ({start_date} to {end_date})"
    )


def compare_predictions_vs_actuals(**context):
    """Compare AI predictions with actual sales for the month."""
    batch_month = context["ti"].xcom_pull(key="batch_month", task_ids="create_batch")
    start_date = context["ti"].xcom_pull(key="start_date", task_ids="create_batch")
    end_date = context["ti"].xcom_pull(key="end_date", task_ids="create_batch")

    hook = RedshiftSQLHook(redshift_conn_id=REDSHIFT_CONN_ID)

    # Compare predictions vs actuals
    comparison_sql = f"""
        INSERT INTO prediction_comparison (
            date, prediction_slot, item_type, item_subtype,
            predicted_quantity, actual_quantity, difference, accuracy_pct,
            model_version
        )
        SELECT
            p.date,
            p.prediction_slot,
            p.item_type,
            p.item_subtype,
            p.predicted_quantity,
            COALESCE(s.total_quantity, 0) as actual_quantity,
            p.predicted_quantity - COALESCE(s.total_quantity, 0) as difference,
            CASE
                WHEN COALESCE(s.total_quantity, 0) = 0 AND p.predicted_quantity = 0 THEN 100.0
                WHEN COALESCE(s.total_quantity, 0) = 0 THEN 0.0
                ELSE GREATEST(0, 100.0 - ABS(
                    (p.predicted_quantity - s.total_quantity)::FLOAT
                    / s.total_quantity * 100
                ))
            END as accuracy_pct,
            p.model_version
        FROM predictions p
        LEFT JOIN sales_by_slot s
            ON p.date = s.date
            AND p.prediction_slot = s.prediction_slot
            AND p.item_type = s.item_type
            AND p.item_subtype = s.item_subtype
        WHERE p.date BETWEEN '{start_date}' AND '{end_date}'
    """
    hook.run(comparison_sql)

    # Calculate average accuracy
    accuracy_result = hook.get_first(f"""
        SELECT AVG(accuracy_pct)
        FROM prediction_comparison
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
    """)

    avg_accuracy = round(accuracy_result[0], 2) if accuracy_result and accuracy_result[0] else 0

    # Update batch record
    hook.run(f"""
        UPDATE retrain_batches
        SET avg_accuracy_before = {avg_accuracy}
        WHERE batch_month = '{batch_month}'
    """)

    context["ti"].xcom_push(key="avg_accuracy_before", value=avg_accuracy)
    logger.info(f"Month {batch_month} average prediction accuracy: {avg_accuracy}%")


def export_training_data(**context):
    """Export training data to a file for the ML model."""
    start_date = context["ti"].xcom_pull(key="start_date", task_ids="create_batch")
    end_date = context["ti"].xcom_pull(key="end_date", task_ids="create_batch")
    batch_month = context["ti"].xcom_pull(key="batch_month", task_ids="create_batch")

    hook = RedshiftSQLHook(redshift_conn_id=REDSHIFT_CONN_ID)

    # Fetch all historical data up to and including this month
    all_data = hook.get_records(f"""
        SELECT
            date,
            prediction_slot,
            item_type,
            item_subtype,
            total_quantity,
            total_revenue,
            transaction_count,
            EXTRACT(DOW FROM date) as day_of_week,
            EXTRACT(MONTH FROM date) as month,
            EXTRACT(WEEK FROM date) as week_of_year
        FROM sales_by_slot
        WHERE date <= '{end_date}'
        ORDER BY date, prediction_slot
    """)

    # Save as JSON for the training script
    training_records = []
    for row in all_data:
        training_records.append({
            "date": str(row[0]),
            "prediction_slot": row[1],
            "item_type": row[2],
            "item_subtype": row[3],
            "total_quantity": row[4],
            "total_revenue": float(row[5]) if row[5] else 0,
            "transaction_count": row[6],
            "day_of_week": row[7],
            "month": row[8],
            "week_of_year": row[9],
        })

    output_path = f"{MODEL_DIR}/training_data_{batch_month}.json"
    with open(output_path, "w") as f:
        json.dump(training_records, f, indent=2)

    context["ti"].xcom_push(key="training_data_path", value=output_path)
    logger.info(f"Exported {len(training_records)} training records to {output_path}")


def retrain_model(**context):
    """Trigger the neural network retraining script."""
    batch_month = context["ti"].xcom_pull(key="batch_month", task_ids="create_batch")
    training_data_path = context["ti"].xcom_pull(
        key="training_data_path", task_ids="export_training_data"
    )

    # Run the training script
    result = subprocess.run(
        [
            "python", f"{MODEL_DIR}/train.py",
            "--data-path", training_data_path,
            "--batch-month", batch_month,
            "--output-dir", f"{MODEL_REGISTRY}/{batch_month}",
        ],
        capture_output=True,
        text=True,
        timeout=3600,  # 1 hour timeout
    )

    if result.returncode != 0:
        logger.error(f"Training failed: {result.stderr}")
        raise Exception(f"Model training failed: {result.stderr}")

    # Parse training output for model version
    new_model_version = f"v_{batch_month.replace('-', '_')}"
    context["ti"].xcom_push(key="new_model_version", value=new_model_version)
    logger.info(f"Model retrained successfully: {new_model_version}")
    logger.info(f"Training stdout: {result.stdout[-500:]}")


def generate_new_predictions(**context):
    """Generate predictions using the newly trained model."""
    batch_month = context["ti"].xcom_pull(key="batch_month", task_ids="create_batch")
    new_model_version = context["ti"].xcom_pull(
        key="new_model_version", task_ids="retrain_model"
    )

    # Run the prediction script for the next month
    result = subprocess.run(
        [
            "python", f"{MODEL_DIR}/predict.py",
            "--model-dir", f"{MODEL_REGISTRY}/{batch_month}",
            "--model-version", new_model_version,
            "--predict-days", "30",  # Next 30 days
        ],
        capture_output=True,
        text=True,
        timeout=1800,
    )

    if result.returncode != 0:
        logger.error(f"Prediction generation failed: {result.stderr}")
        raise Exception(f"Prediction generation failed: {result.stderr}")

    logger.info(f"New predictions generated with model {new_model_version}")


def update_batch_status(**context):
    """Mark the batch as complete and update model version info."""
    batch_month = context["ti"].xcom_pull(key="batch_month", task_ids="create_batch")
    new_model_version = context["ti"].xcom_pull(
        key="new_model_version", task_ids="retrain_model"
    )

    hook = RedshiftSQLHook(redshift_conn_id=REDSHIFT_CONN_ID)
    hook.run(f"""
        UPDATE retrain_batches
        SET status = 'completed',
            model_version_after = '{new_model_version}'
        WHERE batch_month = '{batch_month}'
    """)

    logger.info(f"Batch {batch_month} marked as completed")


with DAG(
    dag_id="monthly_retrain",
    default_args=default_args,
    description="Monthly model retraining pipeline",
    schedule_interval="0 2 1 * *",  # 2 AM on the 1st of each month
    catchup=False,
    max_active_runs=1,
    tags=["ml", "retrain", "monthly"],
) as dag:

    create_batch = PythonOperator(
        task_id="create_batch",
        python_callable=create_monthly_batch,
    )

    compare = PythonOperator(
        task_id="compare_predictions",
        python_callable=compare_predictions_vs_actuals,
    )

    export_data = PythonOperator(
        task_id="export_training_data",
        python_callable=export_training_data,
    )

    retrain = PythonOperator(
        task_id="retrain_model",
        python_callable=retrain_model,
    )

    generate_preds = PythonOperator(
        task_id="generate_predictions",
        python_callable=generate_new_predictions,
    )

    update_status = PythonOperator(
        task_id="update_batch_status",
        python_callable=update_batch_status,
    )

    create_batch >> compare >> export_data >> retrain >> generate_preds >> update_status
