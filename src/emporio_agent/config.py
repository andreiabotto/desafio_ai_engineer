"""Configuração central do agente."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
RUNTIME_DIR = ROOT_DIR / ".data"
DB_PATH = RUNTIME_DIR / "emporio.db"
CHROMA_DIR = ROOT_DIR / ".chroma"
POLICIES_PDF = DATA_DIR / "políticas_da_loja.pdf"
ENV_FILE = ROOT_DIR / ".env"

CSV_FILES = {
    "categories": DATA_DIR / "desafio_tecnico_ai_eng - categories.csv",
    "customers": DATA_DIR / "desafio_tecnico_ai_eng - customers.csv",
    "products": DATA_DIR / "desafio_tecnico_ai_eng - products.csv",
    "promotions": DATA_DIR / "desafio_tecnico_ai_eng - promotions.csv",
    "orders": DATA_DIR / "desafio_tecnico_ai_eng - orders.csv",
    "order_items": DATA_DIR / "desafio_tecnico_ai_eng - order_items.csv",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    # Multilingual: políticas e queries em PT-BR
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    hf_token: str = ""
    rag_top_k: int = 4
    llm_temperature: float = 0.2
    max_history_messages: int = 12
    max_tool_rounds: int = 8
    llm_max_retries: int = 3
    store_timezone: str = "America/Campo_Grande"
    max_user_input_chars: int = 4000


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()


def ensure_runtime_dirs() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
