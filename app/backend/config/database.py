from databricks.connect import DatabricksSession
from os import getenv

class DatabricksDb:
    def get_spark_session(self):
        cluster_id=getenv('DATABRICKS_CLUSTER_ID')
        return DatabricksSession.builder.clusterId(cluster_id).getOrCreate()




