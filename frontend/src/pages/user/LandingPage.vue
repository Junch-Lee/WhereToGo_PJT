<template>
  <div class="landing-page">
    <nav class="landing-nav">
      <div class="landing-nav-inner">
        <button type="button" class="landing-brand" @click="goHome">
          <div class="landing-brand-icon">
            <svg viewBox="0 0 24 24" class="icon">
              <path
                d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2Zm3.86 6.14-2.12 6.36a1.5 1.5 0 0 1-.94.94l-6.36 2.12 2.12-6.36a1.5 1.5 0 0 1 .94-.94l6.36-2.12Z"
                fill="currentColor"
              />
            </svg>
          </div>

          <div class="landing-brand-text">
            <strong>Where To Go</strong>
            <span>AI 학습 컨설턴트</span>
          </div>
        </button>

        <div class="landing-nav-actions">
          <button type="button" class="nav-login-button" @click="goLogin">
            로그인
          </button>

          <button type="button" class="nav-signup-button" @click="goSignup">
            회원가입
          </button>
        </div>
      </div>
    </nav>

    <section class="landing-hero">
      <div class="gradient-blob blob-one"></div>
      <div class="gradient-blob blob-two"></div>
      <div class="gradient-blob blob-three"></div>

      <div class="landing-hero-inner">
        <div class="hero-copy">
          <h1>
            어디서부터 공부해야 할지<br />
            모르겠다면,<br />
            <span>AI 학습 컨설턴트</span>와<br />
            함께 시작하세요.
          </h1>

          <p>
            목표와 수준, 관심 분야를 바탕으로<br />
            나에게 맞는 학습 로드맵을 설계해드립니다.
          </p>

          <div class="hero-actions">
            <button type="button" class="primary-cta" @click="goLogin">
              로그인하고 시작하기
              <svg viewBox="0 0 24 24" class="cta-icon">
                <path
                  d="M5 12h14M13 5l7 7-7 7"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </button>

            <button type="button" class="secondary-cta" @click="goSignup">
              회원가입
            </button>
          </div>
        </div>

        <div class="hero-preview-wrap">
          <div class="hero-preview-card">
            <div class="preview-title-row">
              <div class="preview-icon">
                <svg viewBox="0 0 24 24" class="icon">
                  <path
                    d="M12 2l3 7h7l-5.5 4.5L18.5 21 12 16.8 5.5 21l2-7.5L2 9h7l3-7Z"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linejoin="round"
                  />
                </svg>
              </div>

              <h3>학습 목표 분석</h3>
            </div>

            <div class="preview-list">
              <div class="preview-item">
                <p>목표</p>
                <strong>데이터 분석가 준비</strong>
              </div>

              <div class="preview-item">
                <p>현재 수준</p>
                <strong>기초</strong>
              </div>

              <div class="preview-item">
                <p>주간 학습 시간</p>
                <strong>주 10시간</strong>
              </div>

              <div class="preview-item">
                <p>학습 기간</p>
                <strong>8주</strong>
              </div>
            </div>

            <div class="preview-result">
              <svg viewBox="0 0 24 24" class="check-icon">
                <path
                  d="M20 6 9 17l-5-5"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>

              <p>AI가 분석한 맞춤형 커리큘럼이 생성됩니다</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="landing-features">
      <div class="section-inner">
        <div class="section-heading">
          <h2>나에게 맞는 학습 경로를 찾아드립니다</h2>
          <p>AI가 당신의 목표, 시간, 관심사를 분석하여 최적의 커리큘럼을 설계합니다.</p>
        </div>

        <div class="feature-grid">
          <article
            v-for="feature in features"
            :key="feature.title"
            class="feature-card"
          >
            <div class="feature-icon" v-html="feature.icon"></div>

            <h3>{{ feature.title }}</h3>
            <p>{{ feature.description }}</p>
          </article>
        </div>
      </div>
    </section>

    <section class="landing-steps">
      <div class="steps-inner">
        <div class="section-heading">
          <h2>간단한 3단계로 시작하세요</h2>
          <p>몇 분 안에 나만의 학습 로드맵을 받아보실 수 있습니다.</p>
        </div>

        <div class="step-grid">
          <div
            v-for="(step, index) in steps"
            :key="step.number"
            class="step-card"
          >
            <div class="step-number">
              {{ step.number }}
            </div>

            <p>{{ step.text }}</p>

            <div
              v-if="index < steps.length - 1"
              class="step-line"
            ></div>
          </div>
        </div>
      </div>
    </section>

    <section class="landing-bottom-cta">
      <div class="bottom-cta-inner">
        <h2>
          나에게 맞는 학습 방향을<br />
          지금 확인해보세요.
        </h2>

        <p>AI 학습 컨설턴트가 당신의 성공적인 학습을 도와드립니다.</p>

        <div class="bottom-actions">
          <button type="button" class="bottom-primary" @click="goLogin">
            로그인하고 시작하기
          </button>

          <button type="button" class="bottom-secondary" @click="goSignup">
            회원가입
          </button>
        </div>
      </div>
    </section>

    <footer class="landing-footer">
      <p>© 2026 Where To Go. All rights reserved.</p>
    </footer>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import './LandingPage.css';

const router = useRouter();

const goHome = () => {
  router.push('/');
};

const goLogin = () => {
  router.push('/login');
};

const goSignup = () => {
  router.push('/signup');
};

const features = [
  {
    title: '목표 기반 커리큘럼',
    description: '취업, 자격증, 포트폴리오 등 목표에 따라 최적화된 학습 경로를 제공합니다.',
    icon: `
      <svg viewBox="0 0 24 24" class="icon">
        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        <circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/>
      </svg>
    `,
  },
  {
    title: '학습 가능 시간 반영',
    description: '주간 학습 가능 시간을 고려하여 현실적인 학습 일정을 설계합니다.',
    icon: `
      <svg viewBox="0 0 24 24" class="icon">
        <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/>
        <path d="M12 7v5l3 2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    `,
  },
  {
    title: '관심 분야 기반 추천',
    description: '관심 분야와 선호하는 학습 방식에 맞춘 맞춤형 자료를 추천합니다.',
    icon: `
      <svg viewBox="0 0 24 24" class="icon">
        <path d="M9 18h6M10 22h4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        <path d="M8 14a6 6 0 1 1 8 0c-.9.7-1.4 1.7-1.5 2.5h-5C9.4 15.7 8.9 14.7 8 14Z" fill="none" stroke="currentColor" stroke-width="2"/>
      </svg>
    `,
  },
];

const steps = [
  { number: '01', text: '로그인 또는 회원가입' },
  { number: '02', text: 'AI와 학습 목표 상담' },
  { number: '03', text: '나만의 커리큘럼 생성' },
];
</script>