#!/usr/bin/env python3
"""Test script to verify OpenTelemetry OTLP configuration."""

import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter as GRPCExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as HTTPExporter,
)
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup logging first
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Enable debug logging for OpenTelemetry
logging.getLogger("opentelemetry").setLevel(logging.DEBUG)
logging.getLogger("opentelemetry.exporter").setLevel(logging.DEBUG)
logging.getLogger("opentelemetry.exporter.otlp").setLevel(logging.DEBUG)

# Load environment variables from .env file at project root
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    print(f"Loading environment from: {env_path}")
    load_dotenv(env_path)
else:
    print(f"No .env file found at: {env_path}")

# Print OTEL environment variables for debugging
print("\n=== OTEL Environment Variables ===")
for key, value in os.environ.items():
    if key.startswith("OTEL_"):
        # Mask sensitive data
        if "HEADERS" in key and value:
            # Show partial header for debugging
            masked = value[:30] + "..." if len(value) > 30 else value
            print(f"{key}={masked}")
        else:
            print(f"{key}={value}")


def test_http_exporter():
    """Test OTLP HTTP exporter."""
    print("\n=== Testing HTTP Exporter ===")

    try:
        # Create resource
        resource = Resource.create(
            {
                SERVICE_NAME: "test-service",
                "service.version": "1.0.0",
            }
        )

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Create HTTP exporter
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")

        # For HTTP protocol, append /v1/traces if not already present
        if endpoint and not endpoint.endswith("/v1/traces"):
            traces_endpoint = endpoint.rstrip("/") + "/v1/traces"
        else:
            traces_endpoint = endpoint or ""

        print(f"Base Endpoint: {endpoint}")
        print(f"Traces Endpoint: {traces_endpoint}")
        print(f"Headers present: {'Yes' if headers else 'No'}")

        # Parse headers if present
        parsed_headers = {}
        if headers:
            for header_pair in headers.split(","):
                if "=" in header_pair:
                    key, value = header_pair.split("=", 1)
                    # URL decode the value
                    import urllib.parse

                    decoded_value = urllib.parse.unquote(value)
                    parsed_headers[key] = decoded_value
                    print(
                        f"Header: {key} = {'***' if key.lower() == 'authorization' else decoded_value[:20] + '...' if len(decoded_value) > 20 else decoded_value}"
                    )

        # Create exporter with explicit configuration
        exporter = HTTPExporter(
            endpoint=traces_endpoint,
            headers=parsed_headers if parsed_headers else None,
        )

        # Add span processor
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

        # Set as global tracer provider
        trace.set_tracer_provider(provider)

        # Create a test span
        tracer = trace.get_tracer("test-tracer")
        with tracer.start_as_current_span("test-span") as span:
            span.set_attribute("test.attribute", "test-value")
            print("Created test span")

        # Force flush to send immediately
        print("Flushing spans...")
        provider.force_flush()

        print("HTTP test completed successfully")

    except Exception as e:
        print(f"HTTP test failed: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


def test_grpc_exporter():
    """Test OTLP gRPC exporter."""
    print("\n=== Testing gRPC Exporter ===")

    try:
        # Enable gRPC debug logging
        grpc_logger = logging.getLogger("grpc")
        grpc_logger.setLevel(logging.DEBUG)
        grpc_logger.addHandler(logging.StreamHandler())

        # Create resource
        resource = Resource.create(
            {
                SERVICE_NAME: "test-service-grpc",
                "service.version": "1.0.0",
            }
        )

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Get endpoint and convert to gRPC format if needed
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
        headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")

        if endpoint.startswith("https://"):
            # Convert HTTPS endpoint to gRPC format
            grpc_endpoint = endpoint.replace("https://", "").replace("/otlp", "")
            print(f"Converting endpoint from {endpoint} to {grpc_endpoint}")
        else:
            grpc_endpoint = endpoint

        print(f"gRPC Endpoint: {grpc_endpoint}")
        print(f"Headers present: {'Yes' if headers else 'No'}")

        # Parse headers for gRPC
        metadata = []
        if headers:
            for header_pair in headers.split(","):
                if "=" in header_pair:
                    key, value = header_pair.split("=", 1)
                    # URL decode the value
                    import urllib.parse

                    decoded_value = urllib.parse.unquote(value)
                    metadata.append((key.lower(), decoded_value))
                    print(
                        f"gRPC Metadata: {key.lower()} = {'***' if key.lower() == 'authorization' else decoded_value[:20] + '...'}"
                    )

        # Create gRPC exporter with headers
        exporter = GRPCExporter(
            endpoint=grpc_endpoint,
            headers=tuple(metadata) if metadata else None,
            insecure=False,  # Use TLS
        )

        # Add span processor
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

        # Set as global tracer provider
        trace.set_tracer_provider(provider)

        # Create a test span
        tracer = trace.get_tracer("test-tracer-grpc")
        with tracer.start_as_current_span("test-span-grpc") as span:
            span.set_attribute("test.attribute", "test-value-grpc")
            print("Created test span for gRPC")

        # Force flush
        print("Flushing spans...")
        provider.force_flush()

        print("gRPC test completed successfully")

    except Exception as e:
        print(f"gRPC test failed: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Run OTLP export tests."""
    print("Starting OTLP export tests...")

    # Test HTTP exporter (as configured)
    if os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL") == "http/protobuf":
        test_http_exporter()
    else:
        test_grpc_exporter()

    # Wait a bit for any async operations
    time.sleep(2)

    print("\nTests completed!")


if __name__ == "__main__":
    main()
