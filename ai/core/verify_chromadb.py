"""ChromaDB 설정 모듈 검증 스크립트."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from .chroma_client import (  # noqa: E402
    count_documents,
    ensure_default_collections,
    list_collection_names,
    validate_connection,
)
from .config import settings  # noqa: E402


def main() -> None:
    """ChromaDB 클라이언트 연결과 기본 컬렉션 생성을 검증합니다."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    print("ChromaDB 설정 검증을 시작합니다.")
    print(f"저장 경로: {settings.chroma_persist_path}")

    validate_connection(settings)
    print("클라이언트 연결: OK")

    collections = ensure_default_collections(config=settings)
    print("기본 컬렉션 생성/조회: OK")

    print("컬렉션 목록:")
    for collection_name in list_collection_names(settings):
        print(f"- {collection_name}")

    print("문서 수:")
    for collection_key, collection in collections.items():
        document_count = count_documents(collection.name, settings)
        print(f"- {collection_key} ({collection.name}): {document_count}")


if __name__ == "__main__":
    main()
