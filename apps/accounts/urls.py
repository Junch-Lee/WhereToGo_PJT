from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views


app_name = "accounts"

urlpatterns = [
    path("auth/signup/", views.signup, name="signup"),
    path("auth/login/", views.login, name="login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("users/me/", views.me, name="me"),
    path("users/me/password/", views.change_password, name="change_password"),
    path("users/me/profile/", views.my_profile, name="my_profile"),
]
