"""
POS Data Ingestion DAG
Runs every 15 minutes to pull POS transaction data from Azure Data Lake,
filter food sales by category, and prepare for ETL.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
from airflow.providers.microsoft.azure.sensors.wasb import WasbBlobSensor
import json
import logging

logger = logging.getLogger(__name__)

default_args = {
    "owner": "food-sales-team",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "start_date": datetime(2026, 1, 1),
}

FOOD_CATEGORIES = [
    "food_prepared",
    "food_cooked_instore",
    "food_bakery",
    "food_deli",
]

AZURE_CONTAINER = "pos-data"
AZURE_CONN_ID = "azure_data_lake"


def get_blob_path(**context):
    """Generate the blob path based on execution time."""
    execution_date = context["execution_date"]
    blob_path = (
        f"raw/pos/{execution_date.year}/"
        f"{execution_date.month:02d}/"
        f"{execution_date.day:02d}/"
        f"{execution_date.hour:02d}/"
        f"{(execution_date.minute // 15) * 15:02d}/"
        f"transactions.json"
    )
    context["ti"].xcom_push(key="blob_path", value=blob_path)
    logger.info(f"Generated blob path: {blob_path}")
    return blob_path


def fetch_pos_data(**context):
    """Fetch POS transaction data from Azure Data Lake."""
    blob_path = context["ti"].xcom_pull(key="blob_path", task_ids="generate_blob_path")

    hook = WasbHook(wasb_conn_id=AZURE_CONN_ID)

    try:
        blob_data = hook.read_file(AZURE_CONTAINER, blob_path)
        transactions = json.loads(blob_data)
        logger.info(f"Fetched {len(transactions)} transactions from {blob_path}")
        context["ti"].xcom_push(key="raw_transactions", value=transactions)
        return transactions
    except Exception as e:
        logger.error(f"Error fetching POS data: {e}")
        raise


def filter_food_sales(**context):
    """Filter transactions to only include food sales categories."""
    raw_transactions = context["ti"].xcom_pull(
        key="raw_transactions", task_ids="fetch_pos_data"
    )

    if not raw_transactions:
        logger.warning("No transactions to filter")
        return []

    food_transactions = []
    for txn in raw_transactions:
        if txn.get("category") in FOOD_CATEGORIES:
            food_item = {
                "transaction_id": txn["transaction_id"],
                "timestamp": txn["timestamp"],
                "item_type": txn.get("item_type"),          # e.g., "Item 1"
                "item_subtype": txn.get("item_subtype"),      # e.g., "Item 1a"
                "quantity": txn.get("quantity", 1),
                "unit_price": txn.get("unit_price", 0),
                "total_price": txn.get("total_price", 0),
                "category": txn["category"],
                "pos_terminal_id": txn.get("pos_terminal_id"),
                "store_id": txn.get("store_id"),
            }
            food_transactions.append(food_item)

    logger.info(
        f"Filtered {len(food_transactions)} food transactions "
        f"from {len(raw_transactions)} total"
    )
    context["ti"].xcom_push(key="food_transactions", value=food_transactions)
    return food_transactions


def save_filtered_data(**context):
    """Save filtered food sales data back to Azure Data Lake processed path."""
    food_transactions = context["ti"].xcom_pull(
        key="food_transactions", task_ids="filter_food_sales"
    )
    execution_date = context["execution_date"]

    if not food_transactions:
        logger.warning("No food transactions to save")
        return

    processed_path = (
        f"processed/food-sales/{execution_date.year}/"
        f"{execution_date.month:02d}/"
        f"{execution_date.day:02d}/"
        f"{execution_date.hour:02d}_{(execution_date.minute // 15) * 15:02d}/"
        f"food_sales.json"
    )

    hook = WasbHook(wasb_conn_id=AZURE_CONN_ID)
    hook.load_string(
        json.dumps(food_transactions, indent=2),
        AZURE_CONTAINER,
        processed_path,
        overwrite=True,
    )
    logger.info(f"Saved {len(food_transactions)} food transactions to {processed_path}")
    context["ti"].xcom_push(key="processed_path", value=processed_path)


def compute_slot_aggregates(**context):
    """Aggregate food sales into 2-hour prediction slot buckets."""
    food_transactions = context["ti"].xcom_pull(
        key="food_transactions", task_ids="filter_food_sales"
    )
    execution_date = context["execution_date"]

    if not food_transactions:
        return {}

    # Determine current 2-hour slot
    slot_number = (execution_date.hour // 2) + 1
    slot_start = f"{(slot_number - 1) * 2:02d}:00"
    slot_end = f"{slot_number * 2:02d}:00" if slot_number < 12 else "00:00"

    # Aggregate by item_type and item_subtype
    aggregates = {}
    for txn in food_transactions:
        key = f"{txn['item_type']}|{txn['item_subtype']}"
        if key not in aggregates:
            aggregates[key] = {
                "item_type": txn["item_type"],
                "item_subtype": txn["item_subtype"],
                "total_quantity": 0,
                "total_revenue": 0,
                "transaction_count": 0,
                "slot": slot_number,
                "slot_start": slot_start,
                "slot_end": slot_end,
                "date": execution_date.strftime("%Y-%m-%d"),
            }
        aggregates[key]["total_quantity"] += txn["quantity"]
        aggregates[key]["total_revenue"] += txn["total_price"]
        aggregates[key]["transaction_count"] += 1

    context["ti"].xcom_push(key="slot_aggregates", value=list(aggregates.values()))
    logger.info(f"Computed aggregates for slot {slot_number}: {len(aggregates)} items")
    return aggregates


with DAG(
    dag_id="pos_data_ingestion",
    default_args=default_args,
    description="Ingest POS data every 15 min, filter food sales",
    schedule_interval="*/15 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["pos", "ingestion", "food-sales"],
) as dag:

    generate_blob_path = PythonOperator(
        task_id="generate_blob_path",
        python_callable=get_blob_path,
    )

    sense_blob = WasbBlobSensor(
        task_id="sense_blob_arrival",
        container_name=AZURE_CONTAINER,
        blob_name="{{ ti.xcom_pull(key='blob_path', task_ids='generate_blob_path') }}",
        wasb_conn_id=AZURE_CONN_ID,
        timeout=600,
        poke_interval=30,
    )

    fetch_data = PythonOperator(
        task_id="fetch_pos_data",
        python_callable=fetch_pos_data,
    )

    filter_sales = PythonOperator(
        task_id="filter_food_sales",
        python_callable=filter_food_sales,
    )

    save_data = PythonOperator(
        task_id="save_filtered_data",
        python_callable=save_filtered_data,
    )

    compute_aggregates = PythonOperator(
        task_id="compute_slot_aggregates",
        python_callable=compute_slot_aggregates,
    )

    generate_blob_path >> sense_blob >> fetch_data >> filter_sales >> [save_data, compute_aggregates]
