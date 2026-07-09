"""AI Agent에 전달할 Topic catalog를 구성하는 service."""

from apps.accounts.models import Topic


def build_topic_catalog() -> list[dict]:
    """active Topic과 alias 정보를 AI Agent용 dict list로 변환한다.

    이 함수가 필요한 이유:
        AI Agent는 Django ORM에 접근하지 않아야 한다. 따라서 백엔드가 DB에서
        active Topic과 TopicAlias를 조회한 뒤, AI가 순수 dict/list만으로 사용할 수
        있는 catalog를 만들어 전달해야 한다.

    반환 dict의 용도:
        ``ai.agent.run_agent(raw_input, catalog)``의 두 번째 인자로 전달된다. AI는 이
        catalog의 ``slug``, ``name``, ``parent_slug``, ``aliases``를 사용해 사용자
        목표와 Topic 후보를 매칭한다.

    Args:
        없음. catalog는 항상 현재 DB에 저장된 active Topic 전체를 기준으로 만든다.

    Returns:
        guide 계약에 맞춘 Topic catalog dict list. 각 dict에는 id, slug, name,
        parent_slug, depth, topic_type, is_learning_unit, is_assessable, aliases가
        포함된다.

    캐싱 제외:
        이번 PR에서는 캐싱을 구현하지 않는다. Topic 수가 많아지거나 generate API
        호출 빈도가 높아질 경우 Django cache 적용을 검토할 수 있다.
    """
    topics = (
        Topic.objects.filter(is_active=True)
        # parent_topic은 FK이므로 select_related로 같이 가져와 Topic별 부모 조회를 줄인다.
        .select_related("parent_topic")
        # aliases는 역참조 관계이므로 prefetch_related로 alias 목록 조회 N+1을 줄인다.
        .prefetch_related("aliases")
        .order_by("depth", "name", "id")
    )

    return [_serialize_topic(topic) for topic in topics]


def _serialize_topic(topic: Topic) -> dict:
    # AI에는 Django model 객체를 넘기지 않는다. 부모 Topic은 stable identifier인
    # slug만 전달해야 이후 AI 결과와 백엔드 FK 조회 계약이 단순해진다.
    parent_slug = topic.parent_topic.slug if topic.parent_topic else None

    # TopicAlias row 전체를 넘기면 AI 영역이 DB schema에 결합된다. 검색/매칭에 필요한
    # alias_name 문자열만 list로 평탄화한다.
    aliases = [alias.alias_name for alias in topic.aliases.all()]

    return {
        "id": topic.id,
        "slug": topic.slug,
        "name": topic.name,
        "parent_slug": parent_slug,
        "depth": topic.depth,
        "topic_type": topic.topic_type,
        "is_learning_unit": topic.is_learning_unit,
        "is_assessable": topic.is_assessable,
        "aliases": aliases,
    }
