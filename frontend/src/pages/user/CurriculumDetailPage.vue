<template>
  <div class="curriculum-detail-page">
    <aside class="detail-sidebar" :class="{ 'is-open': sidebarOpen }" @click.stop>
      <div class="sidebar-inner">
        <div class="sidebar-logo-section">
          <button class="sidebar-logo-button" type="button" @click="navigateTo('/')">
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
              <span>AI 학습 커넥트</span>
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
            @click="navigateTo(item.path)"
          >
            <span class="nav-icon" v-html="item.icon"></span>
            <span>{{ item.label }}</span>
          </button>
        </nav>

        <div class="sidebar-content">
          <section class="curriculum-section">
            <h3>진행 중인 커리큘럼</h3>

            <div v-if="sidebarLoading" class="empty-search">커리큘럼을 불러오는 중입니다.</div>

            <button
              v-for="item in filteredCurriculums"
              :key="item.id"
              type="button"
              class="curriculum-item"
              :class="{ active: String(route.params.id) === String(item.id) }"
              @click="navigateTo(`/curriculum/${item.id}`)"
            >
              <div class="curriculum-main">
                <p>{{ item.title }}</p>

                <div class="curriculum-meta">
                  <span class="mini-progress-track">
                    <span
                      class="mini-progress-fill"
                      :style="{ width: `${getListProgress(item)}%` }"
                    ></span>
                  </span>
                  <span>{{ formatDate(item.updated_at || item.created_at) }}</span>
                </div>
              </div>

              <span class="chevron">›</span>
            </button>
          </section>

          <div
            v-if="!sidebarLoading && curriculumSearchKeyword.trim() && filteredCurriculums.length === 0"
            class="empty-search"
          >
            검색 결과가 없습니다.
          </div>

          <div
            v-if="!sidebarLoading && !curriculumSearchKeyword.trim() && filteredCurriculums.length === 0"
            class="empty-search"
          >
            아직 생성한 커리큘럼이 없습니다.
          </div>
        </div>

        <div class="sidebar-bottom">
          <button type="button" class="sidebar-nav-item" @click="navigateTo('/settings')">
            <span class="nav-icon" v-html="icons.settings"></span>
            <span>설정</span>
          </button>

          <button type="button" class="sidebar-nav-item" @click="handleLogout">
            <span class="nav-icon" v-html="icons.logout"></span>
            <span>로그아웃</span>
          </button>
        </div>
      </div>
    </aside>

    <div v-if="sidebarOpen" class="sidebar-backdrop" @click="closeSidebar"></div>

    <div class="detail-main">
      <header class="detail-topbar">
        <div class="topbar-left">
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

          <h1>{{ curriculum?.title || '커리큘럼 상세' }}</h1>
        </div>
      </header>

      <main class="detail-content">
        <section v-if="loading" class="main-card state-card">
          <h2>커리큘럼 정보를 불러오는 중입니다.</h2>
        </section>

        <section v-else-if="errorMessage" class="main-card state-card">
          <h2>{{ errorTitle }}</h2>
          <p>{{ errorMessage }}</p>
          <button type="button" class="secondary-large" @click="loadPageData">
            다시 시도
          </button>
        </section>

        <template v-else-if="curriculum">
          <section class="main-card hero-card">
            <div class="hero-header">
              <div>
                <h2>{{ curriculum.title }}</h2>

                <p class="goal-text">
                  <span class="target-icon">◎</span>
                  목표: {{ curriculum.goal }}
                </p>
              </div>

              <span class="status-pill" :class="statusClass">
                {{ getStatusLabel(curriculum.status) }}
              </span>
            </div>

            <div class="info-grid">
              <div class="info-box">
                <p>생성일</p>
                <strong>{{ formatDate(curriculum.created_at) }}</strong>
              </div>

              <div class="info-box">
                <p>수강 시작일</p>
                <strong>{{ formatDate(curriculum.started_at) || '아직 시작 전' }}</strong>
              </div>

              <div class="info-box">
                <p>완료일</p>
                <strong>{{ formatDate(curriculum.completed_at) || '아직 완료 전' }}</strong>
              </div>

              <div class="info-box">
                <p>현재 단계</p>
                <strong>{{ currentStepText }}</strong>
              </div>
            </div>

            <div class="overall-progress">
              <div class="progress-title-row">
                <strong>전체 진행률</strong>
                <span>{{ overallProgress }}%</span>
              </div>

              <div class="progress-track">
                <div class="progress-fill" :style="{ width: `${overallProgress}%` }"></div>
              </div>

              <p>총 {{ curriculum.target_weeks }}주 · 주 {{ curriculum.weekly_available_hours }}시간 기준</p>
            </div>
          </section>

          <section class="ai-message-card">
            <div class="sparkle-icon">
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

            <p>{{ statusMessage }}</p>
          </section>

          <section v-if="hasCurrentStep" class="main-card current-step-card">
            <div class="section-title-row">
              <h3>현재 진행 중인 단계</h3>
              <span class="blue-status">{{ getStepStatusLabel(currentStepProgress.status) }}</span>
            </div>

            <div class="current-step-summary">
              <p>{{ currentStep.step_order }}단계</p>
              <h4>{{ currentStep.title }}</h4>
              <span>{{ currentStep.description }}</span>
            </div>

            <div class="step-progress-block">
              <div class="progress-title-row">
                <strong>단계 진행률</strong>
                <span>{{ currentStepProgress.progress_rate }}%</span>
              </div>

              <div class="progress-track">
                <div
                  class="progress-fill"
                  :style="{ width: `${currentStepProgress.progress_rate}%` }"
                ></div>
              </div>
            </div>

            <div class="metric-grid">
              <div class="metric-box">
                <p>예상 소요 시간</p>
                <strong>{{ currentStep.estimated_hours }}시간</strong>
              </div>

              <div class="metric-box">
                <p>실제 학습 시간</p>
                <strong>{{ minutesToText(currentStepProgress.actual_minutes) }}</strong>
              </div>

              <div class="metric-box">
                <p>남은 예상 시간</p>
                <strong>약 {{ minutesToText(remainingMinutes) }}</strong>
              </div>

              <div class="metric-box">
                <p>마지막 학습일</p>
                <strong>{{ formatDate(currentStepProgress.last_studied_at) || '기록 없음' }}</strong>
              </div>
            </div>
          </section>

          <section v-if="curriculum.status === 'DRAFT'" class="main-card draft-card">
            <h3>학습 시작 전 안내</h3>
            <p>
              아직 학습 일정은 생성되지 않았어요. 학습을 시작하면 첫 번째 단계에 대한
              일정만 먼저 생성됩니다.
            </p>

            <button
              type="button"
              class="primary-action"
              disabled
              title="학습 시작 API 연결이 필요한 버튼입니다."
            >
              첫 단계 시작하기
            </button>
          </section>

          <section v-if="curriculum.status === 'PAUSED'" class="main-card draft-card">
            <h3>현재 커리큘럼이 일시정지되어 있어요.</h3>
            <p>
              재개하면 완료된 기록은 유지되고, 미완료 일정만 다시 조정할 수 있습니다.
            </p>
          </section>

          <section v-if="showCurrentStepTables" class="main-card table-card">
            <h3>현재 단계 학습 일정</h3>

            <p class="section-description">
              현재 단계 진행 row에 연결된 일정만 표시합니다.
            </p>

            <div v-if="currentStepSchedules.length" class="detail-table">
              <div class="table-row table-head">
                <span>회차</span>
                <span>예정일</span>
                <span>계획 시간</span>
                <span>상태</span>
              </div>

              <div
                v-for="schedule in currentStepSchedules"
                :key="schedule.id"
                class="table-row"
              >
                <span>{{ schedule.sequence_no }}회차</span>
                <span>{{ formatDate(schedule.scheduled_date) }}</span>
                <span>{{ schedule.planned_hours }}시간</span>
                <span>
                  <span class="small-status" :class="getScheduleStatusClass(schedule.status)">
                    {{ getScheduleStatusLabel(schedule.status) }}
                  </span>
                </span>
              </div>
            </div>

            <p v-else class="section-description">현재 단계에 생성된 학습 일정이 없습니다.</p>
          </section>

          <section v-if="showCurrentStepTables" class="main-card table-card">
            <h3>실제 학습 기록</h3>

            <p class="section-description">
              현재 단계 진행 row에 연결된 실제 학습 기록만 표시합니다.
            </p>

            <div v-if="currentStepLearningProgresses.length" class="detail-table record-table">
              <div class="table-row table-head">
                <span>학습일</span>
                <span>연결 일정</span>
                <span>계획 / 실제</span>
                <span>상태</span>
                <span>메모</span>
              </div>

              <div
                v-for="record in currentStepLearningProgresses"
                :key="record.id"
                class="table-row"
              >
                <span>{{ formatDate(record.studied_at) || '-' }}</span>
                <span>{{ getScheduleLabel(record.learning_schedule_id) }}</span>
                <span>{{ getRecordTimeText(record) }}</span>
                <span>
                  <span class="small-status" :class="getProgressStatusClass(record.status)">
                    {{ getProgressStatusLabel(record.status) }}
                  </span>
                </span>
                <span>{{ record.memo || '-' }}</span>
              </div>
            </div>

            <p v-else class="section-description">아직 기록된 실제 학습 내역이 없습니다.</p>
          </section>

          <section v-if="curriculum.status === 'COMPLETED'" class="main-card completed-card">
            <h3>학습 완료 요약</h3>
            <p>전체 커리큘럼이 완료되었습니다. 아래 단계 목록에서 완료 기록을 확인할 수 있습니다.</p>

            <div class="metric-grid">
              <div class="metric-box">
                <p>전체 시작일</p>
                <strong>{{ formatDate(curriculum.started_at) || '-' }}</strong>
              </div>

              <div class="metric-box">
                <p>전체 완료일</p>
                <strong>{{ formatDate(curriculum.completed_at) || '-' }}</strong>
              </div>

              <div class="metric-box">
                <p>완료 단계</p>
                <strong>{{ completedStepCount }}단계</strong>
              </div>

              <div class="metric-box">
                <p>최종 진행률</p>
                <strong>{{ overallProgress }}%</strong>
              </div>
            </div>
          </section>

          <section class="main-card steps-card">
            <h3>커리큘럼 단계</h3>

            <div class="step-list">
              <article
                v-for="step in mappedSteps"
                :key="step.id"
                class="curriculum-step"
                :class="{
                  active: step.id === expandedStepId || step.isCurrent,
                  waiting: step.statusClass === 'waiting',
                }"
              >
                <button type="button" class="step-header" @click="toggleStep(step.id)">
                  <div class="step-left">
                    <span class="step-icon" :class="step.statusClass">
                      <svg v-if="step.statusClass === 'active'" viewBox="0 0 24 24" class="icon">
                        <circle
                          cx="12"
                          cy="12"
                          r="9"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                        />
                      </svg>

                      <svg v-else viewBox="0 0 24 24" class="icon">
                        <rect
                          x="5"
                          y="11"
                          width="14"
                          height="10"
                          rx="2"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                        />
                        <path
                          d="M8 11V8a4 4 0 0 1 8 0v3"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                        />
                      </svg>
                    </span>

                    <div class="step-title-block">
                      <div class="step-title-line">
                        <h4>{{ step.step_order }}단계. {{ step.title }}</h4>
                        <span class="step-status" :class="step.statusClass">
                          {{ step.statusText }}
                        </span>
                      </div>

                      <div class="step-meta">
                        <span>예상 {{ step.estimated_hours }}시간</span>
                        <span :class="['difficulty', getDifficultyClass(step.difficulty_level)]">
                          {{ getDifficultyLabel(step.difficulty_level) }}
                        </span>
                        <span>{{ step.scheduleText }}</span>
                      </div>
                    </div>
                  </div>

                  <span class="step-arrow">{{ expandedStepId === step.id ? '⌃' : '⌄' }}</span>
                </button>

                <div v-if="expandedStepId === step.id" class="step-body">
                  <p>{{ step.description }}</p>

                  <div class="step-topic-block">
                    <h5>핵심 주제</h5>
                    <ul>
                      <li v-for="topic in getStepTopics(step)" :key="topic">{{ topic }}</li>
                    </ul>
                  </div>

                  <div v-if="step.resources.length" class="step-topic-block">
                    <h5>추천 자료</h5>
                    <ul>
                      <li v-for="resource in step.resources" :key="resource.id">
                        {{ resource.title }} · {{ resource.provider_name || '제공자 미상' }}
                      </li>
                    </ul>
                  </div>

                  <div v-if="step.courses.length" class="step-topic-block">
                    <h5>참고 강의</h5>
                    <ul>
                      <li v-for="course in step.courses" :key="course.id">
                        {{ course.course_name }}
                        <span v-if="course.university_name"> · {{ course.university_name }}</span>
                      </li>
                    </ul>
                  </div>

                  <p class="prerequisite">
                    선수 조건: {{ step.prerequisite_note || '별도 선수 조건 없음' }}
                  </p>
                </div>
              </article>
            </div>
          </section>

          <section class="main-card action-card">
            <button
              v-if="curriculum.status === 'ACTIVE'"
              type="button"
              class="primary-large"
              disabled
              title="이어서 학습하기 API 연결이 필요합니다."
            >
              이어서 학습하기
            </button>

            <button
              v-if="curriculum.status === 'ACTIVE'"
              type="button"
              class="secondary-large"
              disabled
              title="일시정지 API 연결이 필요합니다."
            >
              일시정지
            </button>

            <button
              v-if="curriculum.status === 'PAUSED'"
              type="button"
              class="primary-large"
              disabled
              title="학습 재개 API 연결이 필요합니다."
            >
              학습 재개하기
            </button>

            <button
              v-if="curriculum.status === 'DRAFT'"
              type="button"
              class="primary-large"
              disabled
              title="학습 시작 API 연결이 필요합니다."
            >
              학습 시작하기
            </button>

            <button
              v-if="curriculum.status === 'COMPLETED'"
              type="button"
              class="primary-large"
              disabled
              title="학습 리포트 API 연결이 필요합니다."
            >
              학습 리포트 보기
            </button>

            <button type="button" class="secondary-large" @click="navigateTo('/chat')">
              AI 튜터에게 질문하기
            </button>
          </section>
        </template>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getCurriculumDetail, getMyCurriculums } from '@/api/curriculumApi';
import { clearAuthStorage } from '@/utils/auth';
import './CurriculumDetailPage.css';

const router = useRouter();
const route = useRoute();

const sidebarOpen = ref(false);
const curriculumSearchKeyword = ref('');
const curriculum = ref(null);
const curriculums = ref([]);
const loading = ref(false);
const sidebarLoading = ref(false);
const errorMessage = ref('');
const errorStatus = ref(null);
const expandedStepId = ref(null);

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

const filteredCurriculums = computed(() => {
  const keyword = curriculumSearchKeyword.value.trim().toLowerCase();
  const list = curriculums.value.filter((item) => item.status !== 'CANCELLED');

  if (!keyword) return list;

  return list.filter((item) => item.title.toLowerCase().includes(keyword));
});

const currentStepProgress = computed(() => curriculum.value?.current_step_progress || null);
const currentStepSchedules = computed(() => curriculum.value?.current_step_schedules || []);
const currentStepLearningProgresses = computed(
  () => curriculum.value?.current_step_learning_progresses || [],
);

const currentStep = computed(() => {
  const steps = curriculum.value?.steps || [];
  const progressStepId = currentStepProgress.value?.curriculum_step_id;
  const currentStepId = progressStepId || curriculum.value?.current_step_id;

  return steps.find((step) => step.id === currentStepId) || null;
});

const hasCurrentStep = computed(() => Boolean(currentStep.value && currentStepProgress.value));

const showCurrentStepTables = computed(() =>
  ['ACTIVE', 'PAUSED'].includes(curriculum.value?.status) && hasCurrentStep.value,
);

const completedStepCount = computed(() =>
  (curriculum.value?.steps || []).filter((step) => step.step_progress?.status === 'COMPLETED').length,
);

const overallProgress = computed(() => {
  const steps = curriculum.value?.steps || [];

  if (!curriculum.value || curriculum.value.status === 'DRAFT') return 0;
  if (curriculum.value.status === 'COMPLETED') return 100;
  if (!steps.length) return currentStepProgress.value?.progress_rate || 0;

  // 전체 진행률은 단계 완료 개수 기준으로 계산한다.
  return Math.round((completedStepCount.value / steps.length) * 100);
});

const remainingMinutes = computed(() => {
  if (!currentStep.value || !currentStepProgress.value) return 0;

  return Math.max(
    0,
    currentStep.value.estimated_hours * 60 - currentStepProgress.value.actual_minutes,
  );
});

const currentStepText = computed(() => {
  if (!currentStep.value) return curriculum.value?.status === 'DRAFT' ? '시작 전' : '현재 단계 없음';

  return `${currentStep.value.step_order}단계 ${currentStep.value.title}`;
});

const mappedSteps = computed(() =>
  (curriculum.value?.steps || []).map((step) => {
    const status = step.step_progress?.status || 'NOT_STARTED';

    return {
      ...step,
      statusClass: getStepStatusClass(status),
      statusText: getStepStatusLabel(status),
      scheduleText: step.step_progress ? '일정 생성됨' : '아직 일정 없음',
      isCurrent: currentStep.value?.id === step.id,
    };
  }),
);

const statusClass = computed(() => (curriculum.value?.status || 'DRAFT').toLowerCase());

const statusMessage = computed(() => {
  if (curriculum.value?.status === 'DRAFT') {
    return 'AI가 커리큘럼 초안을 구성했어요. 학습을 시작하면 첫 번째 단계 일정이 생성됩니다.';
  }

  if (curriculum.value?.status === 'PAUSED') {
    return '현재 학습이 일시정지되어 있어요. 완료된 기록은 유지되고 미완료 일정만 조정 대상입니다.';
  }

  if (curriculum.value?.status === 'COMPLETED') {
    return '커리큘럼을 완료했어요. 단계별 기록을 바탕으로 다음 학습 방향을 정리할 수 있습니다.';
  }

  return 'AI가 현재 학습 흐름을 분석했어요. 최근 진행 상황을 기준으로 다음 학습 단계를 추천합니다.';
});

const errorTitle = computed(() => {
  if (errorStatus.value === 401) return '로그인이 필요합니다.';
  if (errorStatus.value === 404) return '커리큘럼을 찾을 수 없습니다.';

  return '커리큘럼 정보를 불러오지 못했습니다.';
});

async function loadPageData() {
  const curriculumId = route.params.id;

  loading.value = true;
  sidebarLoading.value = true;
  errorMessage.value = '';
  errorStatus.value = null;

  try {
    const [detailData, listData] = await Promise.all([
      getCurriculumDetail(curriculumId),
      getMyCurriculums(),
    ]);

    curriculum.value = detailData;
    curriculums.value = listData;
    expandedStepId.value = detailData.steps?.[0]?.id || null;
  } catch (error) {
    curriculum.value = null;
    errorStatus.value = error.status || null;
    errorMessage.value = getFriendlyErrorMessage(error);
  } finally {
    loading.value = false;
    sidebarLoading.value = false;
  }
}

function getFriendlyErrorMessage(error) {
  if (error.status === 401) return '로그인이 필요합니다.';
  if (error.status === 404) return '커리큘럼을 찾을 수 없습니다.';

  return error.message || '잠시 후 다시 시도해주세요.';
}

function getStatusLabel(status) {
  return {
    DRAFT: '초안',
    ACTIVE: '진행 중',
    PAUSED: '일시정지',
    COMPLETED: '완료',
    CANCELLED: '중단됨',
  }[status] || status;
}

function getStepStatusClass(status) {
  return {
    IN_PROGRESS: 'active',
    PAUSED: 'paused',
    COMPLETED: 'completed',
    SKIPPED: 'skipped',
    NOT_STARTED: 'waiting',
  }[status] || 'waiting';
}

function getStepStatusLabel(status) {
  return {
    NOT_STARTED: '대기 중',
    IN_PROGRESS: '진행 중',
    PAUSED: '일시정지',
    COMPLETED: '완료',
    SKIPPED: '건너뜀',
  }[status] || '대기 중';
}

function getScheduleStatusLabel(status) {
  return {
    PLANNED: '예정',
    DONE: '완료',
    MISSED: '놓침',
    CANCELLED: '취소됨',
    RESCHEDULED: '재조정됨',
  }[status] || status;
}

function getScheduleStatusClass(status) {
  return {
    DONE: 'done',
    PLANNED: 'planned',
    MISSED: 'missed',
    CANCELLED: 'cancelled',
    RESCHEDULED: 'rescheduled',
  }[status] || 'planned';
}

function getProgressStatusLabel(status) {
  return {
    COMPLETED: '완료',
    IN_PROGRESS: '진행 중',
    PARTIAL: '일부 완료',
  }[status] || status;
}

function getProgressStatusClass(status) {
  return {
    COMPLETED: 'done',
    IN_PROGRESS: 'planned',
    PARTIAL: 'rescheduled',
  }[status] || 'planned';
}

function getDifficultyLabel(difficulty) {
  return {
    beginner: '쉬움',
    intermediate: '보통',
    advanced: '어려움',
  }[difficulty] || difficulty || '보통';
}

function getDifficultyClass(difficulty) {
  return {
    beginner: 'easy',
    intermediate: 'medium',
    advanced: 'hard',
  }[difficulty] || 'medium';
}

function getStepTopics(step) {
  if (step.target_topic?.name) return [step.target_topic.name];

  return ['주제 정보 없음'];
}

function getScheduleLabel(scheduleId) {
  const schedule = currentStepSchedules.value.find((item) => item.id === scheduleId);
  if (!schedule) return '-';

  return `${schedule.sequence_no}회차`;
}

function getRecordTimeText(record) {
  const schedule = currentStepSchedules.value.find((item) => item.id === record.learning_schedule_id);
  const plannedText = schedule ? `계획 ${schedule.planned_hours}시간` : '계획 -';

  return `${plannedText} / 실제 ${minutesToText(record.actual_minutes)}`;
}

function getListProgress(item) {
  if (item.status === 'COMPLETED') return 100;
  if (item.status === 'DRAFT') return 0;

  return 0;
}

function minutesToText(minutes = 0) {
  if (minutes < 60) return `${minutes}분`;

  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;

  return rest ? `${hours}시간 ${rest}분` : `${hours}시간`;
}

function formatDate(value) {
  if (!value) return '';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value).replaceAll('-', '.');

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  return `${year}.${month}.${day}`;
}

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value;
};

const closeSidebar = () => {
  sidebarOpen.value = false;
};

const navigateTo = (path) => {
  router.push(path);
  closeSidebar();
};

const handleLogout = () => {
  clearAuthStorage();
  router.push('/');
};

const toggleStep = (stepId) => {
  expandedStepId.value = expandedStepId.value === stepId ? null : stepId;
};

const handleEscKey = (event) => {
  if (event.key === 'Escape' && sidebarOpen.value) {
    closeSidebar();
  }
};

watch(
  () => route.params.id,
  () => {
    loadPageData();
  },
  { immediate: true },
);

onMounted(() => {
  window.addEventListener('keydown', handleEscKey);
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEscKey);
});
</script>
