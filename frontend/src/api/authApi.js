const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function signup(payload) {
  const response = await fetch(`${API_BASE_URL}/api/auth/signup/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.message ||
        data?.detail ||
        data?.email?.[0] ||
        data?.nickname?.[0] ||
        data?.password?.[0] ||
        data?.non_field_errors?.[0] ||
        '회원가입에 실패했습니다.'
    );
  }

  return data;
}