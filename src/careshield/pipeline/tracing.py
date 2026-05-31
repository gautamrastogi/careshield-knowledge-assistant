import typing

from careshield import contracts

TraceStatus = typing.Literal["ok", "blocked", "warning", "error"]


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
