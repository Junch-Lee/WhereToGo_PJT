import { clearAuthStorage, getAccessToken } from '@/utils/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function redirectToLogin() {
  clearAuthStorage();

  if (window.location.pathname !== '/login') {
    const redirect = `${window.location.pathname}${window.location.search}`;
    window.location.href = `/login?redirect=${encodeURIComponent(redirect)}`;
  }
}

function getErrorMessage(data, fallbackMessage) {
  const firstFieldError = data && typeof data === 'object'
    ? Object.values(data).find((value) => Array.isArray(value) || typeof value === 'string')
    : null;

  if (Array.isArray(firstFieldError)) return firstFieldError[0];
  if (typeof firstFieldError === 'string') return firstFieldError;

  return data?.message || data?.detail || fallbackMessage;
}

async function request(path, options = {}) {
  const accessToken = getAccessToken();

  if (!accessToken) {
    redirectToLogin();
    throw new Error('로그인이 필요합니다.');
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
      ...options.headers,
    },
  });

  const data = await response.json().catch(() => null);

  if (response.status === 401) {
    redirectToLogin();
    throw new Error('로그인이 필요합니다.');
  }

  if (!response.ok) {
    throw new Error(getErrorMessage(data, '커리큘럼 요청 처리에 실패했습니다.'));
  }

  return data;
}

/**
 * 현재 인증된 사용자가 소유한 커리큘럼 목록을 조회한다.
 * 사이드바와 마이페이지가 같은 API 데이터를 사용하도록 공통 함수로 분리했다.
 */
export function getMyCurriculums() {
  return request('/api/curriculums/');
}

/**
 * 커리큘럼 생성 API를 호출한다.
 * 현재 화면에서는 직접 연결하지 않지만, 생성 버튼/입력 화면을 붙일 때 재사용한다.
 */
export function createCurriculum(payload) {
  return request('/api/curriculums/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
