"""
커리큘럼 생성 orchestration service.

view에서 직접 생성 로직을 수행하지 않고, 입력 context 구성, 계획 생성, DB 저장 단계를
순서대로 호출한다. 실제 AI/RAG 생성기로 교체하더라도 view와 API 계약 변경을 최소화하기
위한 계층이다.
"""

from apps.curriculum.services.curriculum_context_service import (
    build_curriculum_context,
)
from apps.curriculum.services.curriculum_generator import generate_curriculum_plan
from apps.curriculum.services.curriculum_save_service import save_generated_curriculum


def create_curriculum_for_user(user, validated_data):
    """
    특정 사용자에 대한 DRAFT 커리큘럼을 생성한다.

    입력값:
        user: 커리큘럼 생성을 요청한 인증 사용자.
        validated_data: CurriculumCreateSerializer를 통과한 요청 데이터.
            goal은 필수이며 target_weeks, weekly_available_hours,
            preferred_learning_style은 선택값이다.

    반환값:
        DB에 저장된 Curriculum 인스턴스.

    현재 구현:
        이 함수는 커리큘럼 생성의 orchestration 계층이다. AI 모델을 직접 호출하지
        않고, context 생성 -> 임시 rule-based generator 호출 -> DB 저장 순서만
        조율한다.

    향후 확장 지점:
        generate_curriculum_plan 호출부가 AI/RAG/Agent 기반 generator로 바뀔 수
        있다. view는 이 service만 호출하므로, 생성 방식이 바뀌어도 API 계층의
        변경을 최소화할 수 있다.
    """
    # 1. 요청 값과 user_profile fallback, 교육 데이터 후보를 하나의 context로 모은다.
    context = build_curriculum_context(user, validated_data)

    # 2. 현재는 AI 없이 rule-based plan을 만든다. 나중에 이 호출이 AI 생성기로 교체된다.
    generated_plan = generate_curriculum_plan(context)

    # 3. 부모 Curriculum과 step/link row를 하나의 transaction 안에서 저장한다.
    return save_generated_curriculum(user, context, generated_plan)
