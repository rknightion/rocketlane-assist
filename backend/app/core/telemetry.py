"""OpenTelemetry configuration and initialization."""

import logging
import os

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)


def instrument_app(app: FastAPI) -> None:
    """Instrument FastAPI application with OpenTelemetry.

    Args:
        app: FastAPI application instance
    """
    # Check if tracing is enabled
    enabled = os.getenv("OTEL_TRACING_ENABLED", "false").lower() == "true"

    if not enabled:
        logger.info("OpenTelemetry instrumentation is disabled")
        return

    try:
        # Enable OTEL debug logging when DEBUG_MODE is enabled
        if os.getenv("DEBUG_MODE", "false").lower() == "true":
            import logging as py_logging
            # Set OTEL exporter logging to DEBUG to see export errors
            otel_logger = py_logging.getLogger("opentelemetry.exporter.otlp")
            otel_logger.setLevel(py_logging.DEBUG)
            # But don't log individual spans to avoid clutter
            span_logger = py_logging.getLogger("opentelemetry.sdk.trace")
            span_logger.setLevel(py_logging.INFO)

        # The opentelemetry-distro package handles configuration automatically
        # It reads all standard OTEL environment variables

        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app, excluded_urls="/health,/docs,/openapi.json,/redoc")

        # Instrument HTTP client
        HTTPXClientInstrumentor().instrument()

        logger.info("OpenTelemetry instrumentation initialized")

        # Log the configuration for debugging
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if endpoint:
            logger.info(f"OTLP endpoint configured: {endpoint}")

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry instrumentation: {e}", exc_info=True)


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance for manual instrumentation.

    Args:
        name: Name of the tracer (typically __name__)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


def set_span_error(span: trace.Span, exception: Exception) -> None:
    """Set error status on a span.

    Args:
        span: The span to set error on
        exception: The exception that occurred
    """
    span.set_status(Status(StatusCode.ERROR, str(exception)))
    span.record_exception(exception)
