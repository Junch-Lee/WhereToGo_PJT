<template>
  <div class="curriculum-result-page">
    <!-- Sidebar -->
    <aside
      class="result-sidebar"
      :class="{ 'is-open': sidebarOpen }"
      @click.stop
    >
      <div class="result-sidebar-inner">
        <!-- Logo Header -->
        <div class="result-sidebar-logo-section">
          <button
            class="result-sidebar-logo-button"
            type="button"
            @click="handleNavigate('/')"
          >
            <div class="result-sidebar-logo">
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
            </div>
          </button>
        </div>

        <!-- Search -->
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

        <!-- Main Menu -->
        <div class="result-sidebar-menu-section">
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
        </div>

        <!-- Curriculum Lists -->
        <div class="result-sidebar-content">
          <div v-if="isLoadingCurricula" class="result-empty-search">
            커리큘럼을 불러오는 중입니다...
          </div>

          <div v-else-if="curriculumLoadError" class="result-empty-search">
            커리큘럼 목록을 불러오지 못했습니다.
          </div>

          <div v-else-if="hasNoCurriculums" class="result-empty-search">
            아직 생성한 커리큘럼이 없습니다.
          </div>

          <div v-else-if="hasNoFilteredCurriculums" class="result-empty-search">
            검색 결과가 없습니다.
          </div>

          <div v-else>
            <section
              v-if="filteredInProgress.length > 0"
              class="result-curriculum-section"
            >
              <h3>진행 중인 커리큘럼</h3>

              <button
                v-for="item in filteredInProgress"
                :key="item.id"
                type="button"
                class="result-curriculum-item"
                @click="handleNavigate(`/curriculum/${item.id}`)"
              >
                <div class="result-curriculum-main">
                  <p>{{ item.title }}</p>

                  <div class="result-curriculum-meta">
                    <span class="result-sidebar-progress-track">
                      <span
                        class="result-sidebar-progress-fill"
                        :style="{ width: `${item.progress}%` }"
                      ></span>
                    </span>

                    <span>{{ item.updated }}</span>
                  </div>
                </div>

                <span class="result-chevron">›</span>
              </button>
            </section>

            <section
              v-if="filteredCompleted.length > 0"
              class="result-curriculum-section"
            >
              <h3>완료한 커리큘럼</h3>

              <button
                v-for="item in filteredCompleted"
                :key="item.id"
                type="button"
                class="result-curriculum-item completed"
                @click="handleNavigate(`/curriculum/${item.id}`)"
              >
                <div class="result-curriculum-main">
                  <p>{{ item.title }}</p>
                  <span class="result-completed-date">{{ item.updated }}</span>
                </div>

                <span class="result-chevron">›</span>
              </button>
            </section>
          </div>
        </div>

        <!-- Bottom -->
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

    <!-- Main -->
    <div class="result-main">
      <header class="result-header">
        <button
          type="button"
          class="logo-menu-button"
          aria-label="사이드바 열기"
          @click="toggleSidebar"
        >
          <span class="logo-menu-default">
            <div class="logo-menu-circle">
              <svg viewBox="0 0 24 24" class="logo-menu-icon">
                <path
                  d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2Zm3.86 6.14-2.12 6.36a1.5 1.5 0 0 1-.94.94l-6.36 2.12 2.12-6.36a1.5 1.5 0 0 1 .94-.94l6.36-2.12Z"
                  fill="currentColor"
                />
              </svg>
            </div>
          </span>

          <span class="logo-menu-hover">
            <svg viewBox="0 0 24 24" class="menu-hover-icon">
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
          <!-- Header -->
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

          <!-- A. Recommendation Summary -->
          <section class="result-card recommendation-card">
            <h3>{{ resultTitle }}</h3>

            <p>{{ recommendationReason }}</p>

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

          <!-- B. Why This Curriculum -->
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
                  d="M12 6v6l4 2"
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

          <!-- C. Curriculum Preview -->
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
                  <div class="week-main">
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

          <!-- D. Recommended Resources -->
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
                :key="resource.key || resource.name"
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

          <!-- E. Expected Schedule -->
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

          <!-- F. Risk / Adjustment Notice -->
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
              <p>{{ cautionNotice }}</p>
            </div>
          </section>

          <!-- G. Action Buttons -->
          <section class="result-actions">
            <button
              type="button"
              class="primary-action-button"
              :disabled="isSaving"
              @click="handleSaveAndStart"
            >
              {{ isSaving ? '저장 중...' : '저장하고 학습 시작하기' }}
            </button>

            <p
              v-if="saveMessage"
              class="result-save-message"
            >
              {{ saveMessage }}
            </p>

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
import { getMyCurriculums, saveGeneratedCurriculum } from '@/api/curriculumApi';
import { clearAuthStorage, isAuthenticated } from '@/utils/auth';
import './CurriculumResult.css';

const router = useRouter();
const route = useRoute();

const sidebarOpen = ref(false);
const curriculumSearchKeyword = ref('');
const curriculums = ref([]);
const isLoadingCurricula = ref(false);
const curriculumLoadError = ref('');
const generatedCurriculum = ref(null);
const isSaving = ref(false);
const saveMessage = ref('');

const fallbackSummaryInfo = [
  { label: '목표', value: '데이터 분석가 준비' },
  { label: '현재 수준', value: '기초' },
  { label: '학습 기간', value: '8주' },
  { label: '주간 학습 시간', value: '주 10시간' },
  { label: '최종 결과물', value: '데이터 분석 미니 프로젝트' },
];

const fallbackReasons = [
  '현재 수준이 기초이므로 Python 데이터 구조부터 시작합니다.',
  '목표가 데이터 분석가 준비이므로 Pandas와 시각화를 핵심 단계로 배치했습니다.',
  '주 10시간 학습 가능하므로 8주 안에 실습과 프로젝트까지 진행할 수 있도록 구성했습니다.',
  '통계 기초가 부족하므로 프로젝트 전에 핵심 통계 개념을 포함했습니다.',
];

const fallbackWeeklyPlan = [
  {
    week: 1,
    title: 'Python 기초 및 데이터 구조',
    topics: ['변수와 자료형', '조건문과 반복문', '리스트와 딕셔너리'],
    time: '10시간',
    difficulty: '쉬움',
    output: 'Python 기본 문법 이해',
  },
  {
    week: 2,
    title: 'Pandas 기초',
    topics: ['DataFrame 다루기', '데이터 필터링', '그룹화와 집계'],
    time: '10시간',
    difficulty: '보통',
    output: 'Pandas 기본 조작',
  },
  {
    week: 3,
    title: '데이터 정제와 전처리',
    topics: ['결측값 처리', '이상치 탐지', '데이터 변환'],
    time: '10시간',
    difficulty: '보통',
    output: '데이터 전처리 프로세스',
  },
  {
    week: 4,
    title: '데이터 시각화',
    topics: ['Matplotlib 기초', 'Seaborn 활용', '차트 커스터마이징'],
    time: '10시간',
    difficulty: '보통',
    output: '시각화 대시보드',
  },
  {
    week: 5,
    title: '통계 기초',
    topics: ['기술 통계', '확률 분포', '가설 검정'],
    time: '10시간',
    difficulty: '보통',
    output: '통계 분석 리포트',
  },
  {
    week: 6,
    title: '탐색적 데이터 분석',
    topics: ['EDA 프로세스', '인사이트 도출', '분석 보고서 작성'],
    time: '12시간',
    difficulty: '높음',
    output: 'EDA 프로젝트',
  },
  {
    week: 7,
    title: '미니 프로젝트 설계',
    topics: ['문제 정의', '데이터 수집', '분석 계획 수립'],
    time: '12시간',
    difficulty: '높음',
    output: '프로젝트 기획서',
  },
  {
    week: 8,
    title: '포트폴리오 정리',
    topics: ['프로젝트 구현', '결과 시각화', '문서화'],
    time: '15시간',
    difficulty: '높음',
    output: '포트폴리오 프로젝트',
  },
];

const fallbackResources = [
  {
    type: '실습 자료',
    name: 'Titanic 데이터셋 분석',
    time: '40분',
    difficulty: '보통',
    reason: '데이터 필터링과 집계를 직접 연습하기 좋습니다.',
  },
  {
    type: '영상',
    name: 'Pandas 핵심 개념 요약',
    time: '25분',
    difficulty: '쉬움',
    reason: 'DataFrame 구조를 시각적으로 이해할 수 있습니다.',
  },
  {
    type: '문서',
    name: 'Python 데이터 분석 가이드',
    time: '1시간',
    difficulty: '보통',
    reason: '전체 분석 프로세스를 체계적으로 학습할 수 있습니다.',
  },
  {
    type: '퀴즈',
    name: '통계 기초 점검 퀴즈',
    time: '15분',
    difficulty: '보통',
    reason: '핵심 통계 개념 이해도를 빠르게 확인할 수 있습니다.',
  },
  {
    type: '프로젝트',
    name: 'COVID-19 데이터 분석',
    time: '3시간',
    difficulty: '높음',
    reason: '실전 데이터 분석 경험을 쌓을 수 있습니다.',
  },
];

const difficultyLabels = {
  beginner: '입문',
  intermediate: '보통',
  advanced: '심화',
};

const learningStyleLabels = {
  lecture: '강의 중심',
  project: '프로젝트 중심',
  balanced: '균형형',
};

const userProfile = computed(() => generatedCurriculum.value?.user_profile || {});
const generatedSteps = computed(() => generatedCurriculum.value?.steps || []);

const resultTitle = computed(
  () => generatedCurriculum.value?.title || 'AI 맞춤 커리큘럼',
);

const recommendationReason = computed(
  () =>
    generatedCurriculum.value?.recommendation_reason ||
    '입력한 목표와 학습 조건을 바탕으로 AI가 학습 경로를 구성했습니다.',
);

const summaryInfo = computed(() => {
  if (!generatedCurriculum.value) return fallbackSummaryInfo;

  return [
    { label: '목표', value: userProfile.value.goal },
    {
      label: '현재 수준',
      value:
        difficultyLabels[userProfile.value.difficulty_level] ||
        userProfile.value.difficulty_level,
    },
    { label: '학습 기간', value: `${userProfile.value.target_weeks || '-'}주` },
    {
      label: '주간 학습 시간',
      value: `주 ${userProfile.value.weekly_available_hours || userProfile.value.weekly_hours || '-'}시간`,
    },
    {
      label: '학습 방식',
      value:
        learningStyleLabels[userProfile.value.preferred_learning_style] ||
        userProfile.value.preferred_learning_style,
    },
  ].filter((item) => item.value !== undefined && item.value !== null && item.value !== '');
});

const reasons = computed(() => {
  if (!generatedCurriculum.value) return fallbackReasons;

  const parts = recommendationReason.value
    .split(/\n|(?<=다\.)\s+|(?<=요\.)\s+|(?<=\.)\s+/)
    .map((item) => item.trim())
    .filter(Boolean);

  return parts.length > 0 ? parts : [recommendationReason.value];
});

const weeklyPlan = computed(() => {
  if (!generatedCurriculum.value) return fallbackWeeklyPlan;

  return generatedSteps.value.map((step, index) => {
    const topics = [
      step.target_topic_slug ? `핵심 주제: ${step.target_topic_slug}` : '',
      step.prerequisite_note ? `선수 지식: ${step.prerequisite_note}` : '',
    ].filter(Boolean);

    return {
      week: step.order || index + 1,
      title: step.title || `학습 단계 ${index + 1}`,
      topics: topics.length > 0 ? topics : ['AI가 추천한 단계별 학습 내용'],
      time: `${step.estimated_hours || 0}시간`,
      difficulty:
        difficultyLabels[step.difficulty_level] ||
        step.difficulty_level ||
        '보통',
      output: step.description || '단계별 학습 결과를 정리합니다.',
    };
  });
});

const resources = computed(() => {
  if (!generatedCurriculum.value) return fallbackResources;

  const items = [];

  generatedSteps.value.forEach((step, stepIndex) => {
    (step.preview_resources || []).forEach((resource, resourceIndex) => {
      const providerName = resource.provider_name ? ` · ${resource.provider_name}` : '';

      items.push({
        key: `resource-preview-${stepIndex}-${resourceIndex}`,
        type: '학습 자료',
        name: resource.title,
        time: `${step.estimated_hours || 0}시간`,
        difficulty:
          difficultyLabels[step.difficulty_level] ||
          step.difficulty_level ||
          '보통',
        reason: `${stepIndex + 1}단계 학습 목표와 연결된 AI 추천 자료입니다${providerName}.`,
      });
    });

    (step.preview_courses || []).forEach((course, courseIndex) => {
      const universityName = course.university_name ? ` · ${course.university_name}` : '';

      items.push({
        key: `course-preview-${stepIndex}-${courseIndex}`,
        type: '강의',
        name: course.course_name,
        time: `${step.estimated_hours || 0}시간`,
        difficulty:
          difficultyLabels[step.difficulty_level] ||
          step.difficulty_level ||
          '보통',
        reason: `${stepIndex + 1}단계 학습 목표와 연결된 AI 추천 강의입니다${universityName}.`,
      });
    });
  });

  return items;
});

const cautionNotice = computed(() => {
  if (!generatedCurriculum.value) {
    return '학습 중 어렵게 느껴지는 단계가 있다면 커리큘럼을 재조정할 수 있습니다.';
  }

  const prerequisiteNotes = generatedSteps.value
    .map((step) => step.prerequisite_note)
    .filter(Boolean);

  if (prerequisiteNotes.length > 0) {
    return prerequisiteNotes.join(' ');
  }

  return recommendationReason.value;
});

const totalEstimatedHours = computed(() =>
  generatedSteps.value.reduce(
    (total, step) => total + Number(step.estimated_hours || 0),
    0,
  ),
);

const expectedEndDate = computed(() => {
  const weeks = Number(userProfile.value.target_weeks || 0);
  if (!weeks) return '-';

  const date = new Date();
  date.setDate(date.getDate() + weeks * 7);
  return date.toLocaleDateString('ko-KR');
});

const scheduleInfo = computed(() => {
  const weeks = userProfile.value.target_weeks || '-';
  const weeklyHours = userProfile.value.weekly_available_hours || userProfile.value.weekly_hours || '-';
  const averageDailyMinutes = totalEstimatedHours.value
    ? Math.round((totalEstimatedHours.value * 60) / Math.max(Number(weeks) * 7, 1))
    : 0;

  return [
    { label: '총 학습 기간', value: `${weeks}주` },
    { label: '주간 학습 시간', value: `주 ${weeklyHours}시간` },
    { label: '예상 완료일', value: expectedEndDate.value },
    {
      label: '하루 평균 학습량',
      value: averageDailyMinutes ? `${averageDailyMinutes}분` : '-',
    },
  ];
});

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
      <path d="M19.4 15a1.8 1.8 0 0 0 .36 1.98l.04.04a2.1 2.1 0 0 1-2.97 2.97l-.04-.04a1.8 1.8 0 0 0-1.98-.36 1.8 1.8 0 0 0-1.1 1.65V21a2.1 2.1 0 1 1-4.2 0v-.06a1.8 1.8 0 0 0-1.1-1.65 1.8 1.8 0 0 0-1.98.36l-.04.04a2.1 2.1 0 0 1-2.97-2.97l.04-.04A1.8 1.8 0 0 0 4.6 15a1.8 1.8 0 0 0-1.65-1.1H3a2.1 2.1 1 1 0 0-4.2h.06A1.8 1.8 0 0 0 4.7 8.6a1.8 1.8 0 0 0-.36-1.98l-.04-.04a2.1 2.1 0 0 1 2.97-2.97l.04.04a1.8 1.8 0 0 0 1.98.36 1.8 1.8 0 0 0 1.1-1.65V3a2.1 2.1 0 1 1 4.2 0v.06a1.8 1.8 0 0 0 1.1 1.65 1.8 1.8 0 0 0 1.98-.36l.04-.04a2.1 2.1 0 0 1 2.97 2.97l-.04.04A1.8 1.8 0 0 0 19.4 9c.18.67.7 1.1 1.35 1.1H21a2.1 2.1 0 1 1 0 4.2h-.06A1.8 1.8 0 0 0 19.4 15Z" fill="none" stroke="currentColor" stroke-width="2"/>
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

const handleSaveAndStart = async () => {
  if (isSaving.value) return;

  if (!generatedCurriculum.value) {
    saveMessage.value = '저장할 AI 커리큘럼 생성 결과가 없습니다. 다시 생성해 주세요.';
    return;
  }

  isSaving.value = true;
  saveMessage.value = '';

  try {
    const response = await saveGeneratedCurriculum(generatedCurriculum.value);
    const curriculumId = response.curriculum_id || response.curriculum?.id;

    if (!curriculumId) {
      saveMessage.value = '커리큘럼은 저장됐지만 상세 페이지 정보를 찾지 못했습니다.';
      return;
    }

    sessionStorage.setItem('generated_curriculum_id', String(curriculumId));
    sessionStorage.setItem('saved_curriculum_response', JSON.stringify(response));
    router.push(`/curriculum/${curriculumId}`);
  } catch (error) {
    saveMessage.value =
      error?.message || '커리큘럼 저장 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.';
  } finally {
    isSaving.value = false;
  }
};

const handleRegenerate = () => {
  router.push('/interview/summary');
};

const handleEditAnswers = () => {
  router.push('/interview/summary');
};

const getDifficultyClass = (difficulty) => {
  if (difficulty === '쉬움' || difficulty === '입문') return 'difficulty-easy';
  if (difficulty === '보통') return 'difficulty-normal';
  return 'difficulty-hard';
};

const loadGeneratedCurriculum = () => {
  const savedResponse = sessionStorage.getItem('generated_curriculum_response');

  if (!savedResponse) {
    router.replace('/interview/summary');
    return;
  }

  try {
    const parsed = JSON.parse(savedResponse);
    generatedCurriculum.value = parsed.generated_curriculum || parsed.curriculum || null;
  } catch (error) {
    generatedCurriculum.value = null;
  }

  if (!generatedCurriculum.value) {
    sessionStorage.removeItem('generated_curriculum_response');
    router.replace('/interview/summary');
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
  window.addEventListener('focus', loadCurriculums);

  loadGeneratedCurriculum();
  loadCurriculums();
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEscKey);
  window.removeEventListener('focus', loadCurriculums);
});
</script>
