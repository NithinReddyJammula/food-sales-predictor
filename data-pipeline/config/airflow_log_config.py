"""
airflow_log_config.py
─────────────────────
Custom Airflow logging configuration that extends the default Airflow local setting
logging config dictionary with our OpenTelemetry OTLP log exporter.

This is loaded by Airflow using the environment variable:
    AIRFLOW__LOGGING__LOGGING_CONFIG_CLASS=config.airflow_log_config.LOGGING_CONFIG
"""

import os
import logging
from copy import deepcopy
from airflow.config_templates.airflow_local_settings import DEFAULT_LOGGING_CONFIG

# Ensure we start with a clean copy of Airflow's internal config (includes SecretsMasker, etc)
LOGGING_CONFIG = deepcopy(DEFAULT_LOGGING_CONFIG)


def _build_otlp_handler() -> logging.Handler:
    """
    Initialises the OpenTelemetry log provider and returns a LoggingHandler
    for New Relic. Falls back to a NullHandler if the key is missing.
    """
    nr_key = os.getenv("NEW_RELIC_API_KEY")
    if not nr_key:
        return logging.NullHandler()

    try:
        from opentelemetry import _logs
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.sdk.resources import Resource

        resource = Resource.create({
            "service.name": "food-sales-predictor.airflow",
            "deployment.environment": os.getenv("AIRFLOW__CORE__ENV", "production"),
        })

        log_provider = LoggerProvider(resource=resource)
        _logs.set_logger_provider(log_provider)

        exporter = OTLPLogExporter(
            endpoint="https://otlp.nr-data.net:4318/v1/logs",
            headers={"api-key": nr_key},
        )
        log_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

        # Re-use Airflow's built-in secrets masker filter if it exists
        handler = LoggingHandler(level=logging.INFO, logger_provider=log_provider)
        return handler

    except Exception as exc:
        logging.warning("OTLP log handler setup failed: %s", exc)
        return logging.NullHandler()


# Build the handler
_otlp_handler = _build_otlp_handler()

# Register the OTLP handler into the config dict
LOGGING_CONFIG["handlers"]["otlp"] = {
    "()": lambda: _otlp_handler,
    "formatter": "airflow",
}

# Add SecretsMasker filter to the OTLP handler (required by Airflow)
if "mask_secrets" in LOGGING_CONFIG.get("filters", {}):
    LOGGING_CONFIG["handlers"]["otlp"]["filters"] = ["mask_secrets"]

# Attach the OTLP handler to the root logger and Airflow's default loggers
if "handlers" in LOGGING_CONFIG["root"]:
    LOGGING_CONFIG["root"]["handlers"].append("otlp")

if "airflow.task" in LOGGING_CONFIG["loggers"]:
    LOGGING_CONFIG["loggers"]["airflow.task"]["handlers"].append("otlp")

if "airflow.processor" in LOGGING_CONFIG["loggers"]:
    LOGGING_CONFIG["loggers"]["airflow.processor"]["handlers"].append("otlp")

if "flask_appbuilder" in LOGGING_CONFIG["loggers"]:
    LOGGING_CONFIG["loggers"]["flask_appbuilder"]["handlers"].append("otlp")



