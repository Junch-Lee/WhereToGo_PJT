<template>
  <div class="summary-page">
    <aside
      class="summary-sidebar"
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

    <div class="summary-main">
      <header class="summary-header">
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

        <h1>학습 정보 확인</h1>
      </header>

      <main class="summary-content">
        <div class="summary-container">
          <section class="summary-hero">
            <div class="summary-check-icon">
              <svg viewBox="0 0 24 24" class="icon-large">
                <path
                  d="M9 12l2 2 4-4"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.4"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <circle
                  cx="12"
                  cy="12"
                  r="9"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.2"
                />
              </svg>
            </div>

            <h2>학습 정보를 확인해주세요</h2>

            <p>
              AI가 아래 정보를 바탕으로 맞춤형 커리큘럼을 생성합니다.
            </p>
          </section>

          <section class="summary-card">
            <div class="summary-list">
              <div
                v-for="item in summaryItems"
                :key="item.key"
                class="summary-item"
              >
                <div class="summary-item-main">
                  <p class="summary-label">
                    {{ item.label }}
                  </p>

                  <p class="summary-value">
                    {{ item.value }}
                  </p>
                </div>
              </div>
            </div>
          </section>

          <section
            v-if="isGenerating"
            class="generating-card"
          >
            <div class="generating-icon">
              <svg viewBox="0 0 24 24" class="icon">
                <path
                  d="M12 2l1.8 5.7L20 10l-6.2 2.3L12 18l-1.8-5.7L4 10l6.2-2.3L12 2Z"
                  fill="currentColor"
                />
                <path
                  d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z"
                  fill="currentColor"
                />
              </svg>
            </div>

            <div class="generating-content">
              <p class="generating-title">
                맞춤형 커리큘럼을 생성하고 있어요
              </p>

              <p class="generating-description">
                학습 목표, 수준, 시간, 선호도를 반영하여 최적의 학습 경로를 구성하고 있습니다.
              </p>

              <div class="skeleton-list">
                <div class="skeleton-line"></div>
                <div class="skeleton-line short"></div>
                <div class="skeleton-line medium"></div>
              </div>
            </div>
          </section>

          <section
            v-if="!isGenerating"
            class="summary-actions"
          >
            <div
              v-if="generationMessage"
              class="generation-message"
              :class="`generation-message-${generationMessageType}`"
            >
              {{ generationMessage }}
            </div>

            <button
              type="button"
              class="primary-action-button"
              :disabled="isGenerating"
              @click="handleGenerateCurriculum"
            >
              커리큘럼 생성하기
            </button>

            <div class="secondary-action-row">
              <button
                type="button"
                class="secondary-action-button"
                @click="handleEditAnswers"
              >
                <svg viewBox="0 0 24 24" class="action-icon">
                  <path
                    d="M12 20h9"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                  />
                  <path
                    d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linejoin="round"
                  />
                </svg>

                답변 수정하기
              </button>

              <button
                type="button"
                class="secondary-action-button"
                @click="handleDiagnosis"
              >
                <svg viewBox="0 0 24 24" class="action-icon">
                  <path
                    d="M12 2l1.8 5.7L20 10l-6.2 2.3L12 18l-1.8-5.7L4 10l6.2-2.3L12 2Z"
                    fill="currentColor"
                  />
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
import { useRoute, useRouter } from 'vue-router';
import { generateCurriculum, getMyCurriculums } from '@/api/curriculumApi';
import { clearAuthStorage, isAuthenticated } from '@/utils/auth';
import './InterviewSummary.css';

const router = useRouter();
const route = useRoute();

const sidebarOpen = ref(false);
const curriculumSearchKeyword = ref('');
const curriculums = ref([]);
const isLoadingCurricula = ref(false);
const curriculumLoadError = ref('');
const isGenerating = ref(false);
const generationMessage = ref('');
const generationMessageType = ref('error');
const interviewPayload = ref({});

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

const valueLabels = {
  purpose: {
    job: '취업·이직',
    portfolio: '포트폴리오',
    concept: '개념 이해',
    certificate: '자격증',
    etc: '기타',
  },
  difficulty_level: {
    beginner: '완전 입문',
    intermediate: '기초 있음',
    advanced: '실무·심화 경험',
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
    balanced: '균형',
  },
};

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

const handleEditAnswers = () => {
  router.push('/chat');
};

const handleDiagnosis = () => {
  router.push('/diagnosis');
};

/**
 * InterviewSummary가 보관한 MVP 6개 답변만 Generate API payload로 만든다.
 *
 * sessionStorage에는 질문 화면에서 선택한 내부 value가 저장되어 있다. 여기서는 화면 표시용
 * label이나 AI raw_input 키(goal_text, level, period, weekly_hours, learning_style)를
 * 만들지 않는다. 백엔드 Generate Serializer가 API 입력 스키마를 검증하고 AI 입력으로
 * 변환해야 프론트와 AI 내부 계약이 느슨하게 분리된다.
 */
const buildGeneratePayload = () => {
  const payload = interviewPayload.value;

  return {
    goal: payload.goal,
    purpose: payload.purpose,
    difficulty_level: payload.difficulty_level,
    target_weeks: payload.target_weeks,
    weekly_available_hours: payload.weekly_available_hours,
    preferred_learning_style: payload.preferred_learning_style,
  };
};

const getGenerationMessage = (response) => {
  if (response?.status === 'out_of_scope') {
    return response.message || '현재는 컴퓨터공학 분야의 학습 목표만 지원합니다.';
  }

  if (response?.status === 'needs_clarification') {
    return response.clarification_question || '학습 목표를 조금 더 구체적으로 입력해주세요.';
  }

  if (response?.status === 'no_results') {
    return response.message || '관련 학습 자료가 부족합니다. 다른 목표로 다시 시도해주세요.';
  }

  return '커리큘럼을 생성하지 못했습니다. 잠시 후 다시 시도해주세요.';
};

const handleGenerateCurriculum = async () => {
  if (isGenerating.value) return;

  isGenerating.value = true;
  generationMessage.value = '';

  try {
    const response = await generateCurriculum(buildGeneratePayload());

    if (response.status === 'success') {
      const curriculumId = response.curriculum_id || response.curriculum?.id;

      if (curriculumId) {
        router.push(`/curriculum/${curriculumId}`);
        return;
      }

      generationMessageType.value = 'error';
      generationMessage.value = '커리큘럼은 생성됐지만 이동할 상세 정보를 찾지 못했습니다.';
      return;
    }

    /**
     * success 외 status는 저장된 커리큘럼이 없다는 의미다.
     * 따라서 결과/상세 페이지로 이동하지 않고 요약 화면에 안내를 남겨 사용자가 입력을
     * 수정하거나 다시 시도할 수 있게 한다.
     */
    generationMessageType.value = 'info';
    generationMessage.value = getGenerationMessage(response);
  } catch (error) {
    generationMessageType.value = 'error';
    generationMessage.value =
      error?.message || '커리큘럼 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
  } finally {
    isGenerating.value = false;
  }
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
  window.removeEventListener('keydown', handleEscKey);
  window.removeEventListener('storage', syncAuthState);
  window.removeEventListener('focus', syncAuthState);
});
</script>
