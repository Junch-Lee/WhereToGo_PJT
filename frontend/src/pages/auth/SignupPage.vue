<template>
  <main class="signup-page">
    <section class="signup-container">
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

      <div class="signup-card">
        <div class="signup-card-header">
          <h2>회원가입</h2>
          <p>목표만 입력하면, AI가 나만의 학습 경로를 설계합니다.</p>
        </div>

        <form class="signup-form" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="nickname">닉네임</label>
            <input
              id="nickname"
              v-model="form.nickname"
              type="text"
              placeholder="닉네임을 입력하세요"
              :class="{ 'is-error': errors.nickname }"
              @input="clearError('nickname')"
            />
            <p v-if="errors.nickname" class="error-message">
              {{ errors.nickname }}
            </p>
          </div>

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
                placeholder="8자 이상 입력하세요"
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

          <div class="form-group">
            <label for="passwordConfirm">비밀번호 확인</label>

            <div class="password-field">
              <input
                id="passwordConfirm"
                v-model="form.passwordConfirm"
                :type="showPasswordConfirm ? 'text' : 'password'"
                placeholder="비밀번호를 다시 입력하세요"
                :class="{ 'is-error': errors.passwordConfirm }"
                @input="clearError('passwordConfirm')"
              />
              <button
                type="button"
                class="password-toggle"
                @click="showPasswordConfirm = !showPasswordConfirm"
              >
                {{ showPasswordConfirm ? '숨김' : '보기' }}
              </button>
            </div>

            <p v-if="errors.passwordConfirm" class="error-message">
              {{ errors.passwordConfirm }}
            </p>
          </div>

          <div class="terms-area">
            <label class="terms-label">
              <input
                v-model="form.agreeTerms"
                type="checkbox"
                class="terms-checkbox"
                @change="clearError('agreeTerms')"
              />

              <span>
                <button type="button" class="terms-link">이용약관</button>
                및
                <button type="button" class="terms-link">개인정보 처리방침</button>
                에 동의합니다.
              </span>
            </label>

            <p v-if="errors.agreeTerms" class="error-message">
              {{ errors.agreeTerms }}
            </p>
          </div>

          <button class="signup-button" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? '가입 중...' : '회원가입' }}
          </button>
        </form>

        <p class="login-guide">
          이미 계정이 있나요?
          <RouterLink to="/login">로그인</RouterLink>
        </p>
      </div>
    </section>
  </main>
</template>

<script setup>
import { RouterLink } from 'vue-router';
import { useSignup } from '@/composables/useSignup';
import './SignupPage.css';

const {
  form,
  errors,
  isSubmitting,
  showPassword,
  showPasswordConfirm,
  clearError,
  handleSubmit,
} = useSignup();
</script>
