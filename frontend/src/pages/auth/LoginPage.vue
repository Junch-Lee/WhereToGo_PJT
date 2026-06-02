<template>
  <main class="login-page">
    <section class="login-container">
      <div class="brand-header">
        <div class="brand-logo">
          <svg viewBox="0 0 24 24" class="brand-logo-icon">
            <path
              d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2Zm3.86 6.14-2.12 6.36a1.5 1.5 0 0 1-.94.94l-6.36 2.12 2.12-6.36a1.5 1.5 0 0 1 .94-.94l6.36-2.12Z"
              fill="currentColor"
            />
          </svg>
        </div>

        <div>
          <h1 class="brand-title">Where To Go</h1>
          <p class="brand-subtitle">AI 학습 컨설턴트</p>
        </div>
      </div>

      <div class="login-card">
        <div class="login-card-header">
          <h2>로그인</h2>
          <p>Where To Go에서 나만의 학습 로드맵을 이어가세요.</p>
        </div>

        <form class="login-form" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="email">이메일</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              placeholder="example@email.com"
              :class="{ 'is-error': errors.email }"
              @input="clearError('email')"
            />
            <p v-if="errors.email" class="error-message">
              {{ errors.email }}
            </p>
          </div>

          <div class="form-group">
            <label for="password">비밀번호</label>

            <div class="password-field">
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="비밀번호를 입력하세요"
                :class="{ 'is-error': errors.password }"
                @input="clearError('password')"
              />
              <button
                type="button"
                class="password-toggle"
                @click="showPassword = !showPassword"
              >
                {{ showPassword ? '숨김' : '보기' }}
              </button>
            </div>

            <p v-if="errors.password" class="error-message">
              {{ errors.password }}
            </p>
          </div>

          <div v-if="errors.nonField" class="form-error-box">
            {{ errors.nonField }}
          </div>

          <div class="login-options">
            <label class="remember-label">
              <input
                v-model="form.rememberMe"
                type="checkbox"
                class="remember-checkbox"
              />
              <span>로그인 상태 유지</span>
            </label>

            <button type="button" class="forgot-button" @click="handleForgotPassword">
              비밀번호 찾기
            </button>
          </div>

          <button class="login-button" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? '로그인 중...' : '로그인' }}
          </button>
        </form>

        <div class="divider">
          <span></span>
          <p>또는</p>
          <span></span>
        </div>

        <div class="social-buttons">
          <button type="button" class="google-button" @click="handleGoogleLogin">
            <svg class="social-icon" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            Google로 계속하기
          </button>

          <button type="button" class="kakao-button" @click="handleKakaoLogin">
            <svg class="social-icon" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12 3C6.48 3 2 6.48 2 10.75c0 2.73 1.86 5.13 4.66 6.5l-.78 2.86c-.07.27.24.49.47.33l3.43-2.29c.72.1 1.46.15 2.22.15 5.52 0 10-3.48 10-7.55S17.52 3 12 3Z"
              />
            </svg>
            Kakao로 계속하기
          </button>
        </div>

        <p class="signup-guide">
          아직 계정이 없나요?
          <RouterLink to="/signup">회원가입</RouterLink>
        </p>
      </div>
    </section>
  </main>
</template>

<script setup>
import { RouterLink } from 'vue-router';
import { useLogin } from '@/composables/useLogin';
import './LoginPage.css';

const {
  form,
  errors,
  isSubmitting,
  showPassword,
  clearError,
  handleSubmit,
  handleGoogleLogin,
  handleKakaoLogin,
  handleForgotPassword,
} = useLogin();
</script>