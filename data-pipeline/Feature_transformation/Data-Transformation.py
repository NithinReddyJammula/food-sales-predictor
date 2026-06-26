import logging
import sys
from typing import Dict
import yaml
from pyspark.sql import SparkSession

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(node)s %(filename)s:%(lineno)d - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TFT-Transformation-Pipeline")

class DataTransformation:
    logging.info('dat transformation pipeline started..')

    def __init__(self,config_path):
        self.config_path=config_path
        self.config=self.load_config()
        self.spark=self._init_spark()

    def load_config(self, config_path: str) -> dict:
        logging.info('Loading the Configuration File..')
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logging.info(f'Error loading configuration file from {config_path}')

    def spark(self)->SparkSession:
        














