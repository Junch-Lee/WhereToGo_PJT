"""RAG 파이프라인 환경 설정 관리 모듈."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 기본 경로들
# COLLECTION 설정 : 거리는 cosine 함수 (ChromaDB 기본 지원)
# 성격이 다른 두 데이터를 별도의 컬렉션으로 관리

DEFAULT_CHROMA_PERSIST_DIR = "./rag/data/chroma_db"
DEFAULT_COLLECTION_COURSES = "courses"
DEFAULT_COLLECTION_RESOURCES = "resources"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
AI_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


@dataclass(frozen=True)
class RagSettings:
    """RAG 설정값을 보관하고 기본 검증을 수행합니다.

    Attributes:
        chroma_persist_dir: ChromaDB가 로컬 디스크에 데이터를 저장할 경로입니다.
        collection_courses: 교육 과정 문서를 저장할 컬렉션명입니다.
        collection_resources: 참고 자료 문서를 저장할 컬렉션명입니다.
        embedding_model: 향후 임베딩 단계에서 사용할 모델명입니다.
        openai_api_key: OpenAI API 키입니다. Task 1에서는 필수로 사용하지 않습니다.
    """

    chroma_persist_dir: Path = field(
        default_factory=lambda: Path(DEFAULT_CHROMA_PERSIST_DIR)
    )
    collection_courses: str = DEFAULT_COLLECTION_COURSES
    collection_resources: str = DEFAULT_COLLECTION_RESOURCES
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    openai_api_key: str | None = None

    def __post_init__(self) -> None:
        """설정값의 형식과 최소 조건을 검증합니다."""
        self._validate_non_empty("COLLECTION_COURSES", self.collection_courses)
        self._validate_non_empty("COLLECTION_RESOURCES", self.collection_resources)
        self._validate_non_empty("EMBEDDING_MODEL", self.embedding_model)

        if self.collection_courses == self.collection_resources:
            raise ValueError("COLLECTION_COURSES와 COLLECTION_RESOURCES는 달라야 합니다.")

        if not str(self.chroma_persist_dir).strip():
            raise ValueError("CHROMA_PERSIST_DIR는 비어 있을 수 없습니다.")

        if not self.openai_api_key:
            logger.warning(
                "OPENAI_API_KEY가 설정되지 않았습니다. Task 1 검증에는 필요하지 않지만 "
                "임베딩 단계(Task 2)에서는 필요합니다."
            )

    @staticmethod
    def _validate_non_empty(name: str, value: str) -> None:
        """문자열 설정값이 비어 있지 않은지 확인합니다.

        Args:
            name: 환경 변수명입니다.
            value: 검증할 설정값입니다.

        Raises:
            ValueError: 설정값이 비어 있으면 발생합니다.
        """
        if not value.strip():
            raise ValueError(f"{name}는 비어 있을 수 없습니다.")

    @property
    def chroma_persist_path(self) -> Path:
        """확장된 ChromaDB 저장 경로를 반환합니다.

        Returns:
            사용자 홈 경로가 반영된 Path 객체입니다.
        """
        return self.chroma_persist_dir.expanduser()


def load_settings() -> RagSettings:
    """`.env` 파일과 환경 변수에서 RAG 설정을 로드합니다.

    Returns:
        검증이 끝난 RagSettings 인스턴스입니다.
    """
    load_dotenv(dotenv_path=AI_ENV_FILE)
    load_dotenv()

    settings = RagSettings(
        chroma_persist_dir=Path(
            os.getenv("CHROMA_PERSIST_DIR", DEFAULT_CHROMA_PERSIST_DIR)
        ),
        collection_courses=os.getenv(
            "COLLECTION_COURSES", DEFAULT_COLLECTION_COURSES
        ),
        collection_resources=os.getenv(
            "COLLECTION_RESOURCES", DEFAULT_COLLECTION_RESOURCES
        ),
        embedding_model=os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
    logger.debug("RAG 설정 로드 완료: %s", settings)
    return settings


settings = load_settings()
