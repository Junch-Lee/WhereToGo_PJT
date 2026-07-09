from django.urls import path

from . import views


app_name = "curriculum"

urlpatterns = [
    path("", views.topics, name="topic_list"),
]
