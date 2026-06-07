"""
프로젝트 최상위 URL 설정.

admin, 계정 API, 커리큘럼 API, OpenAPI 문서 URL을 연결한다. 각 도메인의 세부 라우팅은
가능하면 앱 하위 urls.py에서 관리하고, 이 파일은 프로젝트 전체 prefix를 조립하는 역할에
집중한다.
"""

from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.curriculum.views import curriculum_detail, curriculums


urlpatterns = [
    path("admin/", admin.site.urls),

    # 계정/사용자 API는 /api/ prefix 아래에서 앱 단위 라우팅을 그대로 포함한다.
    path("api/", include("apps.accounts.urls", namespace="accounts")),

    # 토픽 API는 커리큘럼 생성 화면에서 학습 분야 선택용으로 사용한다.
    path("api/topics/", include("apps.curriculum.urls", namespace="curriculum")),

    # 커리큘럼 목록/생성/상세 조회 API는 현재 함수형 view로 직접 연결한다.
    path(
        "api/curriculums/",
        curriculums,
        name="curriculum_list_create",
    ),
    path(
        "api/curriculums/<int:curriculum_id>/",
        curriculum_detail,
        name="curriculum_detail",
    ),

    # Swagger / OpenAPI 문서. 프론트와 API 계약을 확인할 때 사용한다.
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
