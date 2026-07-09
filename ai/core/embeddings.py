"""OpenAI 임베딩 생성 및 ChromaDB 연동 모듈."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from chromadb.api.types import Documents, Embeddings, EmbeddingFunction
from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ai.core.config import RagSettings, settings

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 100
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_MIN_SECONDS = 1
DEFAULT_RETRY_MAX_SECONDS = 4
EMBEDDING_DIMENSION = 1536


class OpenAIEmbeddingFunction(EmbeddingFunction[Documents]):
    """ChromaDB에서 사용할 수 있는 OpenAI 임베딩 함수입니다.

    Args:
        config: OpenAI API 키와 임베딩 모델명을 포함한 RAG 설정입니다.
        client: 테스트에서 주입할 수 있는 OpenAI 호환 클라이언트입니다.
        batch_size: 한 번의 API 호출에 포함할 최대 텍스트 수입니다.
    """

    def __init__(
        self,
        config: RagSettings = settings,
        client: Any | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        if not config.gms_key and client is None:
            raise ValueError("GMS_KEY must be set to create embeddings.")
        if batch_size <= 0:
            raise ValueError("batch_size는 1 이상이어야 합니다.")

        self.config = config
        self.client = client or OpenAI(
            api_key=config.gms_key,
            base_url=config.openai_base_url,
        )
        self.batch_size = batch_size

    def __call__(self, input: Documents):
        """ChromaDB 컬렉션에 주입 가능한 형식으로 임베딩을 생성합니다.

        Args:
            input: 임베딩할 문서 문자열 목록입니다.

        Returns:
            입력 문서 순서와 동일한 임베딩 벡터 목록입니다.
        """
        return self.embed_texts(list(input))

    def embed_text(self, text: str) -> list[float]:
        """단일 텍스트의 임베딩을 생성합니다.

        Args:
            text: 임베딩할 텍스트입니다.

        Returns:
            1536차원 임베딩 벡터입니다.
        """
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """여러 텍스트의 임베딩을 배치 단위로 생성합니다.

        Args:
            texts: 임베딩할 텍스트 목록입니다.

        Returns:
            입력 순서와 동일한 임베딩 벡터 목록입니다.

        Raises:
            ValueError: 입력이 비어 있거나 빈 문자열이 포함된 경우입니다.
            RuntimeError: OpenAI API 응답 차원이 기대값과 다른 경우입니다.
        """
        normalized_texts = _validate_texts(texts)
        embeddings: list[list[float]] = []

        for start in range(0, len(normalized_texts), self.batch_size):
            batch = normalized_texts[start : start + self.batch_size]
            logger.info(
                "OpenAI 임베딩 배치 처리 중: %s-%s/%s",
                start + 1,
                start + len(batch),
                len(normalized_texts),
            )
            embeddings.extend(self._embed_batch(batch))

        return embeddings

    @retry(
        retry=retry_if_exception_type(
            (APIConnectionError, APITimeoutError, InternalServerError, RateLimitError)
        ),
        stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
        wait=wait_exponential(
            multiplier=DEFAULT_RETRY_MIN_SECONDS,
            min=DEFAULT_RETRY_MIN_SECONDS,
            max=DEFAULT_RETRY_MAX_SECONDS,
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """OpenAI API를 호출해 한 배치의 임베딩을 생성합니다.

        Args:
            texts: 한 배치로 전송할 텍스트 목록입니다.

        Returns:
            입력 순서와 동일한 임베딩 벡터 목록입니다.
        """
        try:
            response = self.client.embeddings.create(
                model=self.config.embedding_model,
                input=list(texts),
            )
        except Exception:
            logger.exception("OpenAI 임베딩 API 호출에 실패했습니다.")
            raise

        embeddings = [item.embedding for item in response.data]
        _validate_embedding_response(embeddings, expected_count=len(texts))
        return embeddings


def create_openai_embedding_function(
    config: RagSettings = settings,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> OpenAIEmbeddingFunction:
    """ChromaDB 컬렉션에 주입할 OpenAI 임베딩 함수 인스턴스를 생성합니다.

    Args:
        config: OpenAI API 키와 임베딩 모델명을 포함한 RAG 설정입니다.
        batch_size: 한 번의 API 호출에 포함할 최대 텍스트 수입니다.

    Returns:
        OpenAIEmbeddingFunction 인스턴스입니다.
    """
    return OpenAIEmbeddingFunction(config=config, batch_size=batch_size)


def embed_text(text: str, config: RagSettings = settings) -> list[float]:
    """단일 텍스트의 OpenAI 임베딩을 생성합니다.

    Args:
        text: 임베딩할 텍스트입니다.
        config: OpenAI API 키와 임베딩 모델명을 포함한 RAG 설정입니다.

    Returns:
        1536차원 임베딩 벡터입니다.
    """
    return create_openai_embedding_function(config).embed_text(text)


def embed_texts(texts: Sequence[str], config: RagSettings = settings) -> list[list[float]]:
    """여러 텍스트의 OpenAI 임베딩을 생성합니다.

    Args:
        texts: 임베딩할 텍스트 목록입니다.
        config: OpenAI API 키와 임베딩 모델명을 포함한 RAG 설정입니다.

    Returns:
        입력 순서와 동일한 임베딩 벡터 목록입니다.
    """
    return create_openai_embedding_function(config).embed_texts(texts)


def _validate_texts(texts: Sequence[str]) -> list[str]:
    """임베딩 입력 텍스트를 검증하고 앞뒤 공백을 정리합니다.

    Args:
        texts: 검증할 텍스트 목록입니다.

    Returns:
        공백이 정리된 텍스트 목록입니다.

    Raises:
        ValueError: 입력이 비어 있거나 문자열이 아닌 값이 포함된 경우입니다.
    """
    if not texts:
        raise ValueError("임베딩할 텍스트가 비어 있습니다.")

    normalized: list[str] = []
    for index, text in enumerate(texts):
        if not isinstance(text, str):
            raise ValueError(f"임베딩 입력은 문자열이어야 합니다: index={index}")

        stripped_text = text.strip()
        if not stripped_text:
            raise ValueError(f"빈 문자열은 임베딩할 수 없습니다: index={index}")

        normalized.append(stripped_text)

    return normalized


def _validate_embedding_response(
    embeddings: Sequence[Sequence[float]],
    expected_count: int,
) -> None:
    """OpenAI 임베딩 응답 개수와 차원을 검증합니다.

    Args:
        embeddings: OpenAI API가 반환한 임베딩 목록입니다.
        expected_count: 기대하는 임베딩 개수입니다.

    Raises:
        RuntimeError: 응답 개수나 벡터 차원이 기대와 다른 경우입니다.
    """
    if len(embeddings) != expected_count:
        raise RuntimeError(
            f"임베딩 응답 개수가 입력 개수와 다릅니다: {len(embeddings)} != {expected_count}"
        )

    for index, embedding in enumerate(embeddings):
        if len(embedding) != EMBEDDING_DIMENSION:
            raise RuntimeError(
                f"임베딩 차원이 {EMBEDDING_DIMENSION}이 아닙니다: "
                f"index={index}, dimension={len(embedding)}"
            )


def _get_embedding_dimension(embedding: Sequence[Any]) -> int:
    """검증 스크립트에서 사용할 임베딩 차원을 반환합니다.

    Args:
        embedding: 차원을 확인할 임베딩 벡터입니다.

    Returns:
        임베딩 벡터 차원입니다.
    """
    return len(embedding)
