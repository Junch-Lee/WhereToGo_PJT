from django.urls import path

from . import views


app_name = "curriculum"

urlpatterns = [
    # 커리큘럼 생성 화면에서 사용할 활성 학습 토픽 목록 API
    path("", views.topics, name="topic_list"),
]
