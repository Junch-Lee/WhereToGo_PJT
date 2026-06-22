<template>
  <div class="curriculum-page">
    <UserSidebar :open="sidebarOpen" @close="closeSidebar" />

    <div class="main-layout">
      <header class="page-header">
        <BrandMenuButton @click="toggleSidebar" />

        <h1 class="page-title">{{ curriculum?.title || '커리큘럼 상세' }}</h1>
      </header>

      <main class="page-main">
        <div class="content-wrap">
          <section v-if="loading" class="summary-card page-state-card">
            <p>커리큘럼 정보를 불러오는 중입니다.</p>
          </section>

          <section v-else-if="errorMessage" class="summary-card page-state-card error">
            <p>{{ errorMessage }}</p>
            <button
              class="outline-button"
              :disabled="actionLoading"
              @click="loadPageData"
            >
              다시 시도
            </button>
          </section>

          <template v-else-if="curriculum">
            <section class="summary-card">
              <div class="summary-header">
                <div>
                  <h2 class="summary-title">{{ curriculum.title }}</h2>
                  <p class="summary-description">{{ curriculumDescription }}</p>
                </div>

                <span :class="['status-pill', curriculumStatusClass[curriculumStatus]]">
                  {{ curriculumStatusLabel[curriculumStatus] }}
                </span>
              </div>

              <div class="progress-block">
                <div class="progress-info">
                  <span>{{ completedCount }} / {{ totalCount }} Step 완료</span>
                  <strong>{{ progressPct }}%</strong>
                </div>

                <div class="progress-track">
                  <div
                    class="progress-fill"
                    :style="{ width: `${progressPct}%` }"
                  ></div>
                </div>
              </div>

              <button
                v-if="isCurriculumNotStarted"
                class="primary-button"
                :disabled="actionLoading"
                @click="handleStart"
              >
                <span>▶</span>
                학습 시작하기
              </button>

              <div v-else-if="isCurriculumInProgress" class="button-row">
                <button
                  class="primary-button"
                  :disabled="actionLoading"
                  @click="handleContinue"
                >
                  <span>▶</span>
                  학습 이어가기
                </button>

                <button
                  class="outline-button"
                  :disabled="actionLoading"
                  @click="handlePause"
                >
                  <span>Ⅱ</span>
                  일시정지
                </button>
              </div>

              <button
                v-else-if="isCurriculumPaused"
                class="primary-button"
                :disabled="actionLoading"
                @click="handleResume"
              >
                <span>▶</span>
                학습 재개하기
              </button>

              <p v-else-if="isCurriculumCompleted" class="complete-text">학습 완료</p>
            </section>

            <div v-if="toastMessage" class="toast">
              {{ toastMessage }}
            </div>

            <section
              v-if="isCurriculumInProgress && currentStep"
              class="current-step-card"
            >
              <p class="current-step-label">현재 학습 중인 단계</p>

              <div class="current-step-header">
                <h3>Step {{ currentStep.order }}. {{ currentStep.title }}</h3>

                <div class="current-step-meta">
                  <span>예상 {{ currentStep.estimatedHours }}시간</span>

                  <span :class="['difficulty-pill', difficultyClass[currentStep.difficulty]]">
                    {{ currentStep.difficulty }}
                  </span>
                </div>
              </div>

              <div class="goal-box">
                <p>학습 목표</p>
                <span>{{ currentStep.description }}</span>
              </div>

              <div v-if="currentStep.resources.length > 0" class="resource-block">
                <p class="resource-title">추천 학습 자료</p>

                <ul class="resource-list">
                  <li
                    v-for="resource in currentStep.resources"
                    :key="resource.id"
                    class="resource-item"
                  >
                    <span :class="['resource-type', resourceTypeClass[resource.type] || 'resource-muted']">
                      {{ resource.type }}
                    </span>

                    <span class="resource-label">{{ resource.label }}</span>
                    <a
                      v-if="isValidExternalUrl(resource.url)"
                      :href="resource.url"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="resource-open-link"
                      :aria-label="`${resource.label} 열기`"
                      title="새 탭에서 열기"
                    >
                      ↗
                    </a>
                  </li>
                </ul>
              </div>

              <div class="button-row">
                <button
                  v-if="hasValidCurrentStepResourceUrl"
                  class="outline-card-button"
                  :disabled="actionLoading"
                  @click="openFirstCurrentStepResource"
                >
                  학습 자료 보기
                </button>

                <button
                  class="primary-button"
                  :disabled="actionLoading"
                  @click="handleCompleteStep"
                >
                  Step 완료하기
                </button>
              </div>
            </section>

            <section v-if="isCurriculumPaused" class="paused-banner">
              <p class="paused-title">현재 학습이 일시정지되어 있습니다.</p>

              <p v-if="currentStep" class="paused-description">
                진행 중이던 단계: Step {{ currentStep.order }}. {{ currentStep.title }}
              </p>

              <button
                class="pause-resume-button"
                :disabled="actionLoading"
                @click="handleResume"
              >
                <span>▶</span>
                학습 재개하기
              </button>
            </section>

            <section v-if="isCurriculumCompleted" class="completion-banner">
              <p class="completion-title">커리큘럼을 모두 완료했습니다.</p>
              <p class="completion-description">
                총 {{ totalCount }}개 Step을 모두 학습했습니다. 수고하셨습니다.
              </p>
            </section>

            <section class="step-list-card">
              <h3 class="step-list-title">전체 학습 단계</h3>

              <div class="step-list">
                <article
                  v-for="step in steps"
                  :key="step.id"
                  :class="['step-item', { active: step.status === 'IN_PROGRESS' }]"
                >
                  <button class="step-toggle" @click="toggleStep(step.id)">
                    <span
                      :class="[
                        'step-state-icon',
                        {
                          completed: step.status === 'COMPLETED',
                          progress: step.status === 'IN_PROGRESS',
                          pending: step.status === 'PENDING'
                        }
                      ]"
                    >
                      {{ getStepIcon(step.status) }}
                    </span>

                    <div class="step-toggle-content">
                      <div class="step-title-row">
                        <span :class="['step-name', { muted: step.status === 'PENDING' }]">
                          Step {{ step.order }}. {{ step.title }}
                        </span>

                        <span :class="['step-status-badge', stepStatusClass[step.status]]">
                          {{ stepStatusLabel[step.status] }}
                        </span>
                      </div>

                      <span class="step-time">약 {{ step.estimatedHours }}시간</span>
                    </div>

                    <span class="step-chevron">
                      {{ expandedStepId === step.id ? '⌃' : '⌄' }}
                    </span>
                  </button>

                  <div v-if="expandedStepId === step.id" class="step-detail">
                    <p class="step-description">{{ step.description }}</p>

                    <div v-if="step.resources.length > 0">
                      <p class="step-resource-title">추천 학습 자료</p>

                      <ul class="step-resource-list">
                        <li
                          v-for="resource in step.resources"
                          :key="resource.id"
                          class="step-resource-item"
                        >
                          <span :class="['resource-type small', resourceTypeClass[resource.type] || 'resource-muted']">
                            {{ resource.type }}
                          </span>

                          <span>{{ resource.label }}</span>
                          <a
                            v-if="isValidExternalUrl(resource.url)"
                            :href="resource.url"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="resource-open-link small"
                            :aria-label="`${resource.label} 열기`"
                            title="새 탭에서 열기"
                          >
                            ↗
                          </a>
                        </li>
                      </ul>
                    </div>
                  </div>
                </article>
              </div>
            </section>
          </template>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import './CurriculumDetailPage.css'
import '@/assets/styles/user-shell.css'

import { computed, onMounted, ref, watch } from 'vue'
import UserSidebar from '@/components/user/UserSidebar.vue'
import BrandMenuButton from '@/components/user/BrandMenuButton.vue'
import { useRoute, useRouter } from 'vue-router'
import {
  completeCurriculumStep,
  getCurriculumDetail,
  getMyCurriculums,
  pauseCurriculumLearning,
  resumeCurriculumLearning,
  startCurriculumLearning,
} from '@/api/curriculumApi'
import { clearAuthStorage } from '@/utils/auth'

const route = useRoute()
const router = useRouter()

const sidebarOpen = ref(false)
const currentPath = computed(() => route.path)
const curriculumSearchKeyword = ref('')
const expandedStepId = ref(null)
const toastMessage = ref('')
const curriculum = ref(null)
const sidebarCurricula = ref([])
const loading = ref(false)
const sidebarLoading = ref(false)
const actionLoading = ref(false)
const errorMessage = ref('')

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
}

const menuItems = [
  { icon: icons.user, label: '마이페이지', path: '/mypage' },
  { icon: icons.chart, label: '학습 대시보드', path: '/learning' },
]

const curriculumStatusLabel = {
  NOT_STARTED: '시작 전',
  IN_PROGRESS: '진행 중',
  PAUSED: '일시정지',
  COMPLETED: '완료',
}

const curriculumStatusClass = {
  NOT_STARTED: 'status-gray',
  IN_PROGRESS: 'status-blue',
  PAUSED: 'status-amber',
  COMPLETED: 'status-emerald',
}

const stepStatusLabel = {
  PENDING: '대기 중',
  IN_PROGRESS: '진행 중',
  COMPLETED: '완료',
}

const stepStatusClass = {
  PENDING: 'status-gray',
  IN_PROGRESS: 'status-blue',
  COMPLETED: 'status-emerald',
}

const difficultyClass = {
  쉬움: 'difficulty-easy',
  보통: 'difficulty-normal',
  어려움: 'difficulty-hard',
}

const resourceTypeClass = {
  강의: 'resource-primary',
  문서: 'resource-blue',
  실습: 'resource-purple',
}

const curriculumId = computed(() => route.params.id)

const curriculumStatus = computed(() => normalizeCurriculumStatus(curriculum.value?.status))

const isCurriculumNotStarted = computed(() =>
  curriculumStatus.value === 'NOT_STARTED',
)

const isCurriculumInProgress = computed(() =>
  curriculumStatus.value === 'IN_PROGRESS',
)

const isCurriculumPaused = computed(() => curriculumStatus.value === 'PAUSED')

const isCurriculumCompleted = computed(() => curriculumStatus.value === 'COMPLETED')

const curriculumDescription = computed(() =>
  curriculum.value?.description ||
  curriculum.value?.recommendation_reason ||
  curriculum.value?.goal ||
  '커리큘럼 설명이 아직 등록되지 않았습니다.',
)

const steps = computed(() => {
  const rawSteps = curriculum.value?.steps || []
  return rawSteps.map(mapStep)
})

const completedCount = computed(() => curriculum.value?.completed_step_count ?? 0)

const totalCount = computed(() => curriculum.value?.total_step_count ?? steps.value.length)

const progressPct = computed(() => curriculum.value?.progress_percent ?? 0)

const currentStep = computed(() => {
  if (curriculum.value?.current_step) {
    return mapStep(curriculum.value.current_step)
  }

  const currentStepId = curriculum.value?.current_step_id
  return steps.value.find((step) => step.id === currentStepId) ||
    steps.value.find((step) => step.status === 'IN_PROGRESS' || step.status === 'ACTIVE') ||
    null
})

const hasValidCurrentStepResourceUrl = computed(() =>
  currentStep.value?.resources?.some((resource) => isValidExternalUrl(resource.url)) ?? false,
)

const filteredInProgress = computed(() =>
  filterCurricula(sidebarCurricula.value.filter((item) => item.status !== 'COMPLETED')),
)

const filteredCompleted = computed(() =>
  filterCurricula(sidebarCurricula.value.filter((item) => item.status === 'COMPLETED')),
)

onMounted(() => {
  loadPageData()
  loadSidebarCurricula()
})

watch(curriculumId, () => {
  loadPageData()
  closeSidebar()
})

async function loadPageData() {
  if (!curriculumId.value) {
    errorMessage.value = '커리큘럼 ID를 찾을 수 없습니다.'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    curriculum.value = await getCurriculumDetail(curriculumId.value)
    expandedStepId.value = currentStep.value?.id || steps.value[0]?.id || null
  } catch (error) {
    errorMessage.value = error.message || '커리큘럼 정보를 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

async function loadSidebarCurricula() {
  sidebarLoading.value = true

  try {
    const response = await getMyCurriculums()
    sidebarCurricula.value = Array.isArray(response)
      ? response.map(mapSidebarCurriculum)
      : []
  } catch {
    sidebarCurricula.value = []
  } finally {
    sidebarLoading.value = false
  }
}

function mapSidebarCurriculum(item) {
  const status = normalizeCurriculumStatus(item.status)
  return {
    id: item.id,
    title: item.title,
    status,
    progress: status === 'COMPLETED' ? 100 : 0,
    updated: formatRelativeDate(item.updated_at || item.created_at),
  }
}

function normalizeCurriculumStatus(status) {
  const value = normalizeStatusValue(status)
  if (value === 'ACTIVE' || value === 'IN_PROGRESS') return 'IN_PROGRESS'
  if (value === 'DRAFT' || value === 'NOT_STARTED') return 'NOT_STARTED'
  if (value === 'PAUSED') return 'PAUSED'
  if (value === 'COMPLETED') return 'COMPLETED'
  return 'NOT_STARTED'
}

function mapStep(step) {
  return {
    id: step.id,
    order: step.order ?? step.step_order,
    title: step.title,
    description: step.description,
    estimatedHours: step.estimated_hours || 0,
    difficulty: step.difficulty || mapDifficulty(step.difficulty_level),
    resources: (step.resources || []).map(mapResource),
    status: normalizeStepStatus(step.status, step.step_progress?.status),
  }
}

function normalizeStepStatus(status, legacyProgressStatus) {
  const value = normalizeStatusValue(status || legacyProgressStatus)
  if (value === 'COMPLETED') return 'COMPLETED'
  if (value === 'IN_PROGRESS' || value === 'ACTIVE' || value === 'PAUSED') return 'IN_PROGRESS'
  return 'PENDING'
}

function normalizeStatusValue(status) {
  return String(status || '')
    .trim()
    .replace(/[\s-]+/g, '_')
    .toUpperCase()
}

function mapDifficulty(value) {
  if (value === 'beginner') return '쉬움'
  if (value === 'advanced') return '어려움'
  return '보통'
}

function mapResource(resource) {
  return {
    id: resource.id,
    label: resource.title || resource.course_name || '학습 자료',
    type: normalizeResourceType(resource.resource_type || resource.type),
    url: resource.url || null,
  }
}

function normalizeResourceType(type) {
  if (!type) return '자료'
  const value = String(type).toLowerCase()
  if (value.includes('video') || value.includes('lecture') || value.includes('course')) return '강의'
  if (value.includes('practice') || value.includes('exercise') || value.includes('kaggle')) return '실습'
  if (value.includes('document') || value.includes('text') || value.includes('docs')) return '문서'
  return type
}

function isValidExternalUrl(url) {
  if (!url || typeof url !== 'string') {
    return false
  }

  try {
    const parsedUrl = new URL(url)
    return parsedUrl.protocol === 'http:' || parsedUrl.protocol === 'https:'
  } catch {
    return false
  }
}

function openFirstCurrentStepResource() {
  const resource = currentStep.value?.resources?.find((item) => isValidExternalUrl(item.url))

  if (!resource) return

  window.open(resource.url, '_blank', 'noopener,noreferrer')
}

function filterCurricula(curricula) {
  const keyword = curriculumSearchKeyword.value.trim().toLowerCase()

  if (!keyword) return curricula

  return curricula.filter((item) =>
    item.title.toLowerCase().includes(keyword),
  )
}

function formatRelativeDate(value) {
  if (!value) return ''

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''

  const diffMs = Date.now() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays <= 0) return '오늘'
  if (diffDays < 7) return `${diffDays}일 전`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}주 전`
  return `${Math.floor(diffDays / 30)}개월 전`
}

function showToast(message) {
  toastMessage.value = message

  window.setTimeout(() => {
    toastMessage.value = ''
  }, 3500)
}

async function runLearningAction(action, successMessage) {
  if (actionLoading.value) return

  actionLoading.value = true
  errorMessage.value = ''

  try {
    const result = await action()

    if (isCurriculumDetailResponse(result)) {
      curriculum.value = result
      expandedStepId.value = currentStep.value?.id || steps.value[0]?.id || null
    } else {
      await loadPageData()
    }
    await loadSidebarCurricula()
    showToast(successMessage)
  } catch (error) {
    const message = getErrorMessage(error)
    errorMessage.value = message
    showToast(message)
  } finally {
    actionLoading.value = false
  }
}

function isCurriculumDetailResponse(data) {
  return Boolean(data && Array.isArray(data.steps))
}

function getErrorMessage(error) {
  return error?.message || '요청 처리에 실패했습니다.'
}

function handleStart() {
  runLearningAction(
    () => startCurriculumLearning(curriculumId.value),
    '학습을 시작했습니다.',
  )
}

function handleContinue() {
  if (currentStep.value) {
    expandedStepId.value = currentStep.value.id
  }
}

function handlePause() {
  runLearningAction(
    () => pauseCurriculumLearning(curriculumId.value),
    '현재 커리큘럼을 일시정지했습니다.',
  )
}

function handleResume() {
  runLearningAction(
    () => resumeCurriculumLearning(curriculumId.value),
    '학습을 재개했습니다.',
  )
}

function handleCompleteStep() {
  if (!isCurriculumInProgress.value) return
  if (!currentStep.value?.id) return

  runLearningAction(
    () => completeCurriculumStep(curriculumId.value, currentStep.value.id),
    '현재 Step을 완료했습니다.',
  )
}

function toggleStep(stepId) {
  expandedStepId.value = expandedStepId.value === stepId ? null : stepId
}

function getStepIcon(status) {
  if (status === 'COMPLETED') return '✓'
  if (status === 'IN_PROGRESS') return '●'
  return '○'
}

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

function closeSidebar() {
  sidebarOpen.value = false
}

function navigateTo(path) {
  router.push(path)
  sidebarOpen.value = false
}

function handleLogout() {
  clearAuthStorage()
  router.push('/')
  sidebarOpen.value = false
}
</script>
