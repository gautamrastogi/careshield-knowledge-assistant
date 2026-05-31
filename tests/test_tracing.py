from careshield import contracts, pipeline


def test_trace_collects_response_events() -> None:
    """Verify response trace events are still collected for API output."""
    trace = pipeline.tracing.Trace()

    trace.add(step="request", status="ok", detail="accepted")

    assert trace.events == [
        contracts.schema.TraceEvent(step="request", status="ok", detail="accepted"),
    ]


def test_otel_span_context_runs_without_exporter() -> None:
    """Verify OpenTelemetry spans are safe when no exporter is configured."""
    with pipeline.tracing.start_span(name="test.span") as span:
        span.set_attribute("test.attribute", "value")

    assert span is not None
