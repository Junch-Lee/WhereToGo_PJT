<template>
  <div
    v-if="open"
    class="app-sidebar-backdrop"
    @click="emit('close')"
  ></div>

  <aside
    class="app-sidebar"
    :class="{ 'is-open': open }"
    @click.stop
  >
    <div class="app-sidebar-layout">
      <div class="app-sidebar-logo-section">
        <button
          class="app-sidebar-logo-button"
          type="button"
          @click="handleNavigate('/')"
        >
          <span class="brand-icon" aria-hidden="true"></span>

          <span class="brand-copy">
            <strong>Where To Go</strong>
            <small>AI 학습 컨설턴트</small>
          </span>
        </button>
      </div>

      <div class="app-sidebar-search-section">
        <div class="app-sidebar-search">
          <span class="app-sidebar-search-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="7"></circle>
              <path d="m16.2 16.2 4 4"></path>
            </svg>
          </span>

          <input
            v-model="curriculumSearchKeyword"
            type="search"
            placeholder="내 커리큘럼 검색"
          />
        </div>
      </div>

      <nav class="app-sidebar-main-menu">
        <button
          v-for="item in menuItems"
          :key="item.path"
          type="button"
          :class="['app-sidebar-menu-item', { active: currentPath === item.path }]"
          @click="handleNavigate(item.path)"
        >
          <span
            class="app-sidebar-menu-icon"
            v-html="item.icon"
            aria-hidden="true"
          ></span>
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <div class="app-sidebar-curriculum-area">
        <div v-if="isLoadingCurricula" class="app-sidebar-empty">
          커리큘럼을 불러오는 중입니다...
        </div>

        <div v-else-if="curriculumLoadError" class="app-sidebar-empty">
          커리큘럼 목록을 불러오지 못했습니다. 잠시 후 다시 시도해주세요.
        </div>

        <div v-else-if="hasNoCurriculums" class="app-sidebar-empty">
          아직 생성한 커리큘럼이 없습니다.
        </div>

        <div v-else-if="hasNoFilteredCurriculums" class="app-sidebar-empty">
          검색 결과가 없습니다.
        </div>

        <div v-else>
          <section
            v-if="filteredInProgress.length > 0"
            class="app-sidebar-curriculum-section"
          >
            <h2>진행 중인 커리큘럼</h2>

            <button
              v-for="item in filteredInProgress"
              :key="item.id"
              type="button"
              class="app-sidebar-curriculum-item"
              @click="handleNavigate(`/curriculum/${item.id}`)"
            >
              <div class="app-sidebar-curriculum-content">
                <strong>{{ item.title }}</strong>

                <div class="app-sidebar-curriculum-meta">
                  <div class="app-sidebar-progress-track">
                    <div
                      class="app-sidebar-progress-fill"
                      :style="{ width: `${item.progress}%` }"
                    ></div>
                  </div>
                  <span>{{ item.statusLabel }}</span>
                  <span>{{ item.updated }}</span>
                </div>
              </div>

              <span class="app-sidebar-item-arrow" aria-hidden="true">›</span>
            </button>
          </section>

          <section
            v-if="filteredCompleted.length > 0"
            class="app-sidebar-curriculum-section"
          >
            <h2>완료한 커리큘럼</h2>

            <button
              v-for="item in filteredCompleted"
              :key="item.id"
              type="button"
              class="app-sidebar-curriculum-item completed"
              @click="handleNavigate(`/curriculum/${item.id}`)"
            >
              <div class="app-sidebar-curriculum-content">
                <strong>{{ item.title }}</strong>
                <span class="app-sidebar-completed-date">
                  {{ item.statusLabel }} · {{ item.updated }}
                </span>
              </div>

              <span class="app-sidebar-item-arrow" aria-hidden="true">›</span>
            </button>
          </section>
        </div>
      </div>

      <div class="app-sidebar-footer">
        <button
          type="button"
          class="app-sidebar-footer-button"
          @click="handleNavigate('/settings')"
        >
          <span
            class="app-sidebar-footer-icon"
            v-html="icons.settings"
            aria-hidden="true"
          ></span>
          <span>설정</span>
        </button>

        <button
          type="button"
          class="app-sidebar-footer-button"
          @click="handleLogout"
        >
          <span
            class="app-sidebar-footer-icon"
            v-html="icons.logout"
            aria-hidden="true"
          ></span>
          <span>로그아웃</span>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getMyCurriculums } from '@/api/curriculumApi';
import { clearAuthStorage, isAuthenticated } from '@/utils/auth';

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['close']);

const router = useRouter();
const route = useRoute();

const curriculumSearchKeyword = ref('');
const curriculums = ref([]);
const isLoadingCurricula = ref(false);
const curriculumLoadError = ref('');

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
  IN_PROGRESS: '진행 중',
  NOT_STARTED: '시작 전',
  PAUSED: '일시정지',
  COMPLETED: '완료',
  ARCHIVED: '보관됨',
};

const currentPath = computed(() => route.path);

const formatDate = (dateString) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('ko-KR');
};

const normalizeStatus = (status) =>
  String(status || '')
    .trim()
    .replace(/[\s-]+/g, '_')
    .toUpperCase();

const mapCurriculumForSidebar = (curriculum) => {
  const status = normalizeStatus(curriculum.status);

  return {
    id: curriculum.id,
    title: curriculum.title,
    status,
    statusLabel: statusLabels[status] || status,
    progress: status === 'COMPLETED' ? 100 : 0,
    updated: formatDate(curriculum.updated_at || curriculum.created_at),
  };
};

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

function handleNavigate(path) {
  router.push(path);
  emit('close');
}

function handleLogout() {
  clearAuthStorage();
  emit('close');
  router.push('/');
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      loadCurriculums();
    }
  },
);
</script>
