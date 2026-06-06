"""WhereToGo RAG 문서 인덱싱 실행 모듈."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.core.chroma_client import (  # noqa: E402
    get_courses_collection,
    get_resources_collection,
    reset_collection,
)
from ai.core.embeddings import create_openai_embedding_function  # noqa: E402
from ai.indexing.document_builder import (  # noqa: E402
    build_course_documents,
    build_resource_documents,
)
from ai.indexing.topic_merger import (  # noqa: E402
    build_course_topic_map,
    build_resource_topic_map,
)

logger = logging.getLogger(__name__)

BATCH_SIZE = 100
COURSES_CSV_PATH = PROJECT_ROOT / "ai" / "data" / "curriculum_courses.csv"
RESOURCES_CSV_PATH = PROJECT_ROOT / "ai" / "data" / "learning_resource.csv"
COURSE_TOPICS_CSV_PATH = (
    PROJECT_ROOT / "scripts" / "topic_pipeline" / "data" / "final" / "final_course_topics_import.csv"
)
RESOURCE_TOPICS_CSV_PATH = (
    PROJECT_ROOT / "scripts" / "topic_pipeline" / "data" / "final" / "final_resource_topics_import.csv"
)


def index_courses(reset: bool = False, embedding_function: Any | None = None) -> dict:
    """강의 데이터를 courses 컬렉션에 적재합니다.

    Args:
        reset: True이면 적재 전 courses 컬렉션을 삭제 후 재생성합니다.
        embedding_function: ChromaDB 컬렉션에 주입할 임베딩 함수입니다.

    Returns:
        입력 수, 적재 수, 컬렉션 count를 담은 dict입니다.
    """
    documents = build_course_documents(
        _read_csv(COURSES_CSV_PATH),
        build_course_topic_map(COURSE_TOPICS_CSV_PATH),
    )
    collection = (
        reset_collection("courses", embedding_function=embedding_function)
        if reset
        else get_courses_collection(embedding_function=embedding_function)
    )
    return _add_documents(collection, documents)


def index_resources(reset: bool = False, embedding_function: Any | None = None) -> dict:
    """학습 자료 데이터를 resources 컬렉션에 적재합니다.

    Args:
        reset: True이면 적재 전 resources 컬렉션을 삭제 후 재생성합니다.
        embedding_function: ChromaDB 컬렉션에 주입할 임베딩 함수입니다.

    Returns:
        입력 수, 적재 수, 컬렉션 count를 담은 dict입니다.
    """
    documents = build_resource_documents(
        _read_csv(RESOURCES_CSV_PATH),
        build_resource_topic_map(RESOURCE_TOPICS_CSV_PATH),
    )
    collection = (
        reset_collection("resources", embedding_function=embedding_function)
        if reset
        else get_resources_collection(embedding_function=embedding_function)
    )
    return _add_documents(collection, documents)


def index_all(reset: bool = False, embedding_function: Any | None = None) -> dict:
    """강의와 학습 자료를 모두 인덱싱합니다.

    Args:
        reset: True이면 각 컬렉션을 삭제 후 재생성합니다.
        embedding_function: ChromaDB 컬렉션에 주입할 임베딩 함수입니다.

    Returns:
        courses/resources 결과를 담은 dict입니다.
    """
    embedding_function = embedding_function or create_openai_embedding_function()
    return {
        "courses": index_courses(reset=reset, embedding_function=embedding_function),
        "resources": index_resources(reset=reset, embedding_function=embedding_function),
    }


def _add_documents(collection: Any, documents: list[dict]) -> dict:
    """문서 dict 목록을 ChromaDB 컬렉션에 100건 단위로 add합니다."""
    if not documents:
        raise ValueError("인덱싱할 문서가 없습니다.")

    before_count = int(collection.count())
    for start in range(0, len(documents), BATCH_SIZE):
        batch = documents[start : start + BATCH_SIZE]
        logger.info("문서 적재 중: %s-%s/%s", start + 1, start + len(batch), len(documents))
        collection.add(
            ids=[document["id"] for document in batch],
            documents=[document["text"] for document in batch],
            metadatas=[document["metadata"] for document in batch],
        )

    count = int(collection.count())
    loaded_count = count - before_count
    if loaded_count != len(documents):
        raise RuntimeError(
            f"적재 수 검증 실패: loaded_count={loaded_count}, input_count={len(documents)}"
        )

    sample = collection.get(limit=1, include=["documents", "metadatas"])
    return {
        "input_count": len(documents),
        "loaded_count": loaded_count,
        "collection_count": count,
        "sample": sample,
    }


def _read_csv(csv_path: Path) -> pd.DataFrame:
    """CSV 파일을 읽고 비어 있지 않은지 확인합니다."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"CSV 데이터가 비어 있습니다: {csv_path}")
    return df


def main() -> None:
    """CLI 인덱싱 진입점입니다."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="WhereToGo RAG 데이터를 ChromaDB에 인덱싱합니다.")
    parser.add_argument(
        "--target",
        choices=["courses", "resources", "all"],
        default="all",
        help="인덱싱할 대상입니다.",
    )
    parser.add_argument("--reset", action="store_true", help="적재 전 컬렉션을 초기화합니다.")
    args = parser.parse_args()

    embedding_function = create_openai_embedding_function()
    if args.target == "courses":
        result = {"courses": index_courses(reset=args.reset, embedding_function=embedding_function)}
    elif args.target == "resources":
        result = {"resources": index_resources(reset=args.reset, embedding_function=embedding_function)}
    else:
        result = index_all(reset=args.reset, embedding_function=embedding_function)

    for name, stats in result.items():
        print(f"{name}: input={stats['input_count']}, loaded={stats['loaded_count']}")
        print(f"{name} sample: {stats['sample']}")


if __name__ == "__main__":
    main()
