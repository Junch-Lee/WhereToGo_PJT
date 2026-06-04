<template>
  <LandingPage v-if="!isLoggedIn" />

  <div v-else class="home-page">
    <aside
      class="home-sidebar"
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
                  <span class="progress-track">
                    <span
                      class="progress-fill"
                      :style="{ width: `${item.progress}%` }"
                    ></span>
                  </span>
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
                <span class="completed-date">{{ item.updated }}</span>
              </div>

              <span class="chevron">›</span>
            </button>
          </section>

          <div
            v-if="
              curriculumSearchKeyword.trim() &&
              filteredInProgress.length === 0 &&
              filteredCompleted.length === 0
            "
            class="empty-search"
          >
            검색 결과가 없습니다
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

    <div class="home-main">
      <header class="home-header">
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

      <main class="home-content">
        <section class="hero-section">
          <div class="hero-icon">
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

          <h2>무엇을 배우고 싶으신가요?</h2>

          <p>
            AI 교육 컨설턴트와 상담하며 나만의 맞춤 커리큘럼을 만들어보세요.
          </p>

          <div class="prompt-box">
            <textarea
              v-model="input"
              rows="3"
              placeholder="무엇을 배우고 싶나요?"
              @keydown="handleKeydown"
            ></textarea>

            <button
              type="button"
              class="send-button"
              :disabled="!input.trim()"
              aria-label="상담 시작"
              @click="handleSubmit"
            >
              <svg viewBox="0 0 24 24" class="icon">
                <path
                  d="M22 2L11 13"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  d="M22 2L15 22L11 13L2 9L22 2Z"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
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
import { useRoute, useRouter } from 'vue-router';
import LandingPage from '@/pages/user/LandingPage.vue';
import { clearAuthStorage, isAuthenticated } from '@/utils/auth';
import './HomePage.css';

const router = useRouter();
const route = useRoute();

const sidebarOpen = ref(false);
const input = ref('');
const curriculumSearchKeyword = ref('');
const isLoggedIn = ref(isAuthenticated());

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

const inProgressCurricula = [
  { id: '1', title: '데이터 분석 8주 로드맵', progress: 45, updated: '2일 전' },
  { id: '2', title: 'Django 백엔드 입문', progress: 20, updated: '5일 전' },
  { id: 'new', title: 'Backend Developer Portfolio', progress: 28, updated: '오늘' },
];

const completedCurricula = [
  { id: '3', title: 'Python 기초 완성', progress: 100, updated: '1주 전' },
];

const filterCurricula = (curricula) => {
  const keyword = curriculumSearchKeyword.value.trim().toLowerCase();

  if (!keyword) return curricula;

  return curricula.filter((item) =>
    item.title.toLowerCase().includes(keyword),
  );
};

const filteredInProgress = computed(() => filterCurricula(inProgressCurricula));
const filteredCompleted = computed(() => filterCurricula(completedCurricula));

const syncAuthState = () => {
  isLoggedIn.value = isAuthenticated();

  if (!isLoggedIn.value) {
    closeSidebar();
  }
};

const toggleSidebar = () => {
  syncAuthState();

  if (!isLoggedIn.value) return;

  sidebarOpen.value = !sidebarOpen.value;
};

const closeSidebar = () => {
  sidebarOpen.value = false;
};

const handleNavigate = (path) => {
  router.push(path);
  closeSidebar();
};

const handleSubmit = () => {
  const goal = input.value.trim();

  if (!goal) return;

  sessionStorage.setItem('initialLearningGoal', goal);
  router.push('/chat');
};

const handleKeydown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    handleSubmit();
  }
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
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEscKey);
  window.removeEventListener('storage', syncAuthState);
  window.removeEventListener('focus', syncAuthState);
});
</script>