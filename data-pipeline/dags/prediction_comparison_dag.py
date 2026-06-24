"""
Daily Prediction Comparison DAG
Runs daily to compare yesterday's AI predictions with actual sales.
Generates comparison metrics and drift reports.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.redshift_sql import RedshiftSQLHook
import logging

logger = logging.getLogger(__name__)

default_args = {
    "owner": "food-sales-team",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2026, 1, 1),
}

REDSHIFT_CONN_ID = "redshift_default"


def compare_daily_predictions(**context):
    """Compare yesterday's predictions vs actual sales."""
    execution_date = context["execution_date"]
    yesterday = (execution_date - timedelta(days=1)).strftime("%Y-%m-%d")

    hook = RedshiftSQLHook(redshift_conn_id=REDSHIFT_CONN_ID)

    # Insert comparison records
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
            COALESCE(s.total_quantity, 0),
            p.predicted_quantity - COALESCE(s.total_quantity, 0),
            CASE
                WHEN COALESCE(s.total_quantity, 0) = 0 AND p.predicted_quantity = 0 THEN 100.0
                WHEN COALESCE(s.total_quantity, 0) = 0 THEN 0.0
                ELSE GREATEST(0, 100.0 - ABS(
                    (p.predicted_quantity - s.total_quantity)::FLOAT
                    / s.total_quantity * 100
                ))
            END,
            p.model_version
        FROM predictions p
        LEFT JOIN sales_by_slot s
            ON p.date = s.date
            AND p.prediction_slot = s.prediction_slot
            AND p.item_type = s.item_type
            AND p.item_subtype = s.item_subtype
        WHERE p.date = '{yesterday}'
        AND NOT EXISTS (
            SELECT 1 FROM prediction_comparison pc
            WHERE pc.date = p.date
            AND pc.prediction_slot = p.prediction_slot
            AND pc.item_type = p.item_type
            AND pc.item_subtype = p.item_subtype
        )
    """
    hook.run(comparison_sql)

    # Log summary
    summary = hook.get_first(f"""
        SELECT
            COUNT(*) as total_comparisons,
            AVG(accuracy_pct) as avg_accuracy,
            MIN(accuracy_pct) as min_accuracy,
            MAX(accuracy_pct) as max_accuracy
        FROM prediction_comparison
        WHERE date = '{yesterday}'
    """)

    if summary:
        logger.info(
            f"Daily comparison for {yesterday}: "
            f"{summary[0]} comparisons, "
            f"avg accuracy: {summary[1]:.1f}%, "
            f"range: {summary[2]:.1f}% - {summary[3]:.1f}%"
        )

    context["ti"].xcom_push(key="comparison_date", value=yesterday)
    context["ti"].xcom_push(
        key="avg_accuracy", value=float(summary[1]) if summary and summary[1] else 0
    )


def check_drift_alert(**context):
    """Check if prediction accuracy has drifted below threshold."""
    avg_accuracy = context["ti"].xcom_pull(
        key="avg_accuracy", task_ids="compare_predictions"
    )
    comparison_date = context["ti"].xcom_pull(
        key="comparison_date", task_ids="compare_predictions"
    )

    DRIFT_THRESHOLD = 70.0  # Alert if accuracy drops below 70%

    if avg_accuracy < DRIFT_THRESHOLD:
        logger.warning(
            f"DRIFT ALERT: Average accuracy for {comparison_date} is {avg_accuracy}% "
            f"(threshold: {DRIFT_THRESHOLD}%). Consider early retraining."
        )
        # Could trigger an email or Slack notification here
    else:
        logger.info(
            f"Accuracy for {comparison_date} is {avg_accuracy}% - within acceptable range"
        )


with DAG(
    dag_id="daily_prediction_comparison",
    default_args=default_args,
    description="Daily comparison of predictions vs actual sales",
    schedule_interval="0 3 * * *",  # 3 AM daily
    catchup=False,
    max_active_runs=1,
    tags=["comparison", "daily", "food-sales"],
) as dag:

    compare = PythonOperator(
        task_id="compare_predictions",
        python_callable=compare_daily_predictions,
    )

    check_drift = PythonOperator(
        task_id="check_drift_alert",
        python_callable=check_drift_alert,
    )

    compare >> check_drift
