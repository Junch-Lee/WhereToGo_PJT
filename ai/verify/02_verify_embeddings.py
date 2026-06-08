"""OpenAI 임베딩 모듈 검증 스크립트."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.core.chroma_client import get_courses_collection  # noqa: E402
from ai.core.config import settings  # noqa: E402
from ai.core.embeddings import (  # noqa: E402
    EMBEDDING_DIMENSION,
    OpenAIEmbeddingFunction,
)


def main() -> None:
    """단건, 배치, ChromaDB 주입 방식의 임베딩 동작을 검증합니다."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    print("OpenAI 임베딩 모듈 검증을 시작합니다.")
    if not settings.gms_key:
        print(
            "GMS_KEY가 설정되어 있지 않아 실제 임베딩 API 검증을 건너뜁니다. "
            "ai/.env에 GMS_KEY를 설정한 뒤 다시 실행하세요."
        )
        return

    embedding_function = OpenAIEmbeddingFunction(config=settings)

    single_embedding = embedding_function.embed_text("Python 기초를 배우고 싶습니다.")
    print(f"단건 임베딩 차원: {len(single_embedding)}")

    batch_inputs = [
        "데이터 분석 커리큘럼을 추천해 주세요.",
        "백엔드 개발자가 되기 위한 학습 순서가 궁금합니다.",
        "AI 서비스 기획에 필요한 자료를 찾고 싶습니다.",
    ]
    batch_embeddings = embedding_function.embed_texts(batch_inputs)
    print(f"배치 임베딩 개수: {len(batch_embeddings)}")
    print(f"배치 첫 번째 임베딩 차원: {len(batch_embeddings[0])}")

    collection = get_courses_collection(embedding_function=embedding_function)
    print(f"ChromaDB 임베딩 함수 주입: OK ({collection.name})")

    if len(single_embedding) != EMBEDDING_DIMENSION:
        raise RuntimeError("단건 임베딩 차원이 기대값과 다릅니다.")
    if len(batch_embeddings) != len(batch_inputs):
        raise RuntimeError("배치 임베딩 개수가 입력 개수와 다릅니다.")
    if any(len(embedding) != EMBEDDING_DIMENSION for embedding in batch_embeddings):
        raise RuntimeError("배치 임베딩 차원이 기대값과 다릅니다.")

    print("OpenAI 임베딩 모듈 검증: OK")


if __name__ == "__main__":
    main()
