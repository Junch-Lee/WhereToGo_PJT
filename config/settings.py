"""
Django 프로젝트 설정 파일.

로컬 개발 환경 기준의 앱 등록, 미들웨어, DB, DRF/JWT, CORS, 정적/미디어 파일 설정을
관리한다. 운영 환경으로 분리할 때는 SECRET_KEY, DEBUG, ALLOWED_HOSTS, DB 설정을 환경변수
기반으로 옮기는 것이 우선이다.
"""

from datetime import timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = 'django-insecure-jlw$3=!!5(sfr7**3ub@*g3ey9iy5ei5r42jq797&@1ne9=xt2'

DEBUG = True

ALLOWED_HOSTS = []


# 앱 구성
# Django 기본 앱, DRF/CORS/OpenAPI 서드파티 앱, 프로젝트 로컬 앱을 순서대로 등록한다.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    "rest_framework",
    "corsheaders",
    "drf_spectacular",

    "apps.accounts",
    "apps.curriculum",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 프론트 개발 서버와 Django API 서버의 origin이 다르므로 로컬 Vue dev server를 허용한다.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# 로컬 개발용 SQLite DB 설정이다. 운영 환경에서는 별도 DB 설정으로 분리해야 한다.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# 회원가입/비밀번호 변경 시 Django 기본 비밀번호 검증 정책을 적용한다.
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# 한국어 UI와 Asia/Seoul 기준 시간을 사용한다. DB 저장은 USE_TZ=True 기준으로 처리된다.
LANGUAGE_CODE = 'ko-kr'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_TZ = True


# 정적 파일과 사용자 업로드 파일 경로 설정이다.
STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "media/"

MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DRF 인증/스키마 기본 설정.
# API는 기본적으로 JWT 인증을 사용하며, drf-spectacular가 OpenAPI schema를 생성한다.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# JWT 만료 시간 설정. access token은 API 요청 인증에, refresh token은 재발급에 사용된다.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7)
}

# 커스텀 User 모델을 사용하므로 Django auth가 accounts.User를 기준으로 동작하게 한다.
AUTH_USER_MODEL = "accounts.User"
