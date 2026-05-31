import typing

import careshield.contracts.schemas as schemas


TraceStatus = typing.Literal["ok", "blocked", "warning", "error"]


class Trace:
    """Collect request pipeline events for debugging and audit."""

    def __init__(self) -> None:
        """Create an empty trace."""
        self.events: list[schemas.TraceEvent] = []

    def add(self, *, step: str, status: TraceStatus, detail: str) -> None:
        """Append a trace event.

        :param step: Pipeline step name.
        :param status: Step status.
        :param detail: Human-readable event detail.
        """
        self.events.append(schemas.TraceEvent(step=step, status=status, detail=detail))
