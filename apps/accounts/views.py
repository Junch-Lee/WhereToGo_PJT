from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile
from .serializers import (
    LoginSerializer,
    PasswordChangeSerializer,
    SignupSerializer,
    UserMeSerializer,
    UserProfileSerializer,
)


@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    """
    POST /api/auth/signup/

    비인증 사용자의 회원가입 요청을 처리한다. 입력 검증과 User 생성은 SignupSerializer가
    담당하고, view는 성공/실패 응답 형태만 결정한다.
    """
    serializer = SignupSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()

        return Response(
            {
                "message": "회원가입이 완료되었습니다.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "nickname": user.nickname,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST,
    )
    
    
@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """
    POST /api/auth/login/

    이메일과 비밀번호를 검증한 뒤 Simple JWT access/refresh 토큰을 발급한다. 인증 실패나
    비활성 계정 처리는 LoginSerializer에서 수행한다.
    """
    serializer = LoginSerializer(
        data=request.data,
        context={"request": request},
    )
    
    if serializer.is_valid():
        user = serializer.validated_data["user"]
        
        refresh = RefreshToken.for_user(user) # user를 위한 JWT 토큰 생성
        
        return Response(
            {
                "message": "로그인에 성공했습니다.",
                "access": str(refresh.access_token), # 실제 API 요청에 사용하는 짧은 수명 토큰
                "refresh": str(refresh), # access token이 만료되었을 때 새 access token 받기 위한 긴 수명 토큰
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "nickname": user.nickname
                }
            }, status=status.HTTP_200_OK)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    if request.method == "GET":
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = UserMeSerializer(
        request.user,
        data=request.data,
        partial=True,
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = PasswordChangeSerializer(
        data=request.data,
        context={"request": request},
    )

    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "비밀번호가 변경되었습니다."},
            status=status.HTTP_200_OK,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def my_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "GET":
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = UserProfileSerializer(
        profile,
        data=request.data,
        partial=True,
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
