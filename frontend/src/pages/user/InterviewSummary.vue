<template>
  <div
    v-if="isGenerating"
    class="summary-generating-screen"
  >
    <div class="generating-content">
      <div class="generating-journey" aria-hidden="true">
        <span class="generating-to">TO</span>
        <span class="generating-arrow">→</span>
        <span class="generating-go">GO</span>
      </div>

      <p class="generating-message">
        {{ generationStatusMessage }}
      </p>

      <p class="generating-description">
        답변을 바탕으로 바로 시작할 수 있는 학습 경로를 구성하고 있어요.
      </p>

      <div
        class="generation-progress"
        role="progressbar"
        :aria-valuenow="generationProgress"
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <span :style="{ width: `${generationProgress}%` }"></span>
      </div>
    </div>
  </div>

  <div
    v-else
    class="interview-summary-page"
  >
    <UserSidebar :open="sidebarOpen" @close="closeSidebar" />

    <div class="summary-main-layout">
      <header class="summary-header">
        <div class="summary-header-left">
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

      <main class="summary-content">
        <div class="summary-content-inner">
          <p class="summary-synthesis">
            <span>{{ goalText }}</span> 을 목표로,
            <span>{{ levelText }}</span> 수준에서
            <span>{{ periodText }}</span> 동안
            <span>{{ weeklyHoursText }}</span> 학습하는 커리큘럼을 준비할게요.
          </p>

          <section class="summary-key-points" aria-label="주요 학습 조건">
            <div
              v-for="item in keyPointItems"
              :key="item.label"
              class="summary-key-point"
            >
              <p>{{ item.label }}</p>
              <strong>{{ item.value }}</strong>
            </div>
          </section>

          <section class="answer-summary-card">
            <h1 class="answer-summary-title">Interview Summary</h1>

            <div class="answer-summary-list">
              <div
                v-for="item in summaryItems"
                :key="item.key"
                class="answer-summary-item"
              >
                <span>{{ item.label }}</span>
                <p>{{ item.value }}</p>
              </div>
            </div>
          </section>

          <section class="summary-actions">
            <div
              v-if="generationMessage"
              class="generation-message"
              :class="`generation-message-${generationMessageType}`"
            >
              {{ generationMessage }}
            </div>

            <button
              type="button"
              class="summary-primary-button"
              @click="handleGenerateCurriculum"
            >
              <span>커리큘럼 생성하기</span>
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M5 12h14"></path>
                <path d="m14 7 5 5-5 5"></path>
              </svg>
            </button>

            <div class="summary-secondary-actions">
              <button
                type="button"
                class="summary-outline-button"
                @click="handleEditAnswers"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 20h9"></path>
                  <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z"></path>
                </svg>
                답변 수정하기
              </button>

              <button
                type="button"
                class="summary-outline-button"
                @click="handleDiagnosis"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 2l1.8 5.7L20 10l-6.2 2.3L12 18l-1.8-5.7L4 10l6.2-2.3L12 2Z"></path>
                </svg>
                수준 진단하기
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
import UserSidebar from '@/components/user/UserSidebar.vue';
import BrandMenuButton from '@/components/user/BrandMenuButton.vue';
import { useRoute, useRouter } from 'vue-router';
import {
  generateCurriculumStream,
  getMyCurriculums,
} from '@/api/curriculumApi';
import { clearAuthStorage, isAuthenticated } from '@/utils/auth';
import '@/assets/styles/user-shell.css';
import './InterviewSummary.css';

const router = useRouter();
const route = useRoute();

const sidebarOpen = ref(false);
const logoHovered = ref(false);
const curriculumSearchKeyword = ref('');
const curriculums = ref([]);
const isLoadingCurricula = ref(false);
const curriculumLoadError = ref('');
const isGenerating = ref(false);
const generationMessage = ref('');
const generationMessageType = ref('error');
const displayedGenerationProgress = ref(0);
const generationProgressTarget = ref(0);
const generationStatusMessage = ref('커리큘럼 생성 준비 중입니다.');
const generationMessageTimer = ref(null);
const generationProgressTimer = ref(null);
const generationMessageIndex = ref(0);
const interviewPayload = ref({});

const journeyStages = ['WHERE', 'TO', 'GO'];
const currentJourneyStage = 'TO';

const generationWaitingMessages = [
  '답변에서 핵심 학습 목표를 정리하고 있습니다.',
  '현재 수준에 맞는 시작 지점을 찾고 있습니다.',
  '학습 기간과 주간 가능 시간을 계산하고 있습니다.',
  '관련 주제와 선수 지식을 함께 확인하고 있습니다.',
  '추천 강의와 학습 자료 후보를 비교하고 있습니다.',
  '단계별 학습 순서를 다듬고 있습니다.',
  '너무 쉽거나 어려운 구간이 없는지 점검하고 있습니다.',
  '결과 화면에 보여줄 내용을 정리하고 있습니다.',
];

const menuItems = [
  { icon: 'user', label: '마이페이지', path: '/mypage' },
  { icon: 'chart', label: '학습 대시보드', path: '/learning' },
];

const statusLabels = {
  DRAFT: '초안',
  ACTIVE: '진행 중',
  COMPLETED: '완료',
  ARCHIVED: '보관됨',
};

const valueLabels = {
  purpose: {
    job: '취업/이직',
    portfolio: '포트폴리오',
    concept: '개념 이해',
    certificate: '자격증',
    etc: '기타',
  },
  difficulty_level: {
    beginner: '완전 입문',
    intermediate: '기초 있음',
    advanced: '실무/심화 경험',
  },
  target_weeks: {
    4: '1개월',
    8: '2개월',
    12: '3개월',
    24: '6개월',
  },
  weekly_available_hours: {
    5: '~5h',
    7: '7h',
    10: '10~15h',
    20: '20h+',
  },
  preferred_learning_style: {
    lecture: '강의 중심',
    project: '프로젝트 중심',
    balanced: '균형형',
  },
};

const currentPath = computed(() => route.path);
const currentJourneyIndex = computed(() =>
  journeyStages.indexOf(currentJourneyStage),
);
const generationProgress = computed(() =>
  Math.min(100, Math.max(0, Math.round(displayedGenerationProgress.value))),
);

const goalText = computed(() => interviewPayload.value.goal || '새로운 목표');
const levelText = computed(
  () =>
    valueLabels.difficulty_level[interviewPayload.value.difficulty_level] ||
    interviewPayload.value.difficulty_level ||
    '현재',
);
const periodText = computed(
  () =>
    valueLabels.target_weeks[interviewPayload.value.target_weeks] ||
    `${interviewPayload.value.target_weeks || '-'}주`,
);
const weeklyHoursText = computed(
  () =>
    valueLabels.weekly_available_hours[
      interviewPayload.value.weekly_available_hours
    ] ||
    `${interviewPayload.value.weekly_available_hours || '-'}시간`,
);

const keyPointItems = computed(() => [
  { label: '목표', value: goalText.value },
  { label: '수준', value: levelText.value },
  { label: '기간', value: periodText.value },
]);

const summaryItems = computed(() => {
  const payload = interviewPayload.value;

  return [
    {
      key: 'goal',
      label: '배우고 싶은 주제',
      value: payload.goal,
    },
    {
      key: 'purpose',
      label: '학습 목적',
      value: valueLabels.purpose[payload.purpose] || payload.purpose,
    },
    {
      key: 'difficulty_level',
      label: '현재 수준',
      value:
        valueLabels.difficulty_level[payload.difficulty_level] ||
        payload.difficulty_level,
    },
    {
      key: 'target_weeks',
      label: '목표 기간',
      value: valueLabels.target_weeks[payload.target_weeks] || payload.target_weeks,
    },
    {
      key: 'weekly_available_hours',
      label: '주간 학습 시간',
      value:
        valueLabels.weekly_available_hours[payload.weekly_available_hours] ||
        payload.weekly_available_hours,
    },
    {
      key: 'preferred_learning_style',
      label: '선호 학습 방식',
      value:
        valueLabels.preferred_learning_style[payload.preferred_learning_style] ||
        payload.preferred_learning_style,
    },
  ].filter((item) => item.value !== undefined && item.value !== null && item.value !== '');
});
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

const filterCurricula = (items) => {
  const keyword = curriculumSearchKeyword.value.trim().toLowerCase();

  if (!keyword) return items;

  return items.filter((item) => item.title.toLowerCase().includes(keyword));
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

const filteredInProgress = computed(() =>
  filterCurricula(inProgressCurricula.value),
);
const filteredCompleted = computed(() =>
  filterCurricula(completedCurricula.value),
);
const hasNoCurriculums = computed(() => curriculums.value.length === 0);
const hasNoFilteredCurriculums = computed(
  () =>
    Boolean(curriculumSearchKeyword.value.trim()) &&
    filteredInProgress.value.length === 0 &&
    filteredCompleted.value.length === 0,
);

async function loadCurriculums() {
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
}

function syncAuthState() {
  if (!isAuthenticated()) {
    curriculums.value = [];
    closeSidebar();
  }
}

function toggleSidebar() {
  if (!sidebarOpen.value) {
    loadCurriculums();
  }

  sidebarOpen.value = !sidebarOpen.value;
}

function closeSidebar() {
  sidebarOpen.value = false;
}

function handleNavigate(path) {
  router.push(path);
  closeSidebar();
}

function handleEditAnswers() {
  router.push('/chat');
}

function handleDiagnosis() {
  router.push('/diagnosis');
}

function buildGeneratePayload() {
  const payload = interviewPayload.value;

  return {
    goal: payload.goal,
    purpose: payload.purpose,
    difficulty_level: payload.difficulty_level,
    target_weeks: payload.target_weeks,
    weekly_available_hours: payload.weekly_available_hours,
    preferred_learning_style: payload.preferred_learning_style,
  };
}

function getGenerationMessage(response) {
  if (response?.status === 'out_of_scope') {
    return response.message || '현재는 컴퓨터공학 분야의 학습 목표만 지원합니다.';
  }

  if (response?.status === 'needs_clarification') {
    return response.clarification_question || '학습 목표를 조금 더 구체적으로 입력해 주세요.';
  }

  if (response?.status === 'no_results') {
    return response.message || '관련 학습 자료가 부족합니다. 다른 목표로 다시 시도해 주세요.';
  }

  return '커리큘럼을 생성하지 못했습니다. 잠시 후 다시 시도해 주세요.';
}

function clearGenerationMessageTimer() {
  if (!generationMessageTimer.value) return;

  clearInterval(generationMessageTimer.value);
  generationMessageTimer.value = null;
}

function clearGenerationProgressTimer() {
  if (!generationProgressTimer.value) return;

  clearInterval(generationProgressTimer.value);
  generationProgressTimer.value = null;
}

function getGenerationProgressCap(progress) {
  if (progress >= 100) return 100;
  if (progress >= 80) return 96;
  if (progress >= 45) return 82;
  if (progress >= 25) return 44;
  if (progress >= 10) return 24;
  return 10;
}

function updateGenerationProgressTarget(progress) {
  const numericProgress = Number(progress);

  if (!Number.isFinite(numericProgress)) return;

  generationProgressTarget.value = Math.max(
    generationProgressTarget.value,
    Math.min(100, Math.max(0, numericProgress)),
  );

  displayedGenerationProgress.value = Math.max(
    displayedGenerationProgress.value,
    Math.min(generationProgressTarget.value, 100),
  );
}

function startGenerationProgressInterpolation() {
  clearGenerationProgressTimer();

  generationProgressTimer.value = window.setInterval(() => {
    if (!isGenerating.value) return;

    const cap = getGenerationProgressCap(generationProgressTarget.value);

    if (displayedGenerationProgress.value >= cap) return;

    const remaining = cap - displayedGenerationProgress.value;
    const increment = Math.min(0.8, Math.max(0.12, remaining * 0.035));
    displayedGenerationProgress.value = Math.min(
      cap,
      displayedGenerationProgress.value + increment,
    );
  }, 120);
}

function startGenerationMessageRotation(initialMessage) {
  clearGenerationMessageTimer();

  generationMessageIndex.value = 0;
  generationStatusMessage.value = initialMessage || generationWaitingMessages[0];

  generationMessageTimer.value = window.setInterval(() => {
    if (!isGenerating.value) return;

    generationMessageIndex.value =
      (generationMessageIndex.value + 1) % generationWaitingMessages.length;
    generationStatusMessage.value =
      generationWaitingMessages[generationMessageIndex.value];
  }, 2600);
}

async function handleGenerateCurriculum() {
  if (isGenerating.value) return;

  isGenerating.value = true;
  generationMessage.value = '';
  displayedGenerationProgress.value = 0;
  generationProgressTarget.value = 0;
  startGenerationProgressInterpolation();
  startGenerationMessageRotation('커리큘럼 생성 요청을 보내고 있습니다.');

  try {
    const response = await generateCurriculumStream(buildGeneratePayload(), {
      onProgress: (event) => {
        updateGenerationProgressTarget(event?.progress);
        if (event?.message) {
          generationStatusMessage.value = event.message;
        }
      },
      onDone: (event) => {
        clearGenerationMessageTimer();
        updateGenerationProgressTarget(event?.progress || 100);
        displayedGenerationProgress.value = 100;
        generationStatusMessage.value =
          event?.message || '커리큘럼 생성이 완료되었습니다.';
      },
    });

    if (response.status === 'success') {
      const generatedCurriculum = response.generated_curriculum;

      if (generatedCurriculum) {
        sessionStorage.removeItem('generated_curriculum_id');
        sessionStorage.setItem('generated_curriculum_response', JSON.stringify(response));
        router.push('/curriculum/result');
        return;
      }

      generationMessageType.value = 'error';
      generationMessage.value =
        '커리큘럼은 생성됐지만 이동할 상세 정보를 찾지 못했습니다.';
      return;
    }

    generationMessageType.value = 'info';
    generationMessage.value = getGenerationMessage(response);
  } catch (error) {
    generationMessageType.value = 'error';
    generationMessage.value =
      error?.message ||
      '커리큘럼 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.';
  } finally {
    clearGenerationMessageTimer();
    clearGenerationProgressTimer();
    isGenerating.value = false;
  }
}

function handleEscKey(event) {
  if (event.key === 'Escape' && sidebarOpen.value) {
    closeSidebar();
  }
}

function handleLogout() {
  clearAuthStorage();
  closeSidebar();
  router.push('/');
}

onMounted(() => {
  window.addEventListener('keydown', handleEscKey);
  window.addEventListener('storage', syncAuthState);
  window.addEventListener('focus', syncAuthState);

  const savedPayload = sessionStorage.getItem('interview_payload');

  if (!savedPayload) {
    router.replace('/chat');
    return;
  }

  try {
    interviewPayload.value = JSON.parse(savedPayload);
  } catch (error) {
    sessionStorage.removeItem('interview_payload');
    router.replace('/chat');
    return;
  }

  syncAuthState();
  loadCurriculums();
});

onBeforeUnmount(() => {
  clearGenerationMessageTimer();
  clearGenerationProgressTimer();
  window.removeEventListener('keydown', handleEscKey);
  window.removeEventListener('storage', syncAuthState);
  window.removeEventListener('focus', syncAuthState);
});
</script>
