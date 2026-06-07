"""
WSGI 애플리케이션 진입점.

동기 WSGI 서버에서 Django 앱을 실행할 때 사용된다. 현재 프로젝트는 기본 settings 모듈을
참조하며, 실제 callable은 application 변수로 노출된다.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
