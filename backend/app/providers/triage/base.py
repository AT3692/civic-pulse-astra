from typing import Protocol

from app.schemas import TriageResult


class TriageProvider(Protocol):
    name: str

    async def triage(self, text: str, location: str) -> TriageResult: ...
