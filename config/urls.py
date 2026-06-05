"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.curriculum.views import curriculums


urlpatterns = [
    path("admin/", admin.site.urls),

    # API
    path("api/", include("apps.accounts.urls", namespace="accounts")),
    path("api/topics/", include("apps.curriculum.urls", namespace="curriculum")),
    path(
        "api/curriculums/",
        curriculums,
        name="curriculum_list_create",
    ),

    # Swagger / OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
