"""
POS Data Sender
Runs as a service on the POS machine to send transaction data
to Azure Data Lake every 15 minutes.
"""

import os
import json
import time
import logging
from datetime import datetime
from azure.storage.blob import BlobServiceClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
CONTAINER_NAME = os.getenv("AZURE_CONTAINER", "pos-data")
STORE_ID = os.getenv("STORE_ID", "store-001")
BATCH_INTERVAL_SECONDS = 15 * 60  # 15 minutes


class POSDataSender:
    """Collects and sends POS transaction data to Azure Data Lake every 15 minutes."""

    def __init__(self):
        self.blob_service = BlobServiceClient.from_connection_string(
            AZURE_CONNECTION_STRING
        )
        self.container_client = self.blob_service.get_container_client(CONTAINER_NAME)
        self.transaction_buffer = []

    def add_transaction(self, transaction):
        """Add a transaction to the buffer."""
        transaction["store_id"] = STORE_ID
        transaction["timestamp"] = datetime.utcnow().isoformat()
        self.transaction_buffer.append(transaction)

    def flush_to_datalake(self):
        """Send buffered transactions to Azure Data Lake."""
        if not self.transaction_buffer:
            logger.info("No transactions to send")
            return

        now = datetime.utcnow()
        blob_path = (
            f"raw/pos/{now.year}/{now.month:02d}/{now.day:02d}/"
            f"{now.hour:02d}/{(now.minute // 15) * 15:02d}/transactions.json"
        )

        data = json.dumps(self.transaction_buffer, indent=2)

        blob_client = self.container_client.get_blob_client(blob_path)
        blob_client.upload_blob(data, overwrite=True)

        logger.info(
            f"Sent {len(self.transaction_buffer)} transactions to {blob_path}"
        )
        self.transaction_buffer = []

    def run(self):
        """Main loop — flushes every 15 minutes."""
        logger.info(f"POS Data Sender started for store {STORE_ID}")
        while True:
            time.sleep(BATCH_INTERVAL_SECONDS)
            try:
                self.flush_to_datalake()
            except Exception as e:
                logger.error(f"Failed to flush data: {e}")


# Example usage and transaction format
SAMPLE_TRANSACTION = {
    "transaction_id": "txn_001",
    "pos_terminal_id": "pos_01",
    "category": "food_cooked_instore",
    "item_type": "Item 1",
    "item_subtype": "Item 1a",
    "quantity": 3,
    "unit_price": 5.99,
    "total_price": 17.97,
}

if __name__ == "__main__":
    sender = POSDataSender()
    # In production, transactions are added via POS integration
    # sender.add_transaction(SAMPLE_TRANSACTION)
    sender.run()
