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

function createApiError(message, status) {
  const error = new Error(message);
  error.status = status;
  return error;
}

async function request(path, options = {}) {
  const accessToken = getAccessToken();

  if (!accessToken) {
    redirectToLogin();
    throw createApiError('로그인이 필요합니다.', 401);
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
    throw createApiError('로그인이 필요합니다.', 401);
  }

  if (!response.ok) {
    throw createApiError(
      getErrorMessage(data, '커리큘럼 요청 처리에 실패했습니다.'),
      response.status,
    );
  }

  return data;
}

/**
 * 현재 인증된 사용자가 소유한 커리큘럼 목록을 조회한다.
 * 사이드바와 마이페이지가 같은 API 데이터를 쓰도록 공통 함수로 분리했다.
 */
export function getMyCurriculums() {
  return request('/api/curriculums/');
}

/**
 * 현재 인증된 사용자가 소유한 특정 커리큘럼의 상세 정보를 조회한다.
 * 상세 페이지는 이 응답의 steps, resources, courses, schedules, progresses를 렌더링한다.
 */
export function getCurriculumDetail(curriculumId) {
  return request(`/api/curriculums/${curriculumId}/`);
}

/**
 * 커리큘럼 생성 API를 호출한다.
 * 생성 버튼이나 입력 화면이 붙을 때 같은 인증/오류 처리 흐름을 재사용한다.
 */
export function createCurriculum(payload) {
  return request('/api/curriculums/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * AI Generate API로 MVP 질문 6개 답변을 전송해 커리큘럼 생성을 요청한다.
 *
 * 프론트는 AI 내부 raw_input(goal_text, level, period 등)을 직접 만들지 않는다.
 * 백엔드 Generate Serializer가 검증과 raw_input 변환을 담당해야 API 계약이 한 곳에
 * 모이고, 프론트 화면 표시용 label이 AI 입력 스키마와 섞이지 않는다.
 */
export function generateCurriculum(payload) {
  return request('/api/curriculums/generate/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
