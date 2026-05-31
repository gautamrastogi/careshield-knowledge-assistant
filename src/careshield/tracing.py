from __future__ import annotations

from careshield.schemas import TraceEvent


class Trace:
    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    def add(self, step: str, status: str, detail: str) -> None:
        self.events.append(TraceEvent(step=step, status=status, detail=detail))
