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
    throw new Error(getErrorMessage(data, '요청 처리에 실패했습니다.'));
  }

  return data;
}

export function getMyInfo() {
  return request('/api/users/me/');
}

export function updateMyInfo(payload) {
  return request('/api/users/me/', {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export function changePassword(payload) {
  return request('/api/users/me/password/', {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export function getMyProfile() {
  return request('/api/users/me/profile/');
}

export function updateMyProfile(payload) {
  return request('/api/users/me/profile/', {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export function getTopics() {
  return request('/api/topics/');
}
