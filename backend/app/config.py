from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql://civicpulse:placeholder@postgres:5432/civicpulse"
    redis_url: str = "redis://redis:6379/0"
    triage_provider: str = "simulated"
    groq_api_key: SecretStr = SecretStr("")
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.1-8b-instant"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:1b"
    rate_limit_per_minute: int = Field(default=10, ge=1)
    simulated_failure_rate: float = Field(default=0, ge=0, le=1)
    # Only trust these immediate proxy peers. Empty means use the socket IP.
    trusted_proxy_cidrs: str = ""
    operator_api_key: SecretStr = SecretStr("")
