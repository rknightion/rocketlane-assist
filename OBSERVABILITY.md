# Observability Setup Guide

This guide explains how to enable and configure observability for Rocketlane Assist using OpenTelemetry (backend) and Grafana Faro (frontend).

## Overview

The application includes built-in observability features:
- **Backend**: OpenTelemetry tracing with automatic instrumentation for FastAPI and HTTP clients
- **Frontend**: Grafana Faro for Real User Monitoring (RUM) with error tracking and performance metrics
- **Trace Correlation**: Frontend and backend traces are automatically correlated using W3C trace context propagation

## Backend Configuration

### Enable Tracing

Set the following environment variables in your `.env` file:

```bash
# Enable tracing
OTEL_TRACING_ENABLED=true

# Configure OTLP endpoint (example for Grafana Cloud)
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-gb-south-1.grafana.net/otlp
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic%20<base64_encoded_user:pass>
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf

# Resource attributes (comma-separated, no quotes)
OTEL_RESOURCE_ATTRIBUTES=service.name=rocketlane-assistant,service.namespace=rocketlane,deployment.environment=production
```

**Important Notes**:
1. Do NOT use quotes around values in `.env` files
2. The space after "Basic" in the Authorization header must be URL-encoded as `%20`
3. Resource attributes should be comma-separated key=value pairs without quotes
4. For HTTP protocol, the application automatically appends `/v1/traces` to the endpoint

### Grafana Cloud Setup

1. Get your OTLP endpoint from Grafana Cloud:
   - Navigate to your Grafana Cloud instance
   - Go to **Connections** → **OpenTelemetry**
   - Copy the OTLP endpoint URL

2. Create authentication header:
   - Username: Your Grafana Cloud instance ID (e.g., `123456`)
   - Password: Your Grafana Cloud API token
   - Encode as Base64: `echo -n "123456:your-api-token" | base64`
   - Use in header: `Authorization=Basic <base64_result>`

### Local Development

For local testing with an OTLP collector:

```bash
OTEL_TRACING_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
```

**Note**: The application no longer outputs traces to the console when `DEBUG_MODE=true`. Traces are only sent to the configured OTLP endpoint to avoid cluttering debug logs.

## Frontend Configuration

Grafana Faro is pre-configured in the frontend and automatically initializes when the application starts.

### Configuration Details

- **Collector URL**: `https://faro-collector-prod-gb-south-1.grafana.net/collect/292365ab3438466b8e96120631d3f05f`
- **App Name**: `rocketlane-assistant`
- **Environment**: `production`

The frontend automatically:
- Captures errors and exceptions
- Tracks page navigation and user interactions
- Measures Web Vitals (performance metrics)
- Propagates trace context to backend API calls

## Trace Correlation

Frontend and backend traces are automatically correlated:

1. Frontend creates a trace for user interactions
2. Trace context is propagated via HTTP headers (`traceparent`)
3. Backend continues the trace, linking frontend and backend operations
4. Both traces share the same trace ID in Grafana

### Viewing Correlated Traces

In Grafana Cloud:
1. Navigate to **Explore** → **Traces**
2. Search by trace ID to see the full transaction
3. View the timeline showing both frontend and backend spans

## What's Captured

### Backend Traces
- HTTP request/response cycles
- Database queries (if configured)
- External API calls (Rocketlane, OpenAI, Anthropic)
- Custom spans for business logic
- Errors and exceptions with stack traces

### Frontend Observability
- Page loads and navigation
- API request performance
- JavaScript errors and exceptions
- User interactions
- Web Vitals (LCP, FID, CLS)
- Custom events

## Debugging

### Backend
- Check logs for OpenTelemetry initialization messages
- Verify OTLP endpoint connectivity
- Look for error messages about failed trace exports
- Ensure Authorization header has proper URL encoding (space as %20)
- When DEBUG_MODE=true, OTEL exporter errors are logged at DEBUG level
- Common errors:
  - `404 page not found`: Check if endpoint needs `/v1/traces` appended
  - `StatusCode.UNAVAILABLE`: Check if using gRPC with HTTPS endpoint
  - `Invalid metadata`: Verify Authorization header is URL-encoded

### Frontend
- Open browser console to see Faro initialization message
- Check Network tab for requests to Faro collector
- Use browser DevTools Performance tab to correlate with Faro data

## Best Practices

1. **Sampling**: Consider implementing sampling for high-traffic production environments
2. **Sensitive Data**: Avoid logging sensitive information in spans
3. **Custom Attributes**: Add relevant business context to spans
4. **Error Handling**: Ensure errors are properly captured with context

## Troubleshooting

### No Traces Appearing
1. Verify `OTEL_TRACING_ENABLED=true`
2. Check OTLP endpoint URL is correct
3. Verify authentication credentials
4. Check network connectivity to Grafana Cloud

### Frontend Not Sending Data
1. Check browser console for errors
2. Verify Faro collector URL is accessible
3. Check for ad blockers or privacy extensions

### Traces Not Correlated
1. Ensure both frontend and backend are sending to same Grafana instance
2. Verify trace propagation headers are being sent
3. Check for proxy or load balancer interference with headers