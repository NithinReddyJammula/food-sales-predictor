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
        nr_key = os.getenv("NEW_RELIC_API_KEY")
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

        # Fallback to New Relic defaults if NEW_RELIC_API_KEY / NEW_RELIC_LICENSE_KEY is present
        if not endpoint and nr_key:
            endpoint = "https://otlp.nr-data.net:4318"
            os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint

        if not endpoint:
            logging.warning("OTEL_EXPORTER_OTLP_ENDPOINT and NEW_RELIC_API_KEY environment variables are not set. Telemetry export is disabled.")
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

        # Build api-key header from NEW_RELIC_API_KEY if not already present
        if nr_key and not headers_dict.get("api-key"):
            headers_dict["api-key"] = nr_key

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
    @staticmethod
    def shutdown():
        if not Observability._initialized:
            return
        try:
            if hasattr(Observability, "log_provider") and Observability.log_provider:
                Observability.log_provider.shutdown()
        except Exception as e:
            print(f"Error shutting down log provider: {e}", file=sys.stderr)
        try:
            if hasattr(Observability, "trace_provider") and Observability.trace_provider:
                Observability.trace_provider.shutdown()
        except Exception as e:
            print(f"Error shutting down trace provider: {e}", file=sys.stderr)

class TraceContextFilter(logging.Filter):
    def filter(self,record):
        span=get_current_span()
        span_context=span.get_span_context()
        record.trace_id=format(span_context.trace_id,"032x") if span_context else None
        record.span_id=format(span_context.span_id,"016x") if span_context else None
        return True
























