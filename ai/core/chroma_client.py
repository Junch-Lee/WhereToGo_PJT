"""ChromaDB Persistent 클라이언트와 cosine 컬렉션 관리 모듈."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

from ai.core.config import RagSettings, settings

logger = logging.getLogger(__name__)

COURSES_COLLECTION_KEY = "courses"
RESOURCES_COLLECTION_KEY = "resources"
COSINE_DISTANCE = "cosine"
COLLECTION_METADATA = {"hnsw:space": COSINE_DISTANCE}

_client: ClientAPI | None = None


def get_chroma_client(config: RagSettings = settings) -> ClientAPI:
    """Persistent 모드 ChromaDB 클라이언트를 생성하거나 재사용합니다.

    Args:
        config: ChromaDB 저장 경로를 포함한 RAG 설정입니다.

    Returns:
        재사용 가능한 ChromaDB 클라이언트입니다.

    Raises:
        RuntimeError: 저장 디렉터리 생성 또는 클라이언트 초기화에 실패한 경우입니다.
    """
    global _client

    if _client is not None:
        return _client

    persist_path = config.chroma_persist_path
    _ensure_directory(persist_path)

    try:
        _client = chromadb.PersistentClient(path=str(persist_path))
        logger.info("ChromaDB Persistent 클라이언트 초기화 완료: %s", persist_path)
        return _client
    except Exception as exc:
        raise RuntimeError("ChromaDB 클라이언트 초기화에 실패했습니다.") from exc


def reset_chroma_client() -> None:
    """테스트나 설정 변경 후 클라이언트 싱글톤 캐시를 초기화합니다."""
    global _client
    _client = None


def get_collection(
    collection_key_or_name: str,
    embedding_function: Any | None = None,
    config: RagSettings = settings,
) -> Any:
    """컬렉션을 이름 또는 기본 키로 조회하고 없으면 생성합니다.

    Args:
        collection_key_or_name: `courses`, `resources` 또는 실제 컬렉션명입니다.
        embedding_function: Task 2에서 주입할 임베딩 함수입니다.
        config: 컬렉션명을 포함한 RAG 설정입니다.

    Returns:
        ChromaDB 컬렉션 객체입니다.

    Raises:
        RuntimeError: 컬렉션 생성 또는 조회에 실패한 경우입니다.
    """
    collection_name = resolve_collection_name(collection_key_or_name, config)
    client = get_chroma_client(config)

    try:
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata=COLLECTION_METADATA,
            embedding_function=embedding_function,
        )
        _validate_collection_metadata(collection_name, collection.metadata)
        logger.info("ChromaDB 컬렉션 준비 완료: %s", collection_name)
        return collection
    except Exception as exc:
        raise RuntimeError(f"컬렉션 준비에 실패했습니다: {collection_name}") from exc


def get_courses_collection(
    embedding_function: Any | None = None,
    config: RagSettings = settings,
) -> Any:
    """courses 컬렉션을 조회하거나 생성합니다.

    Args:
        embedding_function: Task 2에서 주입할 임베딩 함수입니다.
        config: 컬렉션명을 포함한 RAG 설정입니다.

    Returns:
        ChromaDB courses 컬렉션 객체입니다.
    """
    return get_collection(COURSES_COLLECTION_KEY, embedding_function, config)


def get_resources_collection(
    embedding_function: Any | None = None,
    config: RagSettings = settings,
) -> Any:
    """resources 컬렉션을 조회하거나 생성합니다.

    Args:
        embedding_function: Task 2에서 주입할 임베딩 함수입니다.
        config: 컬렉션명을 포함한 RAG 설정입니다.

    Returns:
        ChromaDB resources 컬렉션 객체입니다.
    """
    return get_collection(RESOURCES_COLLECTION_KEY, embedding_function, config)


def ensure_default_collections(
    embedding_function: Any | None = None,
    config: RagSettings = settings,
) -> dict[str, Any]:
    """기본 컬렉션(courses, resources)을 모두 준비합니다.

    Args:
        embedding_function: Task 2에서 주입할 임베딩 함수입니다.
        config: 컬렉션명을 포함한 RAG 설정입니다.

    Returns:
        컬렉션 키를 컬렉션 객체에 매핑한 딕셔너리입니다.
    """
    return {
        COURSES_COLLECTION_KEY: get_courses_collection(embedding_function, config),
        RESOURCES_COLLECTION_KEY: get_resources_collection(embedding_function, config),
    }


def resolve_collection_name(
    collection_key_or_name: str,
    config: RagSettings = settings,
) -> str:
    """컬렉션 키를 실제 컬렉션명으로 변환합니다.

    Args:
        collection_key_or_name: `courses`, `resources` 또는 실제 컬렉션명입니다.
        config: 컬렉션명을 포함한 RAG 설정입니다.

    Returns:
        ChromaDB에서 사용할 실제 컬렉션명입니다.
    """
    if collection_key_or_name == COURSES_COLLECTION_KEY:
        return config.collection_courses
    if collection_key_or_name == RESOURCES_COLLECTION_KEY:
        return config.collection_resources
    return collection_key_or_name


def collection_exists(
    collection_key_or_name: str,
    config: RagSettings = settings,
) -> bool:
    """컬렉션 존재 여부를 확인합니다.

    Args:
        collection_key_or_name: `courses`, `resources` 또는 실제 컬렉션명입니다.
        config: 컬렉션명을 포함한 RAG 설정입니다.

    Returns:
        컬렉션이 존재하면 True, 아니면 False입니다.
    """
    collection_name = resolve_collection_name(collection_key_or_name, config)
    client = get_chroma_client(config)

    try:
        client.get_collection(name=collection_name)
        return True
    except Exception:
        return False


def count_documents(
    collection_key_or_name: str,
    config: RagSettings = settings,
) -> int:
    """컬렉션 내 문서 개수를 조회합니다.

    Args:
        collection_key_or_name: `courses`, `resources` 또는 실제 컬렉션명입니다.
        config: 컬렉션명을 포함한 RAG 설정입니다.

    Returns:
        컬렉션에 저장된 문서 수입니다.
    """
    collection = get_collection(collection_key_or_name, config=config)
    return int(collection.count())


def reset_collection(
    collection_key_or_name: str,
    embedding_function: Any | None = None,
    config: RagSettings = settings,
) -> Any:
    """컬렉션을 삭제한 뒤 cosine 설정으로 다시 생성합니다.

    Args:
        collection_key_or_name: `courses`, `resources` 또는 실제 컬렉션명입니다.
        embedding_function: Task 2에서 주입할 임베딩 함수입니다.
        config: 컬렉션명을 포함한 RAG 설정입니다.

    Returns:
        새로 생성된 ChromaDB 컬렉션 객체입니다.
    """
    collection_name = resolve_collection_name(collection_key_or_name, config)
    client = get_chroma_client(config)

    if collection_exists(collection_name, config):
        client.delete_collection(name=collection_name)
        logger.info("ChromaDB 컬렉션 삭제 완료: %s", collection_name)

    return get_collection(collection_name, embedding_function, config)


def list_collection_names(config: RagSettings = settings) -> list[str]:
    """현재 ChromaDB 클라이언트의 컬렉션명 목록을 반환합니다.

    Args:
        config: ChromaDB 저장 경로를 포함한 RAG 설정입니다.

    Returns:
        컬렉션명 리스트입니다.
    """
    client = get_chroma_client(config)
    return [collection.name for collection in client.list_collections()]


def validate_connection(config: RagSettings = settings) -> bool:
    """ChromaDB 클라이언트 연결 상태를 검증합니다.

    Args:
        config: ChromaDB 저장 경로를 포함한 RAG 설정입니다.

    Returns:
        연결과 기본 API 호출이 성공하면 True입니다.

    Raises:
        RuntimeError: 클라이언트 연결 검증에 실패한 경우입니다.
    """
    try:
        client = get_chroma_client(config)
        client.heartbeat()
        client.list_collections()
        logger.info("ChromaDB 연결 검증 성공")
        return True
    except Exception as exc:
        raise RuntimeError("ChromaDB 연결 검증에 실패했습니다.") from exc


def _ensure_directory(path: Path) -> None:
    """ChromaDB 저장 디렉터리를 생성합니다.

    Args:
        path: 생성할 디렉터리 경로입니다.

    Raises:
        RuntimeError: 디렉터리 생성에 실패한 경우입니다.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(f"ChromaDB 저장 디렉터리 생성에 실패했습니다: {path}") from exc


def _validate_collection_metadata(
    collection_name: str,
    metadata: dict[str, Any] | None,
) -> None:
    """컬렉션 거리 함수 설정이 cosine인지 확인합니다.

    Args:
        collection_name: 검증할 컬렉션명입니다.
        metadata: ChromaDB 컬렉션 메타데이터입니다.

    Raises:
        ValueError: 기존 컬렉션의 거리 함수가 cosine이 아닌 경우입니다.
    """
    distance = (metadata or {}).get("hnsw:space")
    if distance != COSINE_DISTANCE:
        raise ValueError(
            f"컬렉션 '{collection_name}'의 거리 함수가 cosine이 아닙니다: {distance}"
        )
