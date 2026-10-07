import json
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.providers.triage.factory import make_provider
from app.providers.triage.llm import LLMTriage
from app.providers.triage.ollama import OllamaTriage
from app.providers.triage.simulated import SimulatedTriage
from app.schemas import TriageResult
from app.services.triage import TriageService
from tests.conftest import MemoryCache

VALID = {"category": "water", "priority": "high", "summary": "Flooding on the road", "confidence": 0.9}


@pytest.mark.parametrize("status,attempts", [(400, 1), (401, 1), (429, 2), (500, 2), (503, 2)])
async def test_retry_only_retryable_http_errors(status, attempts):
    request = httpx.Request("POST", "https://example.test")
    provider = SimulatedTriage()
    provider.triage = AsyncMock(
        side_effect=httpx.HTTPStatusError("error", request=request, response=httpx.Response(status))
    )
    sleep = AsyncMock()
    result, name, _ = await TriageService(provider, MemoryCache(), sleep=sleep).triage(
        "Burst water pipe", "Islamabad", uuid4()
    )
    assert provider.triage.await_count == attempts
    assert sleep.await_count == attempts - 1
    assert name == "rules:fallback" and result.category == "water"


async def test_timeout_retry_then_success():
    provider = SimulatedTriage()
    provider.triage = AsyncMock(side_effect=[TimeoutError(), TriageResult(**VALID)])
    result, name, _ = await TriageService(provider, MemoryCache(), sleep=AsyncMock()).triage(
        "Water pipe burst", "Islamabad", uuid4()
    )
    assert name == "simulated" and result.priority == "high"


@pytest.mark.parametrize(
    "content",
    [
        "not JSON",
        "```json {} ```",
        json.dumps({**VALID, "category": "admin"}),
        json.dumps({**VALID, "summary": "x" * 141}),
        json.dumps({**VALID, "summary": "two\nlines"}),
    ],
)
async def test_llm_malformed_output_falls_back_without_retry(content):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = LLMTriage(client, "https://example.test", "test-only", "model")
        _, name, _ = await TriageService(provider, MemoryCache()).triage("Water leaking outside", "G9", uuid4())
        assert name == "rules:fallback" and len(calls) == 1


async def test_hosted_payload_redacts_contact_and_omits_location():
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(VALID)}}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await LLMTriage(client, "https://example.test", "test-only", "model").triage(
            "Water burst call 0300-1234567 a@b.com", "PRIVATE LOCATION"
        )
    assert result.category == "water"
    payload = seen[0]["messages"][1]["content"]
    assert "0300" not in payload and "a@b.com" not in payload and "PRIVATE LOCATION" not in payload
    assert seen[0]["response_format"]["type"] == "json_object"


async def test_ollama_structured_output():
    def handler(request):
        assert json.loads(request.content)["format"]["type"] == "object"
        return httpx.Response(200, json={"message": {"content": json.dumps(VALID)}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        assert (
            await OllamaTriage(client, "http://ollama:11434", "model").triage("Water burst", "G9")
        ).category == "water"


@pytest.mark.parametrize("name", ["rules", "simulated", "llm", "ollama"])
async def test_factory(name):
    async with httpx.AsyncClient(trust_env=False) as client:
        assert make_provider(Settings(triage_provider=name), client).name


async def test_simulated_failure_deterministic():
    with pytest.raises(TimeoutError):
        await SimulatedTriage(1).triage("Water burst", "G9")
    with pytest.raises(ValidationError):
        TriageResult(**{**VALID, "confidence": 2})
