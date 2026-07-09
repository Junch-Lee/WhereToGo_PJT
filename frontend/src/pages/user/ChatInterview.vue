<template>
  <div class="chat-page">
    <UserSidebar :open="sidebarOpen" @close="closeSidebar" />

    <div class="chat-main-layout">
      <header class="chat-header">
        <div class="chat-header-left">
          <BrandMenuButton @click="toggleSidebar" />

          <div class="journey-navigation" aria-label="현재 서비스 단계">
            <template
              v-for="(stage, index) in journeyStages"
              :key="stage"
            >
              <span
                :class="[
                  'journey-stage',
                  {
                    current: stage === currentJourneyStage,
                    completed: index < currentJourneyIndex,
                    upcoming: index > currentJourneyIndex,
                  },
                ]"
              >
                {{ stage }}
              </span>

              <span
                v-if="index < journeyStages.length - 1"
                class="journey-divider-line"
                aria-hidden="true"
              >
                →
              </span>
            </template>
          </div>
        </div>
      </header>

      <main class="chat-content">
        <section class="interview-section">
          <div class="stage-keyword" aria-hidden="true">TO</div>

          <div class="interview-progress">
            <span class="progress-number">
              {{ formattedCurrentStep }}
            </span>

            <div class="progress-line">
              <div
                class="progress-fill"
                :style="{ width: `${progressPercent}%` }"
              ></div>

              <div
                class="progress-dot"
                :style="{ left: `calc(${progressPercent}% - 5px)` }"
              ></div>
            </div>

            <span class="progress-number">
              {{ formattedTotal }}
            </span>
          </div>

          <div
            :key="currentQuestion.id"
            class="question-content"
          >
            <p class="question-category">
              QUESTION {{ formattedCurrentStep }}
            </p>

            <h1>{{ currentQuestion.question }}</h1>

            <div class="choice-list">
              <button
                v-for="option in currentQuestion.options"
                :key="option.label"
                type="button"
                :class="[
                  'choice-button',
                  { selected: currentAnswer === option.value },
                ]"
                @click="selectOption(option)"
              >
                <span class="choice-radio" aria-hidden="true">
                  <span></span>
                </span>

                <span>{{ option.label }}</span>
              </button>
            </div>
          </div>

          <div class="question-navigation">
            <button
              v-if="currentStep > 0"
              type="button"
              class="previous-button"
              @click="goPrevious"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M19 12H5"></path>
                <path d="m10 17-5-5 5-5"></path>
              </svg>

              <span>이전 질문</span>
            </button>

            <span v-else></span>

            <button
              type="button"
              class="next-button"
              :disabled="!isAnswered"
              @click="goNext"
            >
              <span>
                {{ currentStep === questions.length - 1 ? '완료' : '다음 질문' }}
              </span>

              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M5 12h14"></path>
                <path d="m14 7 5 5-5 5"></path>
              </svg>
            </button>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import UserSidebar from '@/components/user/UserSidebar.vue';
import BrandMenuButton from '@/components/user/BrandMenuButton.vue';
import { useRoute, useRouter } from 'vue-router';
import { getMyCurriculums } from '@/api/curriculumApi';
import { clearAuthStorage, isAuthenticated } from '@/utils/auth';
import '@/assets/styles/user-shell.css';
import './ChatInterview.css';

const router = useRouter();
const route = useRoute();

const goal = ref('');
const sidebarOpen = ref(false);
const logoHovered = ref(false);
const curriculumSearchKeyword = ref('');
const curriculums = ref([]);
const isLoadingCurricula = ref(false);
const curriculumLoadError = ref('');
const currentStep = ref(0);
const answers = ref({});
const journeyStages = ['WHERE', 'TO', 'GO'];
const currentJourneyStage = 'TO';

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

const currentPath = computed(() => route.path);
const currentJourneyIndex = computed(() =>
  journeyStages.indexOf(currentJourneyStage),
);
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
const formattedCurrentStep = computed(() =>
  String(currentStep.value + 1).padStart(2, '0'),
);
const formattedTotal = computed(() =>
  String(questions.length).padStart(2, '0'),
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
