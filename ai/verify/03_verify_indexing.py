"""Step 3 인덱싱 코드 체크리스트 검증 스크립트."""

from __future__ import annotations

import ast
import sys
import tempfile
from pathlib import Path

import pandas as pd
from chromadb.api.types import Documents, Embeddings, EmbeddingFunction

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.core.chroma_client import get_courses_collection, reset_chroma_client  # noqa: E402
from ai.core.config import RagSettings  # noqa: E402
from ai.indexing.document_builder import build_course_documents, build_resource_documents  # noqa: E402
from ai.indexing.indexer import _add_documents  # noqa: E402
from ai.indexing.topic_merger import build_course_topic_map, build_resource_topic_map  # noqa: E402


class FakeEmbeddingFunction(EmbeddingFunction[Documents]):
    """검증용 고정 차원 임베딩 함수입니다."""

    def __init__(self) -> None:
        self.called = False

    def __call__(self, input: Documents):
        self.called = True
        return [[0.0] * 1536 for _ in input]


def main() -> None:
    """체크리스트에 따라 인덱싱 전처리와 적재를 검증합니다."""
    course_topics = build_course_topic_map(
        PROJECT_ROOT / "scripts" / "topic_pipeline" / "data" / "final" / "final_course_topics_import.csv"
    )
    resource_topics = build_resource_topic_map(
        PROJECT_ROOT / "scripts" / "topic_pipeline" / "data" / "final" / "final_resource_topics_import.csv"
    )
    courses_df = pd.read_csv(PROJECT_ROOT / "ai" / "data" / "curriculum_courses.csv", nrows=5)
    resources_df = pd.read_csv(PROJECT_ROOT / "ai" / "data" / "learning_resource.csv", nrows=5)

    course_docs = build_course_documents(courses_df, course_topics)
    resource_docs = build_resource_documents(resources_df, resource_topics)
    all_docs = course_docs + resource_docs

    _assert_no_typeddict()
    _assert_deterministic_ids(courses_df, course_topics)
    _assert_metadata_is_chroma_safe(all_docs)
    _assert_empty_fields_are_omitted()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        reset_chroma_client()
        config = RagSettings(
            chroma_persist_dir=Path(temp_dir),
            collection_courses="verify_courses",
            collection_resources="verify_resources",
        )
        embedding_function = FakeEmbeddingFunction()
        collection = get_courses_collection(embedding_function=embedding_function, config=config)
        stats = _add_documents(collection, course_docs)
        if stats["loaded_count"] != len(course_docs):
            raise AssertionError("적재 수가 입력 수와 다릅니다.")
        if not embedding_function.called:
            raise AssertionError("임베딩 함수가 컬렉션에 주입되어 호출되지 않았습니다.")
        reset_chroma_client()

    resource_path = PROJECT_ROOT / "ai" / "data" / "learning_resource.csv"
    if not resource_path.exists():
        raise AssertionError("learning_resource.csv 단수형 경로가 존재하지 않습니다.")

    print("Step 3 인덱싱 체크리스트 검증: OK")
    print(f"course_docs={len(course_docs)}, resource_docs={len(resource_docs)}")
    print(f"sample_course_id={course_docs[0]['id']}")
    print(f"sample_resource_id={resource_docs[0]['id']}")


def _assert_no_typeddict() -> None:
    """인덱싱 패키지에 TypedDict 사용이 없는지 확인합니다."""
    for path in (PROJECT_ROOT / "ai" / "indexing").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "TypedDict":
                raise AssertionError(f"TypedDict가 사용되었습니다: {path}")


def _assert_deterministic_ids(courses_df: pd.DataFrame, topic_map: dict) -> None:
    """같은 입력에서 같은 ID가 생성되는지 확인합니다."""
    first = build_course_documents(courses_df, topic_map)
    second = build_course_documents(courses_df, topic_map)
    if [doc["id"] for doc in first] != [doc["id"] for doc in second]:
        raise AssertionError("문서 ID가 결정론적으로 생성되지 않았습니다.")


def _assert_metadata_is_chroma_safe(documents: list[dict]) -> None:
    """metadata에 None이나 list가 없고 허용 타입만 있는지 확인합니다."""
    allowed_types = (str, int, float, bool)
    for document in documents:
        for key, value in document["metadata"].items():
            if value is None or isinstance(value, list):
                raise AssertionError(f"metadata에 None/list가 있습니다: {key}")
            if not isinstance(value, allowed_types):
                raise AssertionError(f"metadata 타입이 허용되지 않습니다: {key}={type(value)}")


def _assert_empty_fields_are_omitted() -> None:
    """빈 필드가 임베딩 텍스트에서 깔끔히 생략되는지 확인합니다."""
    df = pd.DataFrame(
        [
            {
                "source_row_number": 1,
                "course_name": "테스트 과목",
                "department_name": "",
                "grade": 0,
                "semester": "",
                "credit": "",
                "learning_objective": "",
                "prerequisite_material": "",
                "main_textbook": "",
            }
        ]
    )
    text = build_course_documents(df, {})[0]["text"]
    if "학과:" in text or "학습 목표:" in text or "선수 지식:" in text:
        raise AssertionError("빈 필드가 텍스트에서 생략되지 않았습니다.")


if __name__ == "__main__":
    main()
