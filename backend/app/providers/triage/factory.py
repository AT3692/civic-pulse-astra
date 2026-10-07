import httpx

from app.config import Settings
from app.providers.triage.base import TriageProvider
from app.providers.triage.llm import LLMTriage
from app.providers.triage.ollama import OllamaTriage
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage


def make_provider(settings: Settings, client: httpx.AsyncClient) -> TriageProvider:
    match settings.triage_provider:
        case "rules":
            return RuleBasedTriage()
        case "simulated":
            return SimulatedTriage(settings.simulated_failure_rate)
        case "llm":
            return LLMTriage(
                client, settings.llm_base_url, settings.groq_api_key.get_secret_value(), settings.llm_model
            )
        case "ollama":
            return OllamaTriage(client, settings.ollama_base_url, settings.ollama_model)
        case _:
            raise ValueError("Unknown TRIAGE_PROVIDER")
