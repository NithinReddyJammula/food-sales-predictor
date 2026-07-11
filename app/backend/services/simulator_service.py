from typing import List
from models.store import Store
from config.database import get_spark_session

class Stores:
    def get_stores(self) -> List[Store]:
        spark=get_spark_session()
        df=spark.sql()

