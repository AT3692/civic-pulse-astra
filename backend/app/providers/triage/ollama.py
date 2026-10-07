import asyncio
import json

import httpx

from app.providers.triage.llm import SYSTEM
from app.schemas import TriageResult


class OllamaTriage:
    name = "llm:ollama"

    def __init__(self, client: httpx.AsyncClient, base_url: str, model: str):
        self.client, self.base_url, self.model = client, base_url, model

    async def triage(self, text: str, location: str) -> TriageResult:
        async with asyncio.timeout(10):
            response = await self.client.post(
                self.base_url.rstrip("/") + "/api/chat",
                timeout=10,
                json={
                    "model": self.model,
                    "stream": False,
                    "format": TriageResult.model_json_schema(),
                    "options": {"temperature": 0},
                    "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": json.dumps({"complaint": text, "location": location})},
                    ],
                },
            )
            response.raise_for_status()
            return TriageResult.model_validate_json(response.json()["message"]["content"])
