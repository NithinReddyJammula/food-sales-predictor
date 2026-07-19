import os
import sys
import logging
from opentelemetry import trace, _logs
from opentelemetry.trace import get_current_span
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

class Observability:
    _initialized = False
    @staticmethod
    def initialize():
        if Observability._initialized:
            return
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")
        if not endpoint:
            try:
                from config.util.azure_config import load_config
                cfg = load_config()
                otel_cfg = cfg.get('monitoring', {}).get('observability', {}).get('otlp', {})
                endpoint = otel_cfg.get('endpoint')
                headers = otel_cfg.get('headers')
                if endpoint:
                    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint
                if headers:
                    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = headers
            except Exception as e:
                import traceback
                print(f"OTLP config fallback failed: {e}\n{traceback.format_exc()}", file=sys.stderr)
            endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
            headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")

        if not endpoint:
            logging.warning("OTEL_EXPORTER_OTLP_ENDPOINT environment variable is not set. Telemetry export is disabled.")
            Observability._initialized = True
            return

        # Ensure correct signal-specific URLs for OTLP/HTTP protocol
        log_endpoint = endpoint
        if log_endpoint and not log_endpoint.endswith("/v1/logs"):
            log_endpoint = log_endpoint.rstrip("/") + "/v1/logs"
            
        trace_endpoint = endpoint
        if trace_endpoint and not trace_endpoint.endswith("/v1/traces"):
            trace_endpoint = trace_endpoint.rstrip("/") + "/v1/traces"

        # Parse OTLP headers
        headers_dict = {}
        if headers:
            for part in headers.split(","):
                if "=" in part:
                    k, v = part.split("=", 1)
                    headers_dict[k.strip()] = v.strip()

        log_provider = LoggerProvider()
        _logs.set_logger_provider(log_provider)
        log_exporter = OTLPLogExporter(endpoint=log_endpoint, headers=headers_dict)
        log_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        handler = LoggingHandler(level=logging.INFO, logger_provider=log_provider)
        handler.addFilter(TraceContextFilter())
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        if not any(isinstance(h, LoggingHandler) for h in root_logger.handlers):              # avoid duplicate handlers
            root_logger.addHandler(handler)
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
        span_exporter = OTLPSpanExporter(endpoint=trace_endpoint, headers=headers_dict)
        provider.add_span_processor(
            BatchSpanProcessor(span_exporter))
        
        # Store for reference/testing
        Observability.log_provider = log_provider
        Observability.log_exporter = log_exporter
        Observability.trace_provider = provider
        Observability.span_exporter = span_exporter
        Observability._initialized = True
    @staticmethod
    def get_tracer(name: str):
        return trace.get_tracer(name)

class TraceContextFilter(logging.Filter):
    def filter(self,record):
        span=get_current_span()
        span_context=span.get_span_context()
        record.trace_id=format(span_context.trace_id,"032x") if span_context else None
        record.span_id=format(span_context.span_id,"016x") if span_context else None
        return True
























