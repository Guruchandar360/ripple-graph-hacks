import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    provider: str = os.getenv("MODEL_PROVIDER", "gemini")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")
    ollama_tool_mode: str = os.getenv("OLLAMA_TOOL_MODE", "native")
    graph_host: str = os.getenv("FALKORDB_HOST", "localhost")
    graph_port: int = int(os.getenv("FALKORDB_PORT", "6379"))
    graph_username: str = os.getenv("FALKORDB_USERNAME", "")
    graph_password: str = field(default=os.getenv("FALKORDB_PASSWORD", ""), repr=False)
    graph_ssl: bool = os.getenv("FALKORDB_SSL", "false").lower() == "true"
    api_key: str = field(default=os.getenv("GEMINI_API_KEY", ""), repr=False)
    model: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    gemini_request_interval: float = float(os.getenv("GEMINI_MIN_REQUEST_INTERVAL_SECONDS", "13"))
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    workspace_daily_runs: int = int(os.getenv("WORKSPACE_DAILY_RUNS", "3"))
    global_daily_runs: int = int(os.getenv("GLOBAL_DAILY_RUNS", "10"))
    max_workspaces: int = int(os.getenv("MAX_WORKSPACES", "30"))
    max_turns: int = int(os.getenv("MAX_MODEL_TURNS", "8"))
    timeout: int = int(os.getenv("RUN_TIMEOUT_SECONDS", "120"))

    @property
    def model_configured(self) -> bool:
        return bool(self.api_key) if self.provider == "gemini" else self.provider == "ollama"

    @property
    def active_model(self) -> str:
        return self.ollama_model if self.provider == "ollama" else self.model
