from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views


app_name = "accounts"

urlpatterns = [
    # 인증 API: 회원가입, 로그인, access token 재발급을 제공한다.
    path("auth/signup/", views.signup, name="signup"),
    path("auth/login/", views.login, name="login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # 현재 로그인한 사용자 기준의 계정/프로필 API다. 별도 user_id를 받지 않는다.
    path("users/me/", views.me, name="me"),
    path("users/me/password/", views.change_password, name="change_password"),
    path("users/me/profile/", views.my_profile, name="my_profile"),
]
