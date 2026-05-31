import contextlib
import os
import sys
import typing

import opentelemetry.sdk.trace as otel_sdk_trace
import opentelemetry.sdk.trace.export as otel_export
import opentelemetry.trace as otel_trace
import opentelemetry.trace.span as otel_span
import opentelemetry.trace.status as otel_status

from careshield import contracts

TraceStatus = typing.Literal["ok", "blocked", "warning", "error"]
_TRACER_NAME = "careshield"
_OTEL_CONFIGURED = False


class Trace:
    """Collect request pipeline events for debugging and audit."""

    def __init__(self) -> None:
        """Create an empty trace."""
        self.events: list[contracts.schema.TraceEvent] = []

    def add(self, *, step: str, status: TraceStatus, detail: str) -> None:
        """Append a trace event.

        :param step: Pipeline step name.
        :param status: Step status.
        :param detail: Human-readable event detail.
        """
        self.events.append(contracts.schema.TraceEvent(step=step, status=status, detail=detail))

        # The API response gets a lightweight app trace, while OpenTelemetry
        # receives the same event on the active span for external observability.
        current_span = otel_trace.get_current_span()
        if current_span.is_recording():
            current_span.add_event(
                name=step,
                attributes={
                    "careshield.step.status": status,
                    "careshield.step.detail": detail,
                },
            )


def configure_from_env() -> None:
    """Configure local OpenTelemetry exporting from environment variables."""
    global _OTEL_CONFIGURED
    if _OTEL_CONFIGURED:
        return

    # By default OpenTelemetry is no-op, keeping CLI JSON output clean. Set
    # CARESHIELD_OTEL_CONSOLE=true to print spans to stderr while learning.
    console_enabled = os.getenv(key="CARESHIELD_OTEL_CONSOLE", default="").lower() in {
        "1",
        "true",
        "yes",
    }
    if console_enabled:
        provider = otel_sdk_trace.TracerProvider()
        provider.add_span_processor(
            span_processor=otel_export.SimpleSpanProcessor(
                span_exporter=otel_export.ConsoleSpanExporter(out=sys.stderr),
            )
        )
        otel_trace.set_tracer_provider(tracer_provider=provider)
    _OTEL_CONFIGURED = True


def tracer() -> otel_trace.Tracer:
    """Return the project tracer.

    :return: OpenTelemetry tracer.
    """
    configure_from_env()
    return otel_trace.get_tracer(instrumenting_module_name=_TRACER_NAME)


@contextlib.contextmanager
def start_span(
    *,
    name: str,
    attributes: dict[str, str | int | float | bool] | None = None,
) -> typing.Iterator[otel_span.Span]:
    """Start an OpenTelemetry span and record exceptions.

    :param name: Span name.
    :param attributes: Optional span attributes.
    :return: Active OpenTelemetry span.
    """
    with tracer().start_as_current_span(name=name, attributes=attributes or {}) as span:
        try:
            yield span
        except Exception as exc:
            span.record_exception(exception=exc)
            span.set_status(
                status=otel_status.Status(
                    status_code=otel_status.StatusCode.ERROR,
                    description=str(exc),
                )
            )
            raise
