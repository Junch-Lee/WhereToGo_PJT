import { reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { login } from '@/api/authApi';

export function useLogin() {
  const router = useRouter();
  const route = useRoute();

  const form = reactive({
    email: '',
    password: '',
    rememberMe: false,
  });

  const errors = reactive({
    email: '',
    password: '',
    nonField: '',
  });

  const isSubmitting = ref(false);
  const showPassword = ref(false);

  const clearError = (field) => {
    errors[field] = '';
    errors.nonField = '';
  };

  const resetErrors = () => {
    Object.keys(errors).forEach((key) => {
      errors[key] = '';
    });
  };

  const validateForm = () => {
    let isValid = true;
    resetErrors();

    if (!form.email.trim()) {
      errors.email = '이메일을 입력해주세요.';
      isValid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      errors.email = '이메일 형식이 올바르지 않습니다.';
      isValid = false;
    }

    if (!form.password) {
      errors.password = '비밀번호를 입력해주세요.';
      isValid = false;
    }

    return isValid;
  };

  const clearPreviousAuthData = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    localStorage.removeItem('rememberMe');

    sessionStorage.removeItem('accessToken');
    sessionStorage.removeItem('refreshToken');
    sessionStorage.removeItem('user');
  };

  const saveTokens = (data) => {
    clearPreviousAuthData();

    const storage = form.rememberMe ? localStorage : sessionStorage;

    storage.setItem('accessToken', data.access);
    storage.setItem('refreshToken', data.refresh);

    localStorage.setItem('rememberMe', form.rememberMe ? 'true' : 'false');

    if (data.user) {
      storage.setItem('user', JSON.stringify(data.user));
    }
  };

  const getRedirectPath = () => {
    const redirect = route.query.redirect;

    if (Array.isArray(redirect)) {
      return redirect[0] || '/';
    }

    if (typeof redirect === 'string' && redirect.startsWith('/')) {
      return redirect;
    }

    return '/';
  };

  const restorePendingGoalIfNeeded = (redirectPath) => {
    const pendingGoal = sessionStorage.getItem('pendingLearningGoal');

    if (!pendingGoal) return;

    if (redirectPath.startsWith('/chat')) {
      sessionStorage.setItem('initialLearningGoal', pendingGoal);
    }

    sessionStorage.removeItem('pendingLearningGoal');
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    isSubmitting.value = true;

    try {
      const data = await login({
        email: form.email.trim(),
        password: form.password,
      });

      saveTokens(data);

      const redirectPath = getRedirectPath();

      restorePendingGoalIfNeeded(redirectPath);

      router.push(redirectPath);
    } catch (error) {
      errors.nonField =
        error?.message || '로그인 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.';
    } finally {
      isSubmitting.value = false;
    }
  };

  const handleGoogleLogin = () => {
    alert('Google 로그인은 추후 지원 예정입니다.');
  };

  const handleKakaoLogin = () => {
    alert('Kakao 로그인은 추후 지원 예정입니다.');
  };

  const handleForgotPassword = () => {
    alert('비밀번호 찾기는 추후 지원 예정입니다.');
  };

  return {
    form,
    errors,
    isSubmitting,
    showPassword,
    clearError,
    handleSubmit,
    handleGoogleLogin,
    handleKakaoLogin,
    handleForgotPassword,
  };
}