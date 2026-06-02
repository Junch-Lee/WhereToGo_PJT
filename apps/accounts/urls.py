from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login, name="login"),
    
    # SimpleJWT가 이미 만들어둔 토큰 재발급 전용 View => 직접 refresh 로직을 만들 수는 있으나 이미 안정적인 것을 제공하고 있다.
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh")
]
