<template>
  <div class="learning-dashboard-page">
    <UserSidebar :open="sidebarOpen" @close="closeSidebar" />

    <div class="learning-dashboard-layout">
      <header class="learning-dashboard-header">
        <BrandMenuButton @click="toggleSidebar" />
        <h1>학습 대시보드</h1>
      </header>

      <main class="learning-dashboard-main">
        <div class="learning-dashboard-container">
          <section v-if="isLoading" class="learning-state-card">
            <p>학습 현황을 불러오는 중입니다.</p>
          </section>

          <section v-else-if="errorMessage" class="learning-state-card error">
            <p>{{ errorMessage }}</p>
            <button type="button" class="learning-outline-button" @click="loadDashboard">
              다시 시도
            </button>
          </section>

          <template v-else>
            <section class="learning-summary-grid" aria-label="학습 현황 요약">
              <article
                v-for="(stat, index) in summaryStats"
                :key="stat.label"
                class="learning-summary-item"
                :style="{ '--animation-order': index }"
              >
                <div class="learning-summary-label">
                  <span v-html="stat.icon" aria-hidden="true"></span>
                  <span>{{ stat.label }}</span>
                </div>
                <strong>{{ stat.value }}</strong>
                <small>{{ stat.hint }}</small>
              </article>
            </section>

            <section class="learning-focus-section">
              <div class="learning-section-header">
                <div>
                  <p>Today</p>
                  <h2>오늘 이어서 학습할 항목</h2>
                </div>
              </div>

              <article v-if="focusCurriculum" class="learning-focus-card">
                <div class="learning-focus-main">
                  <div>
                    <span :class="['learning-status-pill', statusClass[focusCurriculum.status]]">
                      {{ statusLabel[focusCurriculum.status] }}
                    </span>
                    <h3>{{ focusCurriculum.title }}</h3>
                    <p>{{ focusStepDescription }}</p>
                  </div>

                  <div class="learning-focus-progress">
                    <div class="learning-progress-meta">
                      <span>전체 진행률</span>
                      <strong>{{ focusCurriculum.progress }}%</strong>
                    </div>
                    <div class="learning-progress-track">
                      <div
                        class="learning-progress-fill"
                        :style="{ width: `${focusCurriculum.progress}%` }"
                      ></div>
                    </div>
                  </div>
                </div>

                <div v-if="focusStep" class="learning-focus-aside">
                  <span>현재 Step</span>
                  <strong>Step {{ focusStep.order }}. {{ focusStep.title }}</strong>
                  <p>예상 {{ focusStep.estimatedHours }}시간</p>
                  <button
                    type="button"
                    class="learning-primary-button"
                    @click="navigateToCurriculum(focusCurriculum.id)"
                  >
                    이어가기
                  </button>
                </div>
              </article>

              <article v-else class="learning-empty-card">
                <h3>진행 중인 커리큘럼이 없습니다.</h3>
                <p>생성한 커리큘럼을 시작하면 이곳에 이어서 학습할 Step이 표시됩니다.</p>
              </article>
            </section>

            <section class="learning-dashboard-grid">
              <div class="learning-dashboard-column">
                <section class="learning-dashboard-section">
                  <div class="learning-section-header">
                    <div>
                      <p>Progress</p>
                      <h2>커리큘럼 진행 현황</h2>
                    </div>
                  </div>

                  <div v-if="dashboardCurricula.length" class="learning-curriculum-list">
                    <button
                      v-for="curriculum in dashboardCurricula"
                      :key="curriculum.id"
                      type="button"
                      class="learning-curriculum-item"
                      @click="navigateToCurriculum(curriculum.id)"
                    >
                      <div class="learning-curriculum-copy">
                        <div class="learning-curriculum-title">
                          <strong>{{ curriculum.title }}</strong>
                          <span :class="['learning-status-pill small', statusClass[curriculum.status]]">
                            {{ statusLabel[curriculum.status] }}
                          </span>
                        </div>
                        <p>
                          {{ curriculum.completedSteps }} / {{ curriculum.totalSteps }} Step 완료
                          · 목표 {{ curriculum.targetWeeks }}주
                          · 주 {{ curriculum.weeklyHours }}시간
                        </p>
                        <div class="learning-progress-track compact">
                          <div
                            class="learning-progress-fill"
                            :style="{ width: `${curriculum.progress}%` }"
                          ></div>
                        </div>
                      </div>

                      <div class="learning-curriculum-action">
                        <strong>{{ curriculum.progress }}%</strong>
                        <span>{{ curriculum.updatedLabel }}</span>
                      </div>
                    </button>
                  </div>

                  <div v-else class="learning-empty-card compact">
                    <p>아직 생성한 커리큘럼이 없습니다.</p>
                  </div>
                </section>

                <section class="learning-dashboard-section">
                  <div class="learning-section-header">
                    <div>
                      <p>Roadmap</p>
                      <h2>현재 로드맵</h2>
                    </div>
                  </div>

                  <div v-if="focusCurriculum?.steps?.length" class="learning-roadmap-list">
                    <article
                      v-for="step in focusCurriculum.steps"
                      :key="step.id"
                      :class="['learning-roadmap-item', step.status.toLowerCase()]"
                    >
                      <span class="learning-roadmap-marker">{{ getStepIcon(step.status) }}</span>
                      <div>
                        <strong>Step {{ step.order }}. {{ step.title }}</strong>
                        <p>{{ step.statusLabel }} · 예상 {{ step.estimatedHours }}시간</p>
                      </div>
                    </article>
                  </div>

                  <div v-else class="learning-empty-card compact">
                    <p>진행할 로드맵이 아직 없습니다.</p>
                  </div>
                </section>
              </div>

              <aside class="learning-dashboard-column">
                <section class="learning-dashboard-section">
                  <div class="learning-section-header">
                    <div>
                      <p>Plan</p>
                      <h2>학습 계획</h2>
                    </div>
                  </div>

                  <div class="learning-plan-list">
                    <article class="learning-plan-item">
                      <span>예상 총 학습</span>
                      <strong>{{ totalEstimatedHours }}시간</strong>
                    </article>
                    <article class="learning-plan-item">
                      <span>계획 일정</span>
                      <strong>{{ scheduleStats.total }}개</strong>
                    </article>
                    <article class="learning-plan-item">
                      <span>완료 일정</span>
                      <strong>{{ scheduleStats.done }}개</strong>
                    </article>
                    <article class="learning-plan-item">
                      <span>일정 이행률</span>
                      <strong>{{ scheduleCompletionRate }}%</strong>
                    </article>
                  </div>
                </section>

                <section class="learning-dashboard-section">
                  <div class="learning-section-header">
                    <div>
                      <p>Materials</p>
                      <h2>학습 자료 구성</h2>
                    </div>
                  </div>

                  <div class="learning-resource-list">
                    <article
                      v-for="resource in resourceStats"
                      :key="resource.label"
                      class="learning-resource-item"
                    >
                      <span>{{ resource.label }}</span>
                      <strong>{{ resource.count }}</strong>
                    </article>
                  </div>
                </section>

                <section class="learning-dashboard-section">
                  <div class="learning-section-header">
                    <div>
                      <p>Activity</p>
                      <h2>최근 학습 활동</h2>
                    </div>
                  </div>

                  <div v-if="recentActivities.length" class="learning-activity-list">
                    <article
                      v-for="activity in recentActivities"
                      :key="activity.key"
                      class="learning-activity-item"
                    >
                      <span aria-hidden="true"></span>
                      <div>
                        <strong>{{ activity.title }}</strong>
                        <p>{{ activity.meta }}</p>
                      </div>
                    </article>
                  </div>

                  <div v-else class="learning-empty-card compact">
                    <p>아직 기록된 학습 활동이 없습니다.</p>
                  </div>
                </section>
              </aside>
            </section>
          </template>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import './LearningDashboard.css'
import '@/assets/styles/user-shell.css'

import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import UserSidebar from '@/components/user/UserSidebar.vue'
import BrandMenuButton from '@/components/user/BrandMenuButton.vue'
import { getCurriculumDetail, getMyCurriculums } from '@/api/curriculumApi'

const router = useRouter()

const sidebarOpen = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const curricula = ref([])

const statusLabel = {
  NOT_STARTED: '시작 전',
  IN_PROGRESS: '진행 중',
  PAUSED: '일시정지',
  COMPLETED: '완료',
}

const statusClass = {
  NOT_STARTED: 'status-muted',
  IN_PROGRESS: 'status-active',
  PAUSED: 'status-paused',
  COMPLETED: 'status-done',
}

const icons = {
  curriculum: '<svg viewBox="0 0 24 24"><path d="M5 4h14v16H5z"></path><path d="M8 8h8M8 12h8M8 16h5"></path></svg>',
  progress: '<svg viewBox="0 0 24 24"><path d="M4 19V5"></path><path d="M4 19h16"></path><path d="M8 16v-4M12 16V8M16 16v-7"></path></svg>',
  check: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"></circle><path d="m8.2 12.1 2.4 2.5 5.4-5.5"></path></svg>',
  clock: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"></circle><path d="M12 7.5V12l3 2"></path></svg>',
}

const dashboardCurricula = computed(() =>
  curricula.value
    .map(mapDashboardCurriculum)
    .sort((a, b) => statusSortValue(a.status) - statusSortValue(b.status)),
)

const activeCurricula = computed(() =>
  dashboardCurricula.value.filter((item) =>
    ['IN_PROGRESS', 'PAUSED'].includes(item.status),
  ),
)

const focusCurriculum = computed(() =>
  activeCurricula.value[0] ||
  dashboardCurricula.value.find((item) => item.status === 'NOT_STARTED') ||
  dashboardCurricula.value[0] ||
  null,
)

const focusStep = computed(() => {
  if (!focusCurriculum.value) return null

  return focusCurriculum.value.steps.find((step) => step.status === 'IN_PROGRESS') ||
    focusCurriculum.value.steps.find((step) => step.status === 'PENDING') ||
    focusCurriculum.value.steps[0] ||
    null
})

const focusStepDescription = computed(() =>
  focusStep.value?.description ||
  focusCurriculum.value?.goal ||
  '현재 이어서 학습할 단계가 준비되어 있습니다.',
)

const totalCompletedSteps = computed(() =>
  dashboardCurricula.value.reduce((sum, item) => sum + item.completedSteps, 0),
)

const totalStepCount = computed(() =>
  dashboardCurricula.value.reduce((sum, item) => sum + item.totalSteps, 0),
)

const averageProgress = computed(() => {
  if (!dashboardCurricula.value.length) return 0

  const total = dashboardCurricula.value.reduce((sum, item) => sum + item.progress, 0)
  return Math.round(total / dashboardCurricula.value.length)
})

const totalEstimatedHours = computed(() =>
  dashboardCurricula.value.reduce((sum, item) => sum + item.estimatedHours, 0),
)

const scheduleStats = computed(() => {
  const schedules = curricula.value.flatMap((item) => item.current_step_schedules || [])

  return {
    total: schedules.length,
    done: schedules.filter((schedule) => normalizeStatus(schedule.status) === 'DONE').length,
  }
})

const scheduleCompletionRate = computed(() => {
  if (scheduleStats.value.total === 0) return 0
  return Math.round((scheduleStats.value.done / scheduleStats.value.total) * 100)
})

const summaryStats = computed(() => [
  {
    label: '전체 커리큘럼',
    value: dashboardCurricula.value.length,
    hint: `${activeCurricula.value.length}개 진행 중`,
    icon: icons.curriculum,
  },
  {
    label: '평균 진행률',
    value: `${averageProgress.value}%`,
    hint: `${totalCompletedSteps.value} / ${totalStepCount.value} Step 완료`,
    icon: icons.progress,
  },
  {
    label: '완료 커리큘럼',
    value: dashboardCurricula.value.filter((item) => item.status === 'COMPLETED').length,
    hint: '상태가 완료인 커리큘럼',
    icon: icons.check,
  },
  {
    label: '예상 학습 시간',
    value: `${totalEstimatedHours.value}h`,
    hint: '전체 Step 예상 시간 합계',
    icon: icons.clock,
  },
])

const resourceStats = computed(() => {
  const counts = new Map()

  dashboardCurricula.value.forEach((curriculum) => {
    curriculum.steps.forEach((step) => {
      step.resources.forEach((resource) => {
        counts.set(resource.type, (counts.get(resource.type) || 0) + 1)
      })
      if (step.courses.length > 0) {
        counts.set('추천 강의/과목', (counts.get('추천 강의/과목') || 0) + step.courses.length)
      }
    })
  })

  const entries = Array.from(counts.entries()).map(([label, count]) => ({ label, count }))
  return entries.length ? entries : [{ label: '추천 자료', count: 0 }]
})

const recentActivities = computed(() => {
  const activities = []

  dashboardCurricula.value.forEach((curriculum) => {
    curriculum.steps.forEach((step) => {
      if (!step.completedAt && !step.lastStudiedAt) return

      activities.push({
        key: `${curriculum.id}-${step.id}-${step.completedAt || step.lastStudiedAt}`,
        title: `${curriculum.title} · Step ${step.order} ${step.statusLabel}`,
        meta: formatDateTime(step.completedAt || step.lastStudiedAt),
        dateValue: new Date(step.completedAt || step.lastStudiedAt).getTime(),
      })
    })
  })

  return activities
    .filter((activity) => Number.isFinite(activity.dateValue))
    .sort((a, b) => b.dateValue - a.dateValue)
    .slice(0, 5)
})

onMounted(() => {
  loadDashboard()
})

async function loadDashboard() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const list = await getMyCurriculums()
    const items = Array.isArray(list) ? list : []
    const details = await Promise.all(
      items.map((item) =>
        getCurriculumDetail(item.id).catch(() => item),
      ),
    )

    curricula.value = details
  } catch (error) {
    errorMessage.value = error?.message || '학습 대시보드를 불러오지 못했습니다.'
  } finally {
    isLoading.value = false
  }
}

function mapDashboardCurriculum(item) {
  const status = normalizeCurriculumStatus(item.status)
  const steps = (item.steps || []).map(mapStep)
  const completedSteps = item.completed_step_count ?? steps.filter((step) => step.status === 'COMPLETED').length
  const totalSteps = item.total_step_count ?? steps.length

  return {
    id: item.id,
    title: item.title || '이름 없는 커리큘럼',
    goal: item.goal || '',
    status,
    progress: normalizeProgress(item.progress_percent, status),
    completedSteps,
    totalSteps,
    targetWeeks: item.target_weeks || 0,
    weeklyHours: item.weekly_available_hours || 0,
    estimatedHours: steps.reduce((sum, step) => sum + step.estimatedHours, 0),
    updatedLabel: formatRelativeDate(item.updated_at || item.created_at),
    steps,
  }
}

function mapStep(step) {
  const progress = step.step_progress || {}
  const status = normalizeStepStatus(step.status, progress.status)

  return {
    id: step.id,
    order: step.order ?? step.step_order ?? 0,
    title: step.title || '학습 단계',
    description: step.description || '',
    estimatedHours: Number(step.estimated_hours || 0),
    status,
    statusLabel: stepStatusLabel(status),
    completedAt: progress.completed_at,
    lastStudiedAt: progress.last_studied_at,
    resources: (step.resources || []).map(mapResource),
    courses: step.courses || [],
  }
}

function mapResource(resource) {
  return {
    type: normalizeResourceType(resource.resource_type || resource.type || '자료'),
  }
}

function normalizeCurriculumStatus(status) {
  const value = normalizeStatus(status)
  if (value === 'ACTIVE' || value === 'IN_PROGRESS') return 'IN_PROGRESS'
  if (value === 'DRAFT' || value === 'NOT_STARTED') return 'NOT_STARTED'
  if (value === 'PAUSED') return 'PAUSED'
  if (value === 'COMPLETED') return 'COMPLETED'
  return 'NOT_STARTED'
}

function normalizeStepStatus(status, progressStatus) {
  const value = normalizeStatus(status || progressStatus)
  if (value === 'COMPLETED') return 'COMPLETED'
  if (value === 'IN_PROGRESS' || value === 'ACTIVE' || value === 'PAUSED') return 'IN_PROGRESS'
  return 'PENDING'
}

function normalizeStatus(status) {
  return String(status || '')
    .trim()
    .replace(/[\s-]+/g, '_')
    .toUpperCase()
}

function normalizeProgress(progress, status) {
  const numericProgress = Number(progress)
  if (Number.isFinite(numericProgress)) {
    return Math.min(100, Math.max(0, Math.round(numericProgress)))
  }

  return status === 'COMPLETED' ? 100 : 0
}

function normalizeResourceType(type) {
  const value = String(type || '').toLowerCase()
  if (value.includes('video') || value.includes('lecture') || value.includes('course')) return '강의'
  if (value.includes('practice') || value.includes('exercise')) return '실습'
  if (value.includes('document') || value.includes('text') || value.includes('docs')) return '문서'
  return type || '자료'
}

function stepStatusLabel(status) {
  if (status === 'COMPLETED') return '완료'
  if (status === 'IN_PROGRESS') return '진행 중'
  return '대기 중'
}

function getStepIcon(status) {
  if (status === 'COMPLETED') return '✓'
  if (status === 'IN_PROGRESS') return '●'
  return '○'
}

function statusSortValue(status) {
  return {
    IN_PROGRESS: 1,
    PAUSED: 2,
    NOT_STARTED: 3,
    COMPLETED: 4,
  }[status] || 5
}

function formatRelativeDate(value) {
  if (!value) return '-'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'

  const diffDays = Math.floor((Date.now() - date.getTime()) / (1000 * 60 * 60 * 24))
  if (diffDays <= 0) return '오늘'
  if (diffDays < 7) return `${diffDays}일 전`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}주 전`
  return `${Math.floor(diffDays / 30)}개월 전`
}

function formatDateTime(value) {
  if (!value) return '-'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'

  return date.toLocaleString('ko-KR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

function closeSidebar() {
  sidebarOpen.value = false
}

function navigateToCurriculum(curriculumId) {
  router.push(`/curriculum/${curriculumId}`)
}
</script>
