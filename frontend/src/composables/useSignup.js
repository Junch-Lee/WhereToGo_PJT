import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { signup } from '@/api/authApi';

export function useSignup() {
  const router = useRouter();

  const form = reactive({
    nickname: '',
    email: '',
    password: '',
    passwordConfirm: '',
    agreeTerms: false,
  });

  const errors = reactive({
    nickname: '',
    email: '',
    password: '',
    passwordConfirm: '',
    agreeTerms: '',
  });

  const isSubmitting = ref(false);
  const showPassword = ref(false);
  const showPasswordConfirm = ref(false);

  const clearError = (field) => {
    errors[field] = '';
  };

  const resetErrors = () => {
    Object.keys(errors).forEach((key) => {
      errors[key] = '';
    });
  };

  const validateForm = () => {
    let isValid = true;
    resetErrors();

    if (!form.nickname.trim()) {
      errors.nickname = '닉네임을 입력해주세요.';
      isValid = false;
    }

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
    } else if (form.password.length < 8) {
      errors.password = '비밀번호는 8자 이상이어야 합니다.';
      isValid = false;
    }

    if (!form.passwordConfirm) {
      errors.passwordConfirm = '비밀번호 확인을 입력해주세요.';
      isValid = false;
    } else if (form.password !== form.passwordConfirm) {
      errors.passwordConfirm = '비밀번호가 일치하지 않습니다.';
      isValid = false;
    }

    if (!form.agreeTerms) {
      errors.agreeTerms = '이용약관 및 개인정보 처리방침에 동의해주세요.';
      isValid = false;
    }

    return isValid;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    isSubmitting.value = true;

    try {
      await signup({
        nickname: form.nickname.trim(),
        email: form.email.trim(),
        password: form.password,
        password_confirm: form.passwordConfirm,
        agree_terms: form.agreeTerms,
      });

      alert('회원가입이 완료되었습니다.');
      router.push('/login');
    } catch (error) {
      errors.email =
        error?.message || '회원가입 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.';
    } finally {
      isSubmitting.value = false;
    }
  };

  const handleGoogleSignup = () => {
    window.location.href = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/auth/google/login/`;
  };

  const handleKakaoSignup = () => {
    window.location.href = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/auth/kakao/login/`;
  };

  return {
    form,
    errors,
    isSubmitting,
    showPassword,
    showPasswordConfirm,
    clearError,
    handleSubmit,
    handleGoogleSignup,
    handleKakaoSignup,
  };
}