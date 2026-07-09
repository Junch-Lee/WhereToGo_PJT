"""Configuration for the RAG pipeline."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

DEFAULT_CHROMA_PERSIST_DIR = "./rag/data/chroma_db"
DEFAULT_COLLECTION_COURSES = "courses"
DEFAULT_COLLECTION_RESOURCES = "resources"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
AI_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


@dataclass(frozen=True)
class RagSettings:
    """Runtime settings for ChromaDB and embedding calls."""

    chroma_persist_dir: Path = field(default_factory=lambda: Path(DEFAULT_CHROMA_PERSIST_DIR))
    collection_courses: str = DEFAULT_COLLECTION_COURSES
    collection_resources: str = DEFAULT_COLLECTION_RESOURCES
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    gms_key: str | None = None
    openai_base_url: str = DEFAULT_OPENAI_BASE_URL

    def __post_init__(self) -> None:
        """Validate required non-secret settings."""
        self._validate_non_empty("COLLECTION_COURSES", self.collection_courses)
        self._validate_non_empty("COLLECTION_RESOURCES", self.collection_resources)
        self._validate_non_empty("EMBEDDING_MODEL", self.embedding_model)
        self._validate_non_empty("OPENAI_BASE_URL", self.openai_base_url)

        if self.collection_courses == self.collection_resources:
            raise ValueError("COLLECTION_COURSES and COLLECTION_RESOURCES must differ.")

        if not str(self.chroma_persist_dir).strip():
            raise ValueError("CHROMA_PERSIST_DIR must not be empty.")

        if not self.gms_key:
            logger.warning(
                "GMS_KEY is not set. ChromaDB setup can run, but embedding calls need it."
            )

    @staticmethod
    def _validate_non_empty(name: str, value: str) -> None:
        """Raise when a required string setting is empty."""
        if not value.strip():
            raise ValueError(f"{name} must not be empty.")

    @property
    def chroma_persist_path(self) -> Path:
        """Return the expanded ChromaDB persistence path."""
        return self.chroma_persist_dir.expanduser()


def load_settings() -> RagSettings:
    """Load RAG settings from ai/.env and process environment variables."""
    load_dotenv(dotenv_path=AI_ENV_FILE)
    load_dotenv()

    settings = RagSettings(
        chroma_persist_dir=Path(os.getenv("CHROMA_PERSIST_DIR", DEFAULT_CHROMA_PERSIST_DIR)),
        collection_courses=os.getenv("COLLECTION_COURSES", DEFAULT_COLLECTION_COURSES),
        collection_resources=os.getenv("COLLECTION_RESOURCES", DEFAULT_COLLECTION_RESOURCES),
        embedding_model=os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        gms_key=os.getenv("GMS_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL),
    )
    logger.debug("RAG settings loaded: %s", settings)
    return settings


settings = load_settings()
