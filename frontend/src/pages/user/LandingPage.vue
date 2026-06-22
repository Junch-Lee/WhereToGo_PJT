<template>
  <div class="landing-page">
    <!-- 고정 헤더 -->
    <header :class="['landing-header', { scrolled: isHeaderScrolled }]">
      <div class="header-inner">
        <button
          type="button"
          class="brand"
          aria-label="Where To Go 홈"
          @click="scrollToTop"
        >
          <span class="brand-symbol" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="9" />
              <path d="M9.25 14.75 11 9l5.75-1.75L15 13l-5.75 1.75Z" />
            </svg>
          </span>

          <span class="brand-name">Where To Go</span>
        </button>

        <nav class="desktop-navigation" aria-label="주요 메뉴">
          <button type="button" @click="scrollToSection('journey')">
            서비스 소개
          </button>

          <button type="button" @click="scrollToSection('experience')">
            이용 방법
          </button>
        </nav>

        <div class="header-actions">
          <button type="button" class="login-button" @click="goToLogin">
            로그인
          </button>

          <button type="button" class="start-button" @click="goToSignup">
            시작하기
          </button>
        </div>
      </div>
    </header>

    <main>
      <!-- Hero -->
      <section ref="heroSection" class="hero-section">
        <div class="hero-background" aria-hidden="true">
          <div class="hero-path">
            <svg viewBox="0 0 620 620" preserveAspectRatio="xMidYMid meet">
              <path
                class="path-secondary path-left"
                d="M310 75C221 123 132 229 116 352c-15 111 21 177 68 213"
              />

              <path
                class="path-secondary path-right"
                d="M310 75c89 48 178 154 194 277 15 111-21 177-68 213"
              />

              <path
                class="path-primary"
                d="M310 75v490"
                :style="{ strokeDashoffset: heroPathOffset }"
              />

              <circle class="path-start" cx="310" cy="75" r="8" />
              <circle class="path-end-halo" cx="310" cy="565" r="20" />
              <circle class="path-end" cx="310" cy="565" r="7" />
            </svg>
          </div>
        </div>

        <div
          class="hero-content"
          :style="{
            opacity: heroContentOpacity,
            transform: `translate3d(0, ${heroContentTranslate}px, 0)
              scale(${heroContentScale})`,
          }"
        >
          <p class="hero-eyebrow">AI LEARNING CONSULTANT</p>

          <h1 class="hero-title">
            <span>Where do you</span>
            <span>want to go?</span>
          </h1>

          <p class="hero-description">
            목표를 말하면, 현재 수준과 학습 가능 시간을 분석해<br />
            당신에게 맞는 학습 경로를 설계합니다.
          </p>

          <div class="hero-actions">
            <button type="button" class="hero-primary-button" @click="goToSignup">
              나의 학습 경로 찾기
              <span aria-hidden="true">→</span>
            </button>

            <button type="button" class="hero-secondary-button" @click="goToLogin">
              로그인
            </button>
          </div>
        </div>

        <button
          type="button"
          class="scroll-indicator"
          aria-label="서비스 소개로 이동"
          @click="scrollToSection('journey')"
        >
          <span>SCROLL TO DISCOVER</span>
          <span class="scroll-indicator-line"></span>
        </button>
      </section>

      <!-- WHERE → TO → GO -->
      <section
        id="journey"
        ref="journeySection"
        class="journey-section"
      >
        <div
          class="journey-sticky"
          :class="{ 'go-phase': activeJourneyPhase === 'GO' }"
        >
          <div class="journey-progress" aria-label="서비스 이용 단계">
            <span :class="{ active: activeJourneyPhase === 'WHERE', passed: journeyProgress > 0.32 }">
              WHERE
            </span>

            <i></i>

            <span :class="{ active: activeJourneyPhase === 'TO', passed: journeyProgress > 0.66 }">
              TO
            </span>

            <i></i>

            <span :class="{ active: activeJourneyPhase === 'GO' }">
              GO
            </span>
          </div>

          <!-- WHERE -->
          <article
            class="journey-panel where-panel"
            :style="getPhaseStyle('WHERE')"
          >
            <div class="journey-copy">
              <p class="journey-index">01</p>
              <h2 class="journey-word">WHERE</h2>
              <p class="journey-heading">무엇을 배우고 싶나요?</p>

              <p class="journey-description">
                막연한 목표여도 괜찮아요.<br />
                하고 싶은 일을 자유롭게 말해주세요.
              </p>
            </div>

            <div class="where-visual">
              <div class="goal-input-preview">
                <span class="goal-input-label">MY GOAL</span>

                <p>“백엔드 개발자로 취업하고 싶어요.”</p>

                <span class="typing-caret"></span>
              </div>

              <div class="keyword-cloud">
                <span
                  v-for="(keyword, index) in whereKeywords"
                  :key="keyword"
                  :style="getKeywordStyle(index)"
                >
                  {{ keyword }}
                </span>
              </div>
            </div>
          </article>

          <!-- TO -->
          <article
            class="journey-panel to-panel"
            :style="getPhaseStyle('TO')"
          >
            <div class="journey-copy">
              <p class="journey-index">02</p>
              <h2 class="journey-word">TO</h2>
              <p class="journey-heading">당신에게 맞는 방향을 찾습니다.</p>

              <p class="journey-description">
                AI 인터뷰를 통해 현재 수준과 목표,<br />
                현실적인 학습 가능 시간을 파악합니다.
              </p>
            </div>

            <div class="interview-visual">
              <div class="question-indicator">
                <span>QUESTION</span>
                <strong>{{ interviewQuestionIndex + 1 }} / {{ interviewQuestions.length }}</strong>
              </div>

              <div class="question-card">
                <p>{{ interviewQuestions[interviewQuestionIndex] }}</p>

                <div class="answer-options">
                  <span
                    v-for="answer in currentInterviewAnswers"
                    :key="answer"
                    :class="{ selected: answer === selectedInterviewAnswer }"
                  >
                    {{ answer }}
                  </span>
                </div>
              </div>

              <div class="analysis-result">
                <div>
                  <span>현재 수준</span>
                  <strong>기초</strong>
                </div>

                <div>
                  <span>목표</span>
                  <strong>백엔드 취업</strong>
                </div>

                <div>
                  <span>학습 시간</span>
                  <strong>주 10시간</strong>
                </div>
              </div>
            </div>
          </article>

          <!-- GO -->
          <article
            class="journey-panel go-panel"
            :style="getPhaseStyle('GO')"
          >
            <div class="journey-copy">
              <p class="journey-index">03</p>
              <h2 class="journey-word">GO</h2>
              <p class="journey-heading">당신만의 학습 경로가 완성됩니다.</p>

              <p class="journey-description">
                현재 수준과 목표를 기준으로<br />
                필요한 학습을 현실적인 순서로 연결합니다.
              </p>

              <div class="go-summary">
                <span><strong>8주</strong> 예상 기간</span>
                <span><strong>6</strong> Steps</span>
                <span><strong>10시간</strong> 주간 학습</span>
              </div>
            </div>

            <div class="curriculum-path">
              <div
                v-for="(step, index) in curriculumSteps"
                :key="step.number"
                class="curriculum-step"
                :style="getCurriculumStepStyle(index)"
              >
                <div class="step-number">{{ step.number }}</div>

                <div class="step-copy">
                  <strong>{{ step.title }}</strong>
                  <span>{{ step.time }}</span>
                </div>

                <div
                  v-if="index < curriculumSteps.length - 1"
                  class="step-connector"
                ></div>
              </div>
            </div>
          </article>
        </div>
      </section>

      <!-- 실제 학습 경험 -->
      <section
        id="experience"
        ref="experienceSection"
        class="experience-section"
      >
        <div class="experience-sticky">
          <div class="experience-heading">
            <p class="section-eyebrow">LEARNING EXPERIENCE</p>

            <h2>
              계획에서<br />
              끝나지 않도록.
            </h2>

            <p>
              시작하고, 멈추고, 다시 이어가며<br />
              당신의 속도로 학습할 수 있습니다.
            </p>
          </div>

          <div class="product-preview">
            <div class="preview-window-bar">
              <div class="window-dots" aria-hidden="true">
                <span></span>
                <span></span>
                <span></span>
              </div>

              <p>백엔드 개발자 취업 준비 · 6 Steps</p>
            </div>

            <div class="preview-body">
              <div class="preview-header">
                <span :class="['preview-status', previewState]">
                  {{ previewStatusLabel }}
                </span>

                <div class="preview-actions">
                  <template v-if="previewState === 'active'">
                    <button type="button" class="preview-primary">▶ 이어가기</button>
                    <button type="button" class="preview-outline">Ⅱ 일시정지</button>
                  </template>

                  <template v-else-if="previewState === 'paused'">
                    <button type="button" class="preview-primary">↻ 학습 재개하기</button>
                  </template>

                  <template v-else>
                    <button type="button" class="preview-primary">▶ 이어서 학습하기</button>
                  </template>
                </div>
              </div>

              <div class="preview-progress">
                <div class="preview-progress-label">
                  <span>전체 진행률</span>
                  <strong>{{ previewProgress }}%</strong>
                </div>

                <div class="preview-progress-track">
                  <div
                    class="preview-progress-fill"
                    :style="{ width: `${previewProgress}%` }"
                  ></div>
                </div>
              </div>

              <div class="preview-step-list">
                <div
                  v-for="step in previewSteps"
                  :key="step.title"
                  :class="['preview-step', step.status.toLowerCase()]"
                >
                  <span class="preview-step-icon">
                    {{ getPreviewStepIcon(step.status) }}
                  </span>

                  <strong>{{ step.title }}</strong>

                  <span v-if="step.status === 'IN_PROGRESS'" class="preview-step-badge">
                    진행 중
                  </span>

                  <span v-else-if="step.status === 'COMPLETED'" class="preview-step-finish">
                    완료
                  </span>
                </div>
              </div>

              <div v-if="previewState === 'paused'" class="preview-notice paused">
                학습이 일시정지되어 있어요. 진행 기록은 모두 유지됩니다.
              </div>

              <div v-if="previewState === 'done'" class="preview-notice completed">
                Step 2 완료 · 다음 단계인 인증과 권한을 시작합니다.
              </div>
            </div>
          </div>

          <div class="experience-state-label">
            <span :class="{ active: previewState === 'active' }">진행</span>
            <i></i>
            <span :class="{ active: previewState === 'paused' }">일시정지</span>
            <i></i>
            <span :class="{ active: previewState === 'done' }">다음 단계</span>
          </div>
        </div>
      </section>

      <!-- 핵심 가치 -->
      <section class="value-section">
        <article
          v-for="(value, index) in serviceValues"
          :key="value.strong"
          class="value-panel"
          :class="`value-panel-${index + 1}`"
        >
          <div>
            <p>{{ value.label }}</p>

            <h2>
              <strong>{{ value.strong }}</strong>
              <span>{{ value.soft }}</span>
            </h2>
          </div>
        </article>
      </section>

      <!-- Final CTA -->
      <section class="final-cta-section">
        <div class="final-path" aria-hidden="true">
          <span class="final-path-dot"></span>
          <span class="final-path-line"></span>
        </div>

        <div class="final-cta-content">
          <p class="final-cta-eyebrow">YOUR PATH STARTS HERE</p>

          <h2>
            So,<br />
            where do you want to go?
          </h2>

          <p>
            당신의 목표에서 시작해<br />
            당신만의 학습 경로를 만들어보세요.
          </p>

          <button type="button" @click="goToSignup">
            나의 학습 경로 찾기
            <span aria-hidden="true">→</span>
          </button>

          <button type="button" class="final-login-link" @click="goToLogin">
            이미 계정이 있나요? <strong>로그인</strong>
          </button>
        </div>
      </section>
    </main>

    <footer class="landing-footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <span class="brand-symbol small" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="9" />
              <path d="M9.25 14.75 11 9l5.75-1.75L15 13l-5.75 1.75Z" />
            </svg>
          </span>

          <strong>Where To Go</strong>
        </div>

        <p>© 2026 Where To Go. All rights reserved.</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import './LandingPage.css'

import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const heroSection = ref(null)
const journeySection = ref(null)
const experienceSection = ref(null)

const isHeaderScrolled = ref(false)
const heroProgress = ref(0)
const journeyProgress = ref(0)
const experienceProgress = ref(0)

const whereKeywords = [
  '백엔드 개발',
  'Django',
  'REST API',
  '포트폴리오',
  '취업',
]

const interviewQuestions = [
  '현재 어느 정도까지 학습해보셨나요?',
  '일주일에 몇 시간 정도 학습할 수 있나요?',
  '가장 먼저 이루고 싶은 목표는 무엇인가요?',
]

const interviewAnswers = [
  ['처음 배우는 단계', '기초 개념은 알고 있음', '프로젝트 경험 있음'],
  ['주 5시간 이하', '주 5~10시간', '주 10시간 이상'],
  ['기초 역량 강화', '포트폴리오 완성', '백엔드 개발자 취업'],
]

const curriculumSteps = [
  { number: '01', title: 'Python 기초', time: '10시간' },
  { number: '02', title: 'Django 기본', time: '12시간' },
  { number: '03', title: 'REST API', time: '10시간' },
  { number: '04', title: '인증과 권한', time: '8시간' },
  { number: '05', title: '테스트와 배포', time: '10시간' },
  { number: '06', title: '포트폴리오', time: '15시간' },
]

const serviceValues = [
  {
    label: 'FROM UNCERTAINTY',
    strong: '막연한 목표를',
    soft: '실행 가능한 순서로.',
  },
  {
    label: 'MADE FOR YOU',
    strong: '모두에게 같은 강의가 아니라,',
    soft: '당신에게 필요한 학습만.',
  },
  {
    label: 'KEEP MOVING',
    strong: '한 번 만든 계획이 아니라,',
    soft: '계속 이어지는 학습 경로.',
  },
]

const activeJourneyPhase = computed(() => {
  if (journeyProgress.value < 0.34) {
    return 'WHERE'
  }

  if (journeyProgress.value < 0.68) {
    return 'TO'
  }

  return 'GO'
})

const interviewQuestionIndex = computed(() => {
  const localProgress = clamp((journeyProgress.value - 0.34) / 0.34)

  if (localProgress < 0.34) {
    return 0
  }

  if (localProgress < 0.68) {
    return 1
  }

  return 2
})

const currentInterviewAnswers = computed(
  () => interviewAnswers[interviewQuestionIndex.value],
)

const selectedInterviewAnswer = computed(() => {
  if (interviewQuestionIndex.value === 0) {
    return '기초 개념은 알고 있음'
  }

  if (interviewQuestionIndex.value === 1) {
    return '주 5~10시간'
  }

  return '백엔드 개발자 취업'
})

const previewState = computed(() => {
  if (experienceProgress.value < 0.38) {
    return 'active'
  }

  if (experienceProgress.value < 0.72) {
    return 'paused'
  }

  return 'done'
})

const previewProgress = computed(() => (
  previewState.value === 'done' ? 55 : 35
))

const previewStatusLabel = computed(() => {
  if (previewState.value === 'paused') {
    return '일시정지'
  }

  if (previewState.value === 'done') {
    return '다음 단계 진행 중'
  }

  return '학습 중'
})

const previewSteps = computed(() => [
  {
    title: 'Python 기초',
    status: 'COMPLETED',
  },
  {
    title: 'Django REST API',
    status: previewState.value === 'done' ? 'COMPLETED' : 'IN_PROGRESS',
  },
  {
    title: '인증과 권한',
    status: previewState.value === 'done' ? 'IN_PROGRESS' : 'PENDING',
  },
])

const heroContentOpacity = computed(
  () => 1 - clamp(heroProgress.value * 1.9),
)

const heroContentTranslate = computed(
  () => -60 * clamp(heroProgress.value),
)

const heroContentScale = computed(
  () => 1 - 0.08 * clamp(heroProgress.value),
)

const heroPathOffset = computed(
  () => 520 - 520 * clamp(heroProgress.value * 1.45),
)

function clamp(value, min = 0, max = 1) {
  return Math.min(Math.max(value, min), max)
}

function calculateSectionProgress(element) {
  if (!element) {
    return 0
  }

  const rect = element.getBoundingClientRect()
  const scrollableDistance = element.offsetHeight - window.innerHeight

  if (scrollableDistance <= 0) {
    return rect.top <= 0 ? 1 : 0
  }

  return clamp(-rect.top / scrollableDistance)
}

function handleScroll() {
  isHeaderScrolled.value = window.scrollY > 36
  heroProgress.value = calculateSectionProgress(heroSection.value)
  journeyProgress.value = calculateSectionProgress(journeySection.value)
  experienceProgress.value = calculateSectionProgress(experienceSection.value)
}

function getPhaseStyle(phase) {
  const progress = journeyProgress.value

  const ranges = {
    WHERE: [0, 0.04, 0.27, 0.35],
    TO: [0.31, 0.39, 0.59, 0.68],
    GO: [0.63, 0.72, 1, 1],
  }

  const [fadeInStart, fadeInEnd, fadeOutStart, fadeOutEnd] = ranges[phase]

  let opacity = 0

  if (progress >= fadeInStart && progress <= fadeInEnd) {
    opacity = (progress - fadeInStart) / (fadeInEnd - fadeInStart)
  } else if (progress > fadeInEnd && progress < fadeOutStart) {
    opacity = 1
  } else if (
    fadeOutEnd > fadeOutStart &&
    progress >= fadeOutStart &&
    progress <= fadeOutEnd
  ) {
    opacity = 1 - ((progress - fadeOutStart) / (fadeOutEnd - fadeOutStart))
  } else if (phase === 'GO' && progress >= fadeInEnd) {
    opacity = 1
  }

  const translateY = (1 - opacity) * 32

  return {
    opacity,
    pointerEvents: opacity > 0.6 ? 'auto' : 'none',
    transform: `translate3d(0, ${translateY}px, 0)`,
  }
}

function getKeywordStyle(index) {
  const localProgress = clamp(journeyProgress.value / 0.32)
  const threshold = 0.2 + index * 0.12
  const opacity = clamp((localProgress - threshold) / 0.12)

  return {
    opacity,
    transform: `translate3d(0, ${(1 - opacity) * 20}px, 0)
      scale(${0.9 + opacity * 0.1})`,
  }
}

function getCurriculumStepStyle(index) {
  const goProgress = clamp((journeyProgress.value - 0.68) / 0.32)
  const threshold = index * 0.13
  const opacity = clamp((goProgress - threshold) / 0.16)

  return {
    opacity,
    transform: `translate3d(${(1 - opacity) * 24}px, 0, 0)`,
  }
}

function getPreviewStepIcon(status) {
  if (status === 'COMPLETED') {
    return '✓'
  }

  if (status === 'IN_PROGRESS') {
    return '○'
  }

  return '⌑'
}

function scrollToSection(id) {
  document.getElementById(id)?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
}

function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth',
  })
}

function goToLogin() {
  router.push('/login')
}

function goToSignup() {
  router.push('/signup')
}

onMounted(() => {
  handleScroll()

  window.addEventListener('scroll', handleScroll, {
    passive: true,
  })

  window.addEventListener('resize', handleScroll)
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('resize', handleScroll)
})
</script>