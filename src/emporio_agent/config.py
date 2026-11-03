"""Configuração central do agente."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
RUNTIME_DIR = ROOT_DIR / ".data"
DB_PATH = RUNTIME_DIR / "emporio.db"
CHROMA_DIR = ROOT_DIR / ".chroma"
POLICIES_PDF = DATA_DIR / "políticas_da_loja.pdf"

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
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    rag_top_k: int = 4
    llm_temperature: float = 0.2


def get_settings() -> Settings:
    return Settings()


def ensure_runtime_dirs() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
