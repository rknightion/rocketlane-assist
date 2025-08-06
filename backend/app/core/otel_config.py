"""OpenTelemetry configuration using opentelemetry-distro."""

import logging
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def configure_otel():
    """Configure OpenTelemetry with proper OTLP exporter."""
    # Check if we should configure OTEL
    if os.getenv("OTEL_TRACING_ENABLED", "false").lower() != "true":
        return

    try:
        # Create resource with service information
        # This will merge with OTEL_RESOURCE_ATTRIBUTES from env
        resource = Resource.create(
            {
                SERVICE_NAME: "rocketlane-assistant",
                SERVICE_VERSION: "1.0.0",
            }
        )

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Configure OTLP exporter if endpoint is set
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if endpoint:
            # For HTTP protocol, we need to append the specific signal path
            protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")

            if protocol == "http/protobuf" and not endpoint.endswith("/v1/traces"):
                # Set the traces-specific endpoint for HTTP
                traces_endpoint = endpoint.rstrip("/") + "/v1/traces"
                os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = traces_endpoint
                logger.info(f"Set OTLP traces endpoint: {traces_endpoint}")

            # The OTLPSpanExporter will read environment variables automatically
            # including OTEL_EXPORTER_OTLP_HEADERS and OTEL_EXPORTER_OTLP_PROTOCOL
            exporter = OTLPSpanExporter()
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)
            logger.info(f"Configured OTLP trace exporter for endpoint: {endpoint}")

        # Set as global tracer provider
        trace.set_tracer_provider(provider)
        logger.info("OpenTelemetry tracer provider configured successfully")

    except Exception as e:
        logger.error(f"Failed to configure OpenTelemetry: {e}", exc_info=True)
