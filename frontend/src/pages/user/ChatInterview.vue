<template>
  <div class="chat-interview-page">
    <aside
      class="chat-sidebar"
      :class="{ 'is-open': sidebarOpen }"
      @click.stop
    >
      <div class="sidebar-inner">
        <div class="sidebar-logo-section">
          <button class="sidebar-logo-button" type="button" @click="handleNavigate('/')">
            <div class="sidebar-logo-icon">
              <svg viewBox="0 0 24 24" class="icon">
                <path
                  d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2Zm3.86 6.14-2.12 6.36a1.5 1.5 0 0 1-.94.94l-6.36 2.12 2.12-6.36a1.5 1.5 0 0 1 .94-.94l6.36-2.12Z"
                  fill="currentColor"
                />
              </svg>
            </div>

            <div class="sidebar-logo-text">
              <strong>Where To Go</strong>
              <span>AI 학습 컨설턴트</span>
            </div>
          </button>
        </div>

        <div class="sidebar-search-section">
          <div class="sidebar-search-box">
            <svg viewBox="0 0 24 24" class="search-icon">
              <path
                d="M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15Z"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              />
            </svg>

            <input
              v-model="curriculumSearchKeyword"
              type="text"
              placeholder="내 커리큘럼 검색"
            />
          </div>
        </div>

        <nav class="sidebar-nav">
          <button
            v-for="item in menuItems"
            :key="item.path"
            type="button"
            class="sidebar-nav-item"
            :class="{ active: route.path === item.path }"
            @click="handleNavigate(item.path)"
          >
            <span class="nav-icon" v-html="item.icon"></span>
            <span>{{ item.label }}</span>
          </button>
        </nav>

        <div class="sidebar-content">
          <div v-if="isLoadingCurricula" class="empty-search">
            커리큘럼을 불러오는 중입니다...
          </div>

          <div v-else-if="curriculumLoadError" class="empty-search">
            커리큘럼 목록을 불러오지 못했습니다. 잠시 후 다시 시도해주세요.
          </div>

          <div v-else-if="hasNoCurriculums" class="empty-search">
            아직 생성한 커리큘럼이 없습니다.
          </div>

          <div v-else-if="hasNoFilteredCurriculums" class="empty-search">
            검색 결과가 없습니다.
          </div>

          <div v-else>
            <section v-if="filteredInProgress.length > 0" class="curriculum-section">
              <h3>진행 중인 커리큘럼</h3>

              <button
                v-for="item in filteredInProgress"
                :key="item.id"
                type="button"
                class="curriculum-item"
                @click="handleNavigate(`/curriculum/${item.id}`)"
              >
                <div class="curriculum-main">
                  <p>{{ item.title }}</p>

                  <div class="curriculum-meta">
                    <span class="sidebar-progress-track">
                      <span
                        class="sidebar-progress-fill"
                        :style="{ width: `${item.progress}%` }"
                      ></span>
                    </span>
                    <span>{{ item.statusLabel }}</span>
                    <span>{{ item.updated }}</span>
                  </div>
                </div>

                <span class="chevron">›</span>
              </button>
            </section>

            <section v-if="filteredCompleted.length > 0" class="curriculum-section">
              <h3>완료한 커리큘럼</h3>

              <button
                v-for="item in filteredCompleted"
                :key="item.id"
                type="button"
                class="curriculum-item completed"
                @click="handleNavigate(`/curriculum/${item.id}`)"
              >
                <div class="curriculum-main">
                  <p>{{ item.title }}</p>
                  <span class="completed-date">
                    {{ item.statusLabel }} · {{ item.updated }}
                  </span>
                </div>

                <span class="chevron">›</span>
              </button>
            </section>
          </div>
        </div>

        <div class="sidebar-bottom">
          <button type="button" class="sidebar-nav-item" @click="handleNavigate('/settings')">
            <span class="nav-icon" v-html="icons.settings"></span>
            <span>설정</span>
          </button>

          <button
            type="button"
            class="sidebar-nav-item"
            @click="handleLogout"
          >
            <span class="nav-icon" v-html="icons.logout"></span>
            <span>로그아웃</span>
          </button>
        </div>
      </div>
    </aside>

    <div
      v-if="sidebarOpen"
      class="sidebar-backdrop"
      @click="closeSidebar"
    ></div>

    <div class="chat-main">
      <header class="chat-header">
        <button
          type="button"
          class="logo-menu-button"
          aria-label="사이드바 열기"
          @click="toggleSidebar"
        >
          <span class="logo-menu-default">
            <svg viewBox="0 0 24 24" class="icon">
              <path
                d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2Zm3.86 6.14-2.12 6.36a1.5 1.5 0 0 1-.94.94l-6.36 2.12 2.12-6.36a1.5 1.5 0 0 1 .94-.94l6.36-2.12Z"
                fill="currentColor"
              />
            </svg>
          </span>

          <span class="logo-menu-hover">
            <svg viewBox="0 0 24 24" class="icon">
              <path
                d="M4 7h16M4 12h16M4 17h16"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              />
            </svg>
          </span>
        </button>

        <h1>AI 학습 코치</h1>
      </header>

      <main class="chat-content">
        <div class="chat-container">
          <section class="goal-card">
            <p class="goal-label">
              학습 목표
            </p>

            <h2 class="goal-title">
              {{ goal }}
            </h2>
          </section>

          <section class="question-progress-section">
            <div class="question-progress-meta">
              <span>{{ currentStep + 1 }} / {{ questions.length }}</span>
              <span>{{ progressPercent }}% 완료</span>
            </div>

            <div class="question-progress-track">
              <div
                class="question-progress-bar"
                :style="{ width: `${progressPercent}%` }"
              ></div>
            </div>
          </section>

          <section class="question-card">
            <div class="consultant-row">
              <div class="consultant-icon-wrap">
                <svg
                  class="consultant-icon"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M12 3l1.6 5.4L19 10l-5.4 1.6L12 17l-1.6-5.4L5 10l5.4-1.6L12 3z" />
                  <path d="M19 3v4" />
                  <path d="M17 5h4" />
                </svg>
              </div>

              <span class="consultant-label">
                AI 컨설턴트
              </span>
            </div>

            <h2 class="question-title">
              {{ currentQuestion.question }}
            </h2>

            <p class="question-helper">
              {{ currentQuestion.helperText }}
            </p>

            <div class="option-group">
              <button
                v-for="option in currentQuestion.options"
                :key="option.label"
                type="button"
                class="option-button"
                :class="{ 'option-button-selected': currentAnswer === option.value }"
                @click="selectOption(option)"
              >
                {{ option.label }}
              </button>
            </div>

            <div class="navigation-row">
              <button
                v-if="currentStep > 0"
                type="button"
                class="nav-button nav-button-secondary"
                @click="goPrevious"
              >
                이전
              </button>

              <button
                type="button"
                class="nav-button nav-button-primary"
                :class="{ 'nav-button-disabled': !isAnswered }"
                :disabled="!isAnswered"
                @click="goNext"
              >
                {{ currentStep === questions.length - 1 ? '완료' : '다음' }}
              </button>
            </div>
          </section>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getMyCurriculums } from '@/api/curriculumApi';
import { clearAuthStorage, isAuthenticated } from '@/utils/auth';
import './ChatInterview.css';

const router = useRouter();
const route = useRoute();

const goal = ref('');
const sidebarOpen = ref(false);
const curriculumSearchKeyword = ref('');
const curriculums = ref([]);
const isLoadingCurricula = ref(false);
const curriculumLoadError = ref('');
const currentStep = ref(0);
const answers = ref({});

const questions = [
  {
    id: 'purpose',
    question: '학습 목적이나 기대 결과는 무엇인가요?',
    helperText: '학습 목적에 따라 추천 이유와 커리큘럼 방향이 달라집니다.',
    options: [
      { label: '취업·이직', value: 'job' },
      { label: '포트폴리오', value: 'portfolio' },
      { label: '개념 이해', value: 'concept' },
      { label: '자격증', value: 'certificate' },
      { label: '기타', value: 'etc' },
    ],
  },
  {
    id: 'difficulty_level',
    question: '현재 어느 정도 수준인가요?',
    helperText: '현재 수준에 따라 커리큘럼의 시작 난이도를 결정합니다.',
    options: [
      { label: '완전 입문', value: 'beginner' },
      { label: '기초 있음', value: 'intermediate' },
      { label: '실무·심화 경험', value: 'advanced' },
    ],
  },
  {
    id: 'target_weeks',
    question: '어느 정도 기간 동안 학습할 수 있나요?',
    helperText: '학습 가능 기간을 기준으로 전체 커리큘럼 길이를 조정합니다.',
    options: [
      { label: '1개월', value: 4 },
      { label: '2개월', value: 8 },
      { label: '3개월', value: 12 },
      { label: '6개월', value: 24 },
    ],
  },
  {
    id: 'weekly_available_hours',
    question: '일주일에 몇 시간 정도 학습할 수 있나요?',
    helperText: '주간 학습 가능 시간에 따라 주차별 학습량을 조정합니다.',
    options: [
      { label: '~5h', value: 5 },
      { label: '7h', value: 7 },
      { label: '10~15h', value: 10 },
      { label: '20h+', value: 20 },
    ],
  },
  {
    id: 'preferred_learning_style',
    question: '어떤 방식으로 배우는 걸 선호하시나요?',
    helperText: '선호 학습 방식에 따라 강의, 실습, 프로젝트 비중을 조정합니다.',
    options: [
      { label: '강의 중심', value: 'lecture' },
      { label: '프로젝트 중심', value: 'project' },
      { label: '균형', value: 'balanced' },
    ],
  },
];

const icons = {
  user: `
    <svg viewBox="0 0 24 24" class="icon">
      <path d="M20 21a8 8 0 0 0-16 0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <circle cx="12" cy="7" r="4" fill="none" stroke="currentColor" stroke-width="2"/>
    </svg>
  `,
  chart: `
    <svg viewBox="0 0 24 24" class="icon">
      <path d="M4 19V5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <path d="M4 19h16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <path d="M8 16v-5M12 16V8M16 16v-9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    </svg>
  `,
  settings: `
    <svg viewBox="0 0 24 24" class="icon">
      <path d="M12 15.5A3.5 3.5 0 1 0 12 8a3.5 3.5 0 0 0 0 7.5Z" fill="none" stroke="currentColor" stroke-width="2"/>
      <path d="M19.4 15a1.8 1.8 0 0 0 .36 1.98l.04.04a2.1 2.1 0 0 1-2.97 2.97l-.04-.04a1.8 1.8 0 0 0-1.98-.36 1.8 1.8 0 0 0-1.1 1.65V21a2.1 2.1 0 1 1-4.2 0v-.06a1.8 1.8 0 0 0-1.1-1.65 1.8 1.8 0 0 0-1.98.36l-.04.04a2.1 2.1 0 0 1-2.97-2.97l.04-.04A1.8 1.8 0 0 0 4.6 15a1.8 1.8 0 0 0-1.65-1.1H3a2.1 2.1 0 1 1 0-4.2h.06A1.8 1.8 0 0 0 4.7 8.6a1.8 1.8 0 0 0-.36-1.98l-.04-.04a2.1 2.1 0 0 1 2.97-2.97l.04.04a1.8 1.8 0 0 0 1.98.36 1.8 1.8 0 0 0 1.1-1.65V3a2.1 2.1 0 1 1 4.2 0v.06a1.8 1.8 0 0 0 1.1 1.65 1.8 1.8 0 0 0 1.98-.36l.04-.04a2.1 2.1 0 0 1 2.97 2.97l-.04.04A1.8 1.8 0 0 0 19.4 9c.18.67.7 1.1 1.35 1.1H21a2.1 2.1 0 1 1 0 4.2h-.06A1.8 1.8 0 0 0 19.4 15Z" fill="none" stroke="currentColor" stroke-width="2"/>
    </svg>
  `,
  logout: `
    <svg viewBox="0 0 24 24" class="icon">
      <path d="M10 17l5-5-5-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M15 12H3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <path d="M14 4h5a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    </svg>
  `,
};

const menuItems = [
  { icon: icons.user, label: '마이페이지', path: '/mypage' },
  { icon: icons.chart, label: '학습 대시보드', path: '/learning' },
];

const statusLabels = {
  DRAFT: '초안',
  ACTIVE: '진행 중',
  COMPLETED: '완료',
  ARCHIVED: '보관됨',
};

const currentQuestion = computed(() => questions[currentStep.value]);

const currentAnswer = computed(() => answers.value[currentQuestion.value.id]);

const progressPercent = computed(() =>
  Math.round(((currentStep.value + 1) / questions.length) * 100),
);

const isAnswered = computed(() =>
  currentAnswer.value !== undefined && currentAnswer.value !== '',
);

const formatDate = (dateString) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('ko-KR');
};

const mapCurriculumForSidebar = (curriculum) => ({
  id: curriculum.id,
  title: curriculum.title,
  status: curriculum.status,
  statusLabel: statusLabels[curriculum.status] || curriculum.status,
  progress: curriculum.status === 'COMPLETED' ? 100 : 0,
  updated: formatDate(curriculum.updated_at || curriculum.created_at),
});

const filterCurricula = (curricula) => {
  const keyword = curriculumSearchKeyword.value.trim().toLowerCase();

  if (!keyword) return curricula;

  return curricula.filter((item) =>
    item.title.toLowerCase().includes(keyword),
  );
};

const inProgressCurricula = computed(() =>
  curriculums.value
    .filter((curriculum) => curriculum.status !== 'COMPLETED')
    .map(mapCurriculumForSidebar),
);

const completedCurricula = computed(() =>
  curriculums.value
    .filter((curriculum) => curriculum.status === 'COMPLETED')
    .map(mapCurriculumForSidebar),
);

const filteredInProgress = computed(() => filterCurricula(inProgressCurricula.value));

const filteredCompleted = computed(() => filterCurricula(completedCurricula.value));

const hasNoCurriculums = computed(() => curriculums.value.length === 0);

const hasNoFilteredCurriculums = computed(
  () =>
    Boolean(curriculumSearchKeyword.value.trim()) &&
    filteredInProgress.value.length === 0 &&
    filteredCompleted.value.length === 0,
);

const loadCurriculums = async () => {
  if (!isAuthenticated()) {
    curriculums.value = [];
    return;
  }

  isLoadingCurricula.value = true;
  curriculumLoadError.value = '';

  try {
    const response = await getMyCurriculums();
    curriculums.value = Array.isArray(response) ? response : [];
  } catch (error) {
    curriculumLoadError.value =
      error?.message || '커리큘럼 목록을 불러오지 못했습니다.';
  } finally {
    isLoadingCurricula.value = false;
  }
};

const syncAuthState = () => {
  if (!isAuthenticated()) {
    curriculums.value = [];
    closeSidebar();
  }
};

const toggleSidebar = () => {
  if (!sidebarOpen.value) {
    loadCurriculums();
  }

  sidebarOpen.value = !sidebarOpen.value;
};

const closeSidebar = () => {
  sidebarOpen.value = false;
};

const handleNavigate = (path) => {
  router.push(path);
  closeSidebar();
};

const selectOption = (option) => {
  answers.value[currentQuestion.value.id] = option.value;
};

const goPrevious = () => {
  if (currentStep.value === 0) return;
  currentStep.value -= 1;
};

const goNext = () => {
  if (!isAnswered.value) return;

  if (currentStep.value === questions.length - 1) {
    submitInterview();
    return;
  }

  currentStep.value += 1;
};

const submitInterview = () => {
  /**
   * InterviewSummary와 Generate API가 공유하는 MVP 6개 질문 payload입니다.
   *
   * 화면에는 한국어 label을 보여주지만, sessionStorage에는 백엔드 serializer choices가
   * 검증하는 내부 value를 저장합니다. 그래야 요약 화면에서 별도 변환 없이 그대로
   * Generate API payload로 사용할 수 있고, 프론트가 AI raw_input 키를 직접 만들지 않습니다.
   */
  const payload = {
    goal: goal.value,
    purpose: answers.value.purpose,
    difficulty_level: answers.value.difficulty_level,
    target_weeks: answers.value.target_weeks,
    weekly_available_hours: answers.value.weekly_available_hours,
    preferred_learning_style: answers.value.preferred_learning_style,
  };

  sessionStorage.setItem('interview_payload', JSON.stringify(payload));

  console.log('AI 상담 질문 응답:', payload);

  router.push('/interview/summary');
};

const handleEscKey = (event) => {
  if (event.key === 'Escape' && sidebarOpen.value) {
    closeSidebar();
  }
};

const handleLogout = () => {
  clearAuthStorage();
  closeSidebar();

  router.push('/');
};

onMounted(() => {
  window.addEventListener('keydown', handleEscKey);
  window.addEventListener('storage', syncAuthState);
  window.addEventListener('focus', syncAuthState);

  const savedGoal = sessionStorage.getItem('interview_goal');

  if (!savedGoal) {
    router.replace('/');
    return;
  }

  goal.value = savedGoal;

  syncAuthState();
  loadCurriculums();
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEscKey);
  window.removeEventListener('storage', syncAuthState);
  window.removeEventListener('focus', syncAuthState);
});
</script>
