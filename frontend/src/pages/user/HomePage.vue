<template>
  <LandingPage v-if="!isLoggedIn" />

  <div v-else class="home-page">
    <UserSidebar :open="sidebarOpen" @close="closeSidebar" />

    <div class="home-main-layout">
      <header class="home-header">
        <div class="home-header-left">
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

      <main class="home-content">
        <section class="where-section">
          <div class="where-keyword" aria-hidden="true">WHERE</div>

          <h1>어디까지 성장하고 싶나요?</h1>

          <p class="where-description">
            막연한 목표도 괜찮아요. 당신의 현재와 목표를 함께 정리해드릴게요.
          </p>

          <form class="goal-form" @submit.prevent="handleSubmit">
            <textarea
              v-model="input"
              rows="4"
              aria-label="학습 목표"
              placeholder="무엇을 배우고 싶은지 자유롭게 적어주세요.
예: 백엔드 개발자로 취업하고 싶어요"
              @keydown.enter.exact.prevent="handleSubmit"
            ></textarea>

            <div class="goal-form-footer">
              <button
                type="submit"
                class="goal-submit-button"
                :disabled="!input.trim()"
              >
                <span>시작하기</span>

                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M5 12h14"></path>
                  <path d="m14 7 5 5-5 5"></path>
                </svg>
              </button>
            </div>
          </form>

          <div class="suggestion-area">
            <button
              v-for="suggestion in suggestions"
              :key="suggestion"
              type="button"
              class="suggestion-chip"
              @click="selectSuggestion(suggestion)"
            >
              {{ suggestion }}
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
import LandingPage from '@/pages/user/LandingPage.vue';
import { getMyCurriculums } from '@/api/curriculumApi';
import { clearAuthStorage, isAuthenticated } from '@/utils/auth';
import '@/assets/styles/user-shell.css';
import './HomePage.css';

const router = useRouter();
const route = useRoute();

const sidebarOpen = ref(false);
const logoHovered = ref(false);
const input = ref('');
const curriculumSearchKeyword = ref('');
const isLoggedIn = ref(isAuthenticated());
const curriculums = ref([]);
const isLoadingCurricula = ref(false);
const curriculumLoadError = ref('');

const currentJourneyStage = 'WHERE';
const journeyStages = ['WHERE', 'TO', 'GO'];
const currentJourneyIndex = computed(() =>
  journeyStages.indexOf(currentJourneyStage),
);
const currentPath = computed(() => route.path);

const suggestions = [
  '백엔드 개발',
  '데이터 분석',
  'AI 엔지니어링',
  '프론트엔드',
  '머신러닝',
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
  isLoggedIn.value = isAuthenticated();

  if (!isLoggedIn.value) {
    curriculums.value = [];
    closeSidebar();
  }
};

const toggleSidebar = () => {
  syncAuthState();

  if (!isLoggedIn.value) return;

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

const selectSuggestion = (suggestion) => {
  input.value = `${suggestion} 관련 학습을 하고 싶어요`;
};

const handleSubmit = () => {
  const goal = input.value.trim();

  if (!goal) return;

  /**
   * 첫 대화창에서 입력한 학습 목표를 질문 화면에서 사용할 수 있도록 저장합니다.
   *
   * ChatInterview.vue에서는 이 값을 sessionStorage.getItem('interview_goal')로 읽습니다.
   */
  sessionStorage.setItem('interview_goal', goal);

  /**
   * 이전 상담 결과가 남아 있으면 새 상담과 섞일 수 있으므로 제거합니다.
   */
  sessionStorage.removeItem('interview_payload');

  /**
   * 현재 프로젝트에서 질문 화면 라우트가 /chat이면 그대로 둡니다.
   * 만약 질문 화면 라우트를 /interview로 등록했다면 '/interview'로 바꾸면 됩니다.
   */
  router.push('/chat');
};

const handleEscKey = (event) => {
  if (event.key === 'Escape' && sidebarOpen.value) {
    closeSidebar();
  }
};

const handleLogout = () => {
  clearAuthStorage();
  syncAuthState();
  closeSidebar();

  router.push('/');
};

onMounted(() => {
  window.addEventListener('keydown', handleEscKey);
  window.addEventListener('storage', syncAuthState);
  window.addEventListener('focus', syncAuthState);

  syncAuthState();
  loadCurriculums();
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEscKey);
  window.removeEventListener('storage', syncAuthState);
  window.removeEventListener('focus', syncAuthState);
});
</script>
