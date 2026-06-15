<template>
  <div class="curriculum-result-page">
    <aside
      class="result-sidebar"
      :class="{ 'is-open': sidebarOpen }"
      @click.stop
    >
      <div class="result-sidebar-inner">
        <div class="result-sidebar-logo-section">
          <button
            class="result-sidebar-logo-button"
            type="button"
            @click="handleNavigate('/')"
          >
            <div class="result-sidebar-logo-icon">
              <svg viewBox="0 0 24 24" class="icon">
                <path
                  d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2Zm3.86 6.14-2.12 6.36a1.5 1.5 0 0 1-.94.94l-6.36 2.12 2.12-6.36a1.5 1.5 0 0 1 .94-.94l6.36-2.12Z"
                  fill="currentColor"
                />
              </svg>
            </div>

            <div class="result-sidebar-logo-text">
              <strong>Where To Go</strong>
              <span>AI 학습 컨설턴트</span>
            </div>
          </button>
        </div>

        <div class="result-sidebar-search-section">
          <div class="result-sidebar-search-box">
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

        <nav class="result-sidebar-nav">
          <button
            v-for="item in menuItems"
            :key="item.path"
            type="button"
            class="result-sidebar-nav-item"
            :class="{ active: route.path === item.path }"
            @click="handleNavigate(item.path)"
          >
            <span class="nav-icon" v-html="item.icon"></span>
            <span>{{ item.label }}</span>
          </button>
        </nav>

        <div class="result-sidebar-content">
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
            <section
              v-if="filteredInProgress.length > 0"
              class="curriculum-section"
            >
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

            <section
              v-if="filteredCompleted.length > 0"
              class="curriculum-section"
            >
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

        <div class="result-sidebar-bottom">
          <button
            type="button"
            class="result-sidebar-nav-item"
            @click="handleNavigate('/settings')"
          >
            <span class="nav-icon" v-html="icons.settings"></span>
            <span>설정</span>
          </button>

          <button
            type="button"
            class="result-sidebar-nav-item"
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
      class="result-sidebar-backdrop"
      @click="closeSidebar"
    ></div>

    <div class="result-main">
      <header class="result-header">
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

        <h1>커리큘럼 생성 완료</h1>
      </header>

      <main class="result-content">
        <div class="result-container">
          <section class="result-hero">
            <div class="result-hero-icon">
              <svg viewBox="0 0 24 24" class="hero-icon-svg">
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

            <h2>맞춤형 커리큘럼이 생성되었어요</h2>

            <p>
              입력한 목표와 학습 조건을 바탕으로 AI가 학습 경로를 구성했습니다.
            </p>
          </section>

          <section class="result-card recommendation-card">
            <h3>{{ curriculumTitle }}</h3>

            <p>
              {{ curriculumDescription }}
            </p>

            <div class="summary-grid">
              <div
                v-for="info in summaryInfo"
                :key="info.label"
                class="summary-box"
              >
                <p>{{ info.label }}</p>
                <strong>{{ info.value }}</strong>
              </div>
            </div>
          </section>

          <section class="result-card">
            <div class="section-title-row">
              <svg viewBox="0 0 24 24" class="section-icon">
                <circle
                  cx="12"
                  cy="12"
                  r="9"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                />
                <path
                  d="M12 7v5l3 2"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>

              <h3>이 커리큘럼을 추천한 이유</h3>
            </div>

            <ul class="reason-list">
              <li
                v-for="reason in reasons"
                :key="reason"
              >
                <span></span>
                <p>{{ reason }}</p>
              </li>
            </ul>
          </section>

          <section class="result-card">
            <div class="section-title-row">
              <svg viewBox="0 0 24 24" class="section-icon">
                <path
                  d="M4 19.5V5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5Z"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linejoin="round"
                />
                <path
                  d="M8 7h8M8 11h8"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>

              <h3>주차별 학습 로드맵</h3>
            </div>

            <div class="weekly-list">
              <article
                v-for="week in weeklyPlan"
                :key="week.week"
                class="week-card"
              >
                <div class="week-header">
                  <div>
                    <h4>{{ week.week }}주차: {{ week.title }}</h4>

                    <div class="week-meta">
                      <span>
                        <svg viewBox="0 0 24 24" class="mini-icon">
                          <circle
                            cx="12"
                            cy="12"
                            r="9"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                          />
                          <path
                            d="M12 7v5l3 2"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            stroke-linecap="round"
                          />
                        </svg>

                        {{ week.time }}
                      </span>

                      <span
                        class="difficulty-badge"
                        :class="getDifficultyClass(week.difficulty)"
                      >
                        {{ week.difficulty }}
                      </span>
                    </div>
                  </div>
                </div>

                <ul class="topic-list">
                  <li
                    v-for="topic in week.topics"
                    :key="topic"
                  >
                    <span></span>
                    {{ topic }}
                  </li>
                </ul>

                <p class="week-output">
                  주요 결과물: {{ week.output }}
                </p>
              </article>
            </div>
          </section>

          <section class="result-card">
            <div class="section-title-row">
              <svg viewBox="0 0 24 24" class="section-icon">
                <path
                  d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linejoin="round"
                />
                <path
                  d="M14 2v6h6M8 13h8M8 17h5"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>

              <h3>추천 학습 자료</h3>
            </div>

            <div class="resource-list">
              <article
                v-for="resource in resources"
                :key="resource.name"
                class="resource-card"
              >
                <div class="resource-header">
                  <div class="resource-main">
                    <span class="resource-type">
                      {{ resource.type }}
                    </span>

                    <strong>{{ resource.name }}</strong>
                  </div>

                  <div class="resource-meta">
                    <span>
                      <svg viewBox="0 0 24 24" class="mini-icon">
                        <circle
                          cx="12"
                          cy="12"
                          r="9"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                        />
                        <path
                          d="M12 7v5l3 2"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                        />
                      </svg>

                      {{ resource.time }}
                    </span>

                    <span
                      class="difficulty-badge"
                      :class="getDifficultyClass(resource.difficulty)"
                    >
                      {{ resource.difficulty }}
                    </span>
                  </div>
                </div>

                <p>
                  추천 이유: {{ resource.reason }}
                </p>
              </article>
            </div>
          </section>

          <section class="result-card">
            <div class="section-title-row">
              <svg viewBox="0 0 24 24" class="section-icon">
                <rect
                  x="3"
                  y="4"
                  width="18"
                  height="18"
                  rx="2"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                />
                <path
                  d="M16 2v4M8 2v4M3 10h18"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>

              <h3>예상 학습 일정</h3>
            </div>

            <div class="schedule-grid">
              <div
                v-for="item in scheduleInfo"
                :key="item.label"
                class="schedule-item"
              >
                <p>{{ item.label }}</p>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </section>

          <section class="notice-card">
            <svg viewBox="0 0 24 24" class="notice-icon">
              <path
                d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linejoin="round"
              />
              <path
                d="M12 9v4M12 17h.01"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              />
            </svg>

            <div>
              <h4>AI가 주의 깊게 본 부분</h4>
              <p>
                현재 수준과 학습 가능 시간을 고려해 초반에는 기초 개념과 실습을 충분히 배치했습니다.
                학습 중 어렵게 느껴지면 커리큘럼을 재조정할 수 있습니다.
              </p>
            </div>
          </section>

          <section class="result-actions">
            <button
              type="button"
              class="primary-action-button"
              @click="handleSaveAndStart"
            >
              저장하고 학습 시작하기
            </button>

            <div class="secondary-action-row">
              <button
                type="button"
                class="secondary-action-button"
                @click="handleRegenerate"
              >
                다시 생성하기
              </button>

              <button
                type="button"
                class="secondary-action-button"
                @click="handleEditAnswers"
              >
                답변 수정하기
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
import './CurriculumResult.css';

const router = useRouter();
const route = useRoute();

const sidebarOpen = ref(false);
const curriculumSearchKeyword = ref('');
const curriculums = ref([]);
const isLoadingCurricula = ref(false);
const curriculumLoadError = ref('');
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
    4: '4주',
    8: '8주',
    12: '12주',
    24: '24주',
  },
  weekly_available_hours: {
    5: '주 5시간 이하',
    7: '주 7시간',
    10: '주 10~15시간',
    20: '주 20시간 이상',
  },
  preferred_learning_style: {
    lecture: '강의 중심',
    project: '프로젝트 중심',
    balanced: '균형',
  },
};

const goalText = computed(() => interviewPayload.value.goal || '데이터 분석');

const targetWeeksText = computed(() => {
  const value = interviewPayload.value.target_weeks;
  return valueLabels.target_weeks[value] || '8주';
});

const weeklyHoursText = computed(() => {
  const value = interviewPayload.value.weekly_available_hours;
  return valueLabels.weekly_available_hours[value] || '주 10시간';
});

const difficultyText = computed(() => {
  const value = interviewPayload.value.difficulty_level;
  return valueLabels.difficulty_level[value] || '기초 있음';
});

const purposeText = computed(() => {
  const value = interviewPayload.value.purpose;
  return valueLabels.purpose[value] || '포트폴리오';
});

const learningStyleText = computed(() => {
  const value = interviewPayload.value.preferred_learning_style;
  return valueLabels.preferred_learning_style[value] || '균형';
});

const curriculumTitle = computed(() => {
  return `${goalText.value} 맞춤형 ${targetWeeksText.value} 커리큘럼`;
});

const curriculumDescription = computed(() => {
  return `${goalText.value} 학습을 위해 기초 개념, 핵심 실습, 결과물 제작까지 단계적으로 구성한 과정입니다.`;
});

const summaryInfo = computed(() => [
  { label: '목표', value: goalText.value },
  { label: '현재 수준', value: difficultyText.value },
  { label: '학습 기간', value: targetWeeksText.value },
  { label: '주간 학습 시간', value: weeklyHoursText.value },
  { label: '학습 방식', value: learningStyleText.value },
]);

const reasons = computed(() => [
  `현재 수준이 '${difficultyText.value}'이므로 초반에는 핵심 개념과 기초 실습을 배치했습니다.`,
  `목표가 '${goalText.value}'이므로 관련 실습과 결과물 중심으로 학습 경로를 구성했습니다.`,
  `${weeklyHoursText.value} 기준으로 무리 없이 따라갈 수 있도록 주차별 학습량을 조정했습니다.`,
  `학습 목적이 '${purposeText.value}'이므로 추천 자료와 과제의 방향을 그에 맞게 구성했습니다.`,
]);

const weeklyPlan = [
  {
    week: 1,
    title: '기초 개념 정리',
    topics: ['학습 목표 이해', '핵심 용어 정리', '기본 환경 준비'],
    time: '7~10시간',
    difficulty: '쉬움',
    output: '기초 개념 요약 노트',
  },
  {
    week: 2,
    title: '핵심 문법과 기본 사용법',
    topics: ['기본 문법', '필수 도구 사용', '간단한 예제 실습'],
    time: '7~10시간',
    difficulty: '쉬움',
    output: '기초 실습 결과물',
  },
  {
    week: 3,
    title: '핵심 기능 실습',
    topics: ['대표 기능 학습', '예제 분석', '작은 단위 실습'],
    time: '10시간',
    difficulty: '보통',
    output: '기능별 실습 정리',
  },
  {
    week: 4,
    title: '문제 해결 연습',
    topics: ['문제 정의', '해결 흐름 설계', '반복 실습'],
    time: '10시간',
    difficulty: '보통',
    output: '문제 해결 기록',
  },
  {
    week: 5,
    title: '미니 프로젝트 설계',
    topics: ['주제 선정', '요구사항 정리', '구현 계획 수립'],
    time: '10~12시간',
    difficulty: '보통',
    output: '프로젝트 기획서',
  },
  {
    week: 6,
    title: '미니 프로젝트 구현',
    topics: ['핵심 기능 구현', '자료 적용', '결과물 개선'],
    time: '12시간',
    difficulty: '높음',
    output: '미니 프로젝트 초안',
  },
  {
    week: 7,
    title: '결과물 고도화',
    topics: ['오류 수정', '완성도 개선', '문서화'],
    time: '12시간',
    difficulty: '높음',
    output: '완성 프로젝트',
  },
  {
    week: 8,
    title: '정리와 포트폴리오화',
    topics: ['회고 정리', '학습 내용 요약', '발표 자료 구성'],
    time: '10시간',
    difficulty: '보통',
    output: '최종 포트폴리오',
  },
];

const resources = [
  {
    type: '강의',
    name: '핵심 개념 입문 강의',
    time: '40분',
    difficulty: '쉬움',
    reason: '처음 시작할 때 전체 흐름을 빠르게 잡기 좋습니다.',
  },
  {
    type: '실습 자료',
    name: '기초 실습 예제 모음',
    time: '1시간',
    difficulty: '쉬움',
    reason: '개념을 바로 손으로 확인할 수 있습니다.',
  },
  {
    type: '문서',
    name: '학습 로드맵 참고 문서',
    time: '30분',
    difficulty: '보통',
    reason: '각 단계에서 무엇을 배워야 하는지 정리되어 있습니다.',
  },
  {
    type: '퀴즈',
    name: '기초 이해도 점검 퀴즈',
    time: '15분',
    difficulty: '보통',
    reason: '다음 단계로 넘어가기 전 이해도를 확인할 수 있습니다.',
  },
  {
    type: '프로젝트',
    name: '미니 프로젝트 템플릿',
    time: '3시간',
    difficulty: '높음',
    reason: '학습 내용을 결과물로 연결하기 좋습니다.',
  },
];

const scheduleInfo = computed(() => [
  { label: '총 학습 기간', value: targetWeeksText.value },
  { label: '주간 학습 시간', value: weeklyHoursText.value },
  { label: '예상 완료일', value: expectedEndDate.value },
  { label: '하루 평균 학습량', value: averageDailyTime.value },
]);

const expectedEndDate = computed(() => {
  const weeks = Number(interviewPayload.value.target_weeks || 8);
  const date = new Date();

  date.setDate(date.getDate() + weeks * 7);

  return date.toLocaleDateString('ko-KR');
});

const averageDailyTime = computed(() => {
  const weeklyHours = Number(interviewPayload.value.weekly_available_hours || 10);
  const dailyHours = weeklyHours / 7;

  if (dailyHours < 1) {
    return `약 ${Math.round(dailyHours * 60)}분`;
  }

  return `약 ${dailyHours.toFixed(1)}시간`;
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

const handleSaveAndStart = () => {
  const generatedCurriculum = {
    title: curriculumTitle.value,
    summary: curriculumDescription.value,
    weeks: weeklyPlan,
    resources,
    created_at: new Date().toISOString(),
  };

  sessionStorage.setItem(
    'generated_curriculum',
    JSON.stringify(generatedCurriculum),
  );

  router.push('/learning');
};

const handleRegenerate = () => {
  window.location.reload();
};

const handleEditAnswers = () => {
  router.push('/interview/summary');
};

const getDifficultyClass = (difficulty) => {
  if (difficulty === '쉬움') return 'difficulty-easy';
  if (difficulty === '보통') return 'difficulty-normal';
  return 'difficulty-hard';
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

  if (savedPayload) {
    try {
      interviewPayload.value = JSON.parse(savedPayload);
    } catch (error) {
      interviewPayload.value = {};
    }
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
