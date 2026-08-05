"""OpenTelemetry tracing configuration with instrumentation."""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import get_settings

settings = get_settings()
tracer = trace.get_tracer(__name__)


def setup_tracking(app) -> None:
    """Configure OpenTelemetry tracing with OTLP exporter."""
    resource = Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": settings.APP_VERSION,
            "deployment.environment": settings.ENVIRONMENT,
        }
    )

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    RedisInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()


def create_span(name: str, attributes: dict | None = None):
    """Decorator for tracing specific functions with custom span."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(name) as span:
                if attributes:
                    span.set_attributes(attributes)
                return await func(*args, **kwargs)

        return wrapper

    return decorator
