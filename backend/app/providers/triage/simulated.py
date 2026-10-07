import hashlib

from app.providers.triage.rules import RuleBasedTriage
from app.schemas import TriageResult


class SimulatedTriage:
    name = "simulated"

    def __init__(self, failure_rate: float = 0):
        self.failure_rate = failure_rate

    async def triage(self, text: str, location: str) -> TriageResult:
        score = int(hashlib.sha256((text + location).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        if score < self.failure_rate:
            raise TimeoutError("Injected simulated timeout")
        return await RuleBasedTriage().triage(text, location)
