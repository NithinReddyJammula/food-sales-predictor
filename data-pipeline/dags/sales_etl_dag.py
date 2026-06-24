"""
Sales ETL to Redshift DAG
Transforms filtered food sales data and loads into Amazon Redshift.
Runs hourly to batch-process accumulated 15-minute data.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.redshift_sql import RedshiftSQLHook
from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
import json
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

AZURE_CONTAINER = "pos-data"
AZURE_CONN_ID = "azure_data_lake"
REDSHIFT_CONN_ID = "redshift_default"

# Redshift table DDL
CREATE_TABLES_SQL = """
-- Sales transactions table
CREATE TABLE IF NOT EXISTS food_sales (
    id BIGINT IDENTITY(1,1),
    transaction_id VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    date DATE NOT NULL,
    hour INTEGER NOT NULL,
    prediction_slot INTEGER NOT NULL,
    item_type VARCHAR(64) NOT NULL,
    item_subtype VARCHAR(64) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    category VARCHAR(64),
    pos_terminal_id VARCHAR(32),
    store_id VARCHAR(32),
    created_at TIMESTAMP DEFAULT GETDATE()
)
DISTSTYLE KEY
DISTKEY (item_type)
SORTKEY (date, prediction_slot, item_type);

-- Aggregated sales by prediction slot
CREATE TABLE IF NOT EXISTS sales_by_slot (
    id BIGINT IDENTITY(1,1),
    date DATE NOT NULL,
    prediction_slot INTEGER NOT NULL,
    slot_start VARCHAR(5) NOT NULL,
    slot_end VARCHAR(5) NOT NULL,
    item_type VARCHAR(64) NOT NULL,
    item_subtype VARCHAR(64) NOT NULL,
    total_quantity INTEGER NOT NULL DEFAULT 0,
    total_revenue DECIMAL(10,2) DEFAULT 0,
    transaction_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT GETDATE(),
    UNIQUE (date, prediction_slot, item_type, item_subtype)
)
DISTSTYLE KEY
DISTKEY (item_type)
SORTKEY (date, prediction_slot);

-- AI predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id BIGINT IDENTITY(1,1),
    date DATE NOT NULL,
    prediction_slot INTEGER NOT NULL,
    slot_start VARCHAR(5) NOT NULL,
    slot_end VARCHAR(5) NOT NULL,
    item_type VARCHAR(64) NOT NULL,
    item_subtype VARCHAR(64) NOT NULL,
    predicted_quantity INTEGER NOT NULL,
    model_version VARCHAR(32),
    created_at TIMESTAMP DEFAULT GETDATE(),
    UNIQUE (date, prediction_slot, item_type, item_subtype)
)
DISTSTYLE KEY
DISTKEY (item_type)
SORTKEY (date, prediction_slot);

-- Prediction vs Actuals comparison
CREATE TABLE IF NOT EXISTS prediction_comparison (
    id BIGINT IDENTITY(1,1),
    date DATE NOT NULL,
    prediction_slot INTEGER NOT NULL,
    item_type VARCHAR(64) NOT NULL,
    item_subtype VARCHAR(64) NOT NULL,
    predicted_quantity INTEGER,
    actual_quantity INTEGER,
    difference INTEGER,
    accuracy_pct DECIMAL(5,2),
    model_version VARCHAR(32),
    created_at TIMESTAMP DEFAULT GETDATE()
)
DISTSTYLE KEY
DISTKEY (item_type)
SORTKEY (date, prediction_slot);

-- Monthly retraining batches
CREATE TABLE IF NOT EXISTS retrain_batches (
    id BIGINT IDENTITY(1,1),
    batch_month VARCHAR(7) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_records BIGINT,
    model_version_before VARCHAR(32),
    model_version_after VARCHAR(32),
    avg_accuracy_before DECIMAL(5,2),
    avg_accuracy_after DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT GETDATE()
);
"""


def ensure_tables(**context):
    """Create Redshift tables if they don't exist."""
    hook = RedshiftSQLHook(redshift_conn_id=REDSHIFT_CONN_ID)
    hook.run(CREATE_TABLES_SQL)
    logger.info("Ensured all Redshift tables exist")


def fetch_processed_data(**context):
    """Fetch processed food sales data from Azure Data Lake for the current hour."""
    execution_date = context["execution_date"]

    hook = WasbHook(wasb_conn_id=AZURE_CONN_ID)
    all_transactions = []

    # Fetch all 15-minute batches for the current hour (4 batches)
    for minute in [0, 15, 30, 45]:
        blob_path = (
            f"processed/food-sales/{execution_date.year}/"
            f"{execution_date.month:02d}/"
            f"{execution_date.day:02d}/"
            f"{execution_date.hour:02d}_{minute:02d}/"
            f"food_sales.json"
        )
        try:
            data = hook.read_file(AZURE_CONTAINER, blob_path)
            transactions = json.loads(data)
            all_transactions.extend(transactions)
            logger.info(f"Fetched {len(transactions)} records from {blob_path}")
        except Exception as e:
            logger.warning(f"No data at {blob_path}: {e}")

    logger.info(f"Total transactions fetched for hour: {len(all_transactions)}")
    context["ti"].xcom_push(key="hourly_transactions", value=all_transactions)
    return all_transactions


def calculate_prediction_slot(hour):
    """Calculate the prediction slot (1-12) from hour (0-23)."""
    return (hour // 2) + 1


def transform_for_redshift(**context):
    """Transform transaction data for Redshift insertion."""
    transactions = context["ti"].xcom_pull(
        key="hourly_transactions", task_ids="fetch_processed_data"
    )
    execution_date = context["execution_date"]

    if not transactions:
        logger.warning("No transactions to transform")
        return []

    transformed = []
    for txn in transactions:
        from datetime import datetime as dt
        txn_timestamp = dt.fromisoformat(txn["timestamp"])
        slot = calculate_prediction_slot(txn_timestamp.hour)

        transformed.append({
            "transaction_id": txn["transaction_id"],
            "timestamp": txn["timestamp"],
            "date": txn_timestamp.strftime("%Y-%m-%d"),
            "hour": txn_timestamp.hour,
            "prediction_slot": slot,
            "item_type": txn["item_type"],
            "item_subtype": txn["item_subtype"],
            "quantity": txn["quantity"],
            "unit_price": txn.get("unit_price", 0),
            "total_price": txn.get("total_price", 0),
            "category": txn["category"],
            "pos_terminal_id": txn.get("pos_terminal_id"),
            "store_id": txn.get("store_id"),
        })

    context["ti"].xcom_push(key="transformed_data", value=transformed)
    logger.info(f"Transformed {len(transformed)} records")
    return transformed


def load_to_redshift(**context):
    """Load transformed data into Redshift food_sales table."""
    transformed = context["ti"].xcom_pull(
        key="transformed_data", task_ids="transform_data"
    )

    if not transformed:
        logger.warning("No data to load")
        return

    hook = RedshiftSQLHook(redshift_conn_id=REDSHIFT_CONN_ID)

    insert_sql = """
    INSERT INTO food_sales (
        transaction_id, timestamp, date, hour, prediction_slot,
        item_type, item_subtype, quantity, unit_price, total_price,
        category, pos_terminal_id, store_id
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    rows = [
        (
            r["transaction_id"], r["timestamp"], r["date"], r["hour"],
            r["prediction_slot"], r["item_type"], r["item_subtype"],
            r["quantity"], r["unit_price"], r["total_price"],
            r["category"], r["pos_terminal_id"], r["store_id"],
        )
        for r in transformed
    ]

    hook.insert_rows("food_sales", rows)
    logger.info(f"Loaded {len(rows)} records to Redshift food_sales table")


def update_slot_aggregates(**context):
    """Update the sales_by_slot aggregate table."""
    transformed = context["ti"].xcom_pull(
        key="transformed_data", task_ids="transform_data"
    )

    if not transformed:
        return

    hook = RedshiftSQLHook(redshift_conn_id=REDSHIFT_CONN_ID)

    # Aggregate by date, slot, item_type, item_subtype
    aggregates = {}
    for r in transformed:
        key = (r["date"], r["prediction_slot"], r["item_type"], r["item_subtype"])
        if key not in aggregates:
            slot_num = r["prediction_slot"]
            aggregates[key] = {
                "date": r["date"],
                "prediction_slot": slot_num,
                "slot_start": f"{(slot_num - 1) * 2:02d}:00",
                "slot_end": f"{slot_num * 2:02d}:00" if slot_num < 12 else "00:00",
                "item_type": r["item_type"],
                "item_subtype": r["item_subtype"],
                "total_quantity": 0,
                "total_revenue": 0,
                "transaction_count": 0,
            }
        aggregates[key]["total_quantity"] += r["quantity"]
        aggregates[key]["total_revenue"] += r["total_price"]
        aggregates[key]["transaction_count"] += 1

    # Upsert aggregates
    for agg in aggregates.values():
        upsert_sql = f"""
        DELETE FROM sales_by_slot
        WHERE date = '{agg['date']}'
          AND prediction_slot = {agg['prediction_slot']}
          AND item_type = '{agg['item_type']}'
          AND item_subtype = '{agg['item_subtype']}';

        INSERT INTO sales_by_slot (
            date, prediction_slot, slot_start, slot_end,
            item_type, item_subtype,
            total_quantity, total_revenue, transaction_count
        ) VALUES (
            '{agg['date']}', {agg['prediction_slot']},
            '{agg['slot_start']}', '{agg['slot_end']}',
            '{agg['item_type']}', '{agg['item_subtype']}',
            {agg['total_quantity']}, {agg['total_revenue']},
            {agg['transaction_count']}
        );
        """
        hook.run(upsert_sql)

    logger.info(f"Updated {len(aggregates)} slot aggregates in Redshift")


with DAG(
    dag_id="sales_etl_to_redshift",
    default_args=default_args,
    description="ETL food sales to Redshift every hour",
    schedule_interval="@hourly",
    catchup=False,
    max_active_runs=1,
    tags=["etl", "redshift", "food-sales"],
) as dag:

    create_tables = PythonOperator(
        task_id="ensure_tables",
        python_callable=ensure_tables,
    )

    fetch_data = PythonOperator(
        task_id="fetch_processed_data",
        python_callable=fetch_processed_data,
    )

    transform = PythonOperator(
        task_id="transform_data",
        python_callable=transform_for_redshift,
    )

    load = PythonOperator(
        task_id="load_to_redshift",
        python_callable=load_to_redshift,
    )

    update_aggs = PythonOperator(
        task_id="update_slot_aggregates",
        python_callable=update_slot_aggregates,
    )

    create_tables >> fetch_data >> transform >> [load, update_aggs]
