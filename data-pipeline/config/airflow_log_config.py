"""
airflow_log_config.py
─────────────────────
Custom Airflow logging configuration that extends the default file-based handler
with an OpenTelemetry OTLP log handler pointing to New Relic.

Activated via docker-compose environment variable:
    AIRFLOW__LOGGING__LOGGING_CONFIG_CLASS=config.airflow_log_config.LOGGING_CONFIG

The NEW_RELIC_API_KEY environment variable must be set.
All Airflow scheduler, webserver, and task logs will appear in New Relic Logs
under service.name='food-sales-predictor.airflow'.
"""

import os
import logging

# ── Build the OTLP handler at import time so Airflow picks it up ──────────────

def _build_otlp_handler() -> logging.Handler:
    """
    Initialise the OpenTelemetry log provider and return a LoggingHandler that
    ships records to New Relic.  Falls back to a NullHandler if the key is missing
    so Airflow still starts cleanly.
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

        handler = LoggingHandler(level=logging.INFO, logger_provider=log_provider)
        return handler

    except Exception as exc:  # pragma: no cover
        # Gracefully degrade — Airflow must not crash if OTLP setup fails
        logging.getLogger(__name__).warning(
            "OTLP log handler setup failed: %s — falling back to NullHandler", exc
        )
        return logging.NullHandler()


_otlp_handler = _build_otlp_handler()

# ── Airflow LOGGING_CONFIG dict ───────────────────────────────────────────────
# Based on Airflow's default config with an extra "otlp" handler added.

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "airflow": {
            "format": "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
        },
        "airflow_coloured": {
            "()": "airflow.utils.log.colored_log.CustomTTYColoredFormatter",
            "fmt": "%(log_color)s[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s%(reset)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "airflow.utils.log.logging_mixin.RedirectStdHandler",
            "formatter": "airflow_coloured",
            "stream": "sys.stdout",
        },
        "task": {
            "class": "airflow.utils.log.file_task_handler.FileTaskHandler",
            "formatter": "airflow",
            "base_log_folder": os.path.expanduser(
                os.getenv("AIRFLOW__LOGGING__BASE_LOG_FOLDER", "~/airflow/logs")
            ),
            "filename_template": "{{ ti.dag_id }}/{{ ti.task_id }}/{{ ts }}/{{ try_number }}.log",
        },
        "processor": {
            "class": "airflow.utils.log.file_processor_handler.FileProcessorHandler",
            "formatter": "airflow",
            "base_log_folder": os.path.expanduser(
                os.getenv("AIRFLOW__LOGGING__BASE_LOG_FOLDER", "~/airflow/logs")
            ),
            "filename_template": "{{ filename }}",
        },
        # ── New Relic OTLP handler ────────────────────────────────────────────
        "otlp": {
            "()": lambda: _otlp_handler,
            "formatter": "airflow",
        },
    },
    "loggers": {
        "airflow.processor": {
            "handlers": ["processor", "otlp"],
            "level": "INFO",
            "propagate": False,
        },
        "airflow.task": {
            "handlers": ["task", "otlp"],
            "level": "INFO",
            "propagate": False,
        },
        "flask_appbuilder": {
            "handlers": ["console", "otlp"],
            "level": "WARNING",
            "propagate": True,
        },
    },
    "root": {
        "handlers": ["console", "otlp"],
        "level": "INFO",
    },
}
