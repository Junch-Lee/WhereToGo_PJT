<template>
  <div class="curriculum-page">
    <div
      v-if="sidebarOpen"
      class="sidebar-overlay"
      @click="closeSidebar"
    ></div>

    <aside :class="['sidebar', { 'sidebar-open': sidebarOpen }]">
      <div class="sidebar-inner">
        <div class="sidebar-logo-section">
          <button class="sidebar-logo-button" @click="navigateTo('/')">
            <div class="logo">
              <div class="logo-icon">WTG</div>
              <div class="logo-text-wrap">
                <span class="logo-title">Where To Go</span>
                <span class="logo-subtitle">AI 학습 컨설턴트</span>
              </div>
            </div>
          </button>
        </div>

        <div class="sidebar-search-section">
          <div class="search-box">
            <span class="search-icon">⌕</span>
            <input
              v-model="curriculumSearchKeyword"
              type="text"
              class="search-input"
              placeholder="내 커리큘럼 검색"
            />
          </div>
        </div>

        <div class="sidebar-menu-section">
          <nav class="sidebar-nav">
            <button
              v-for="item in menuItems"
              :key="item.path"
              :class="['sidebar-menu-item', { active: currentPath === item.path }]"
              @click="navigateTo(item.path)"
            >
              <span class="menu-icon">{{ item.icon }}</span>
              <span>{{ item.label }}</span>
            </button>
          </nav>
        </div>

        <div class="sidebar-curricula">
          <div v-if="sidebarLoading" class="sidebar-empty">
            <p>커리큘럼을 불러오는 중입니다.</p>
          </div>

          <div v-if="filteredInProgress.length > 0" class="curriculum-list-group">
            <h3 class="sidebar-section-title">진행 중인 커리큘럼</h3>

            <button
              v-for="item in filteredInProgress"
              :key="item.id"
              class="sidebar-curriculum-item"
              @click="navigateTo(`/curriculum/${item.id}`)"
            >
              <div class="sidebar-curriculum-content">
                <p class="sidebar-curriculum-title">{{ item.title }}</p>

                <div class="sidebar-progress-row">
                  <div class="sidebar-progress-track">
                    <div
                      class="sidebar-progress-fill"
                      :style="{ width: `${item.progress}%` }"
                    ></div>
                  </div>

                  <span class="sidebar-updated">{{ item.updated }}</span>
                </div>
              </div>

              <span class="sidebar-chevron">›</span>
            </button>
          </div>

          <div v-if="filteredCompleted.length > 0" class="curriculum-list-group">
            <h3 class="sidebar-section-title">완료한 커리큘럼</h3>

            <button
              v-for="item in filteredCompleted"
              :key="item.id"
              class="sidebar-curriculum-item"
              @click="navigateTo(`/curriculum/${item.id}`)"
            >
              <div class="sidebar-curriculum-content">
                <p class="sidebar-curriculum-title completed">{{ item.title }}</p>
                <span class="sidebar-updated">{{ item.updated }}</span>
              </div>

              <span class="sidebar-chevron">›</span>
            </button>
          </div>

          <div
            v-if="
              !sidebarLoading &&
              curriculumSearchKeyword.trim() &&
              filteredInProgress.length === 0 &&
              filteredCompleted.length === 0
            "
            class="sidebar-empty"
          >
            <p>검색 결과가 없습니다</p>
          </div>
        </div>

        <div class="sidebar-bottom">
          <button class="sidebar-bottom-item" @click="toggleTheme">
            <span class="menu-icon">{{ isDark ? '☀' : '☾' }}</span>
            <span>{{ isDark ? '라이트 모드' : '다크 모드' }}</span>
          </button>

          <button class="sidebar-bottom-item">
            <span class="menu-icon">⚙</span>
            <span>설정</span>
          </button>

          <button class="sidebar-bottom-item">
            <span class="menu-icon">↩</span>
            <span>로그아웃</span>
          </button>
        </div>
      </div>
    </aside>

    <div class="main-layout">
      <header class="page-header">
        <button
          class="logo-menu-button"
          aria-label="사이드바 열기"
          @click="toggleSidebar"
        >
          <span class="logo-menu-icon">☰</span>
        </button>

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
                v-if="curriculumStatus === 'NOT_STARTED'"
                class="primary-button"
                :disabled="actionLoading"
                @click="handleStart"
              >
                <span>▶</span>
                학습 시작하기
              </button>

              <div v-else-if="curriculumStatus === 'IN_PROGRESS'" class="button-row">
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
                v-else-if="curriculumStatus === 'PAUSED'"
                class="primary-button"
                :disabled="actionLoading"
                @click="handleResume"
              >
                <span>▶</span>
                학습 재개하기
              </button>

              <p v-else class="complete-text">학습 완료</p>
            </section>

            <div v-if="toastMessage" class="toast">
              {{ toastMessage }}
            </div>

            <section
              v-if="curriculumStatus === 'IN_PROGRESS' && currentStep"
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
                      v-if="resource.url"
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
                  class="primary-button"
                  :disabled="actionLoading"
                  @click="handleCompleteStep"
                >
                  Step 완료하기
                </button>
              </div>
            </section>

            <section v-if="curriculumStatus === 'PAUSED'" class="paused-banner">
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

            <section v-if="curriculumStatus === 'COMPLETED'" class="completion-banner">
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
                            v-if="resource.url"
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

import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  completeCurrentStep,
  getCurriculumDetail,
  getMyCurriculums,
  pauseCurriculumLearning,
  resumeCurriculumLearning,
  startCurriculumLearning,
} from '@/api/curriculumApi'

const route = useRoute()
const router = useRouter()

const sidebarOpen = ref(false)
const isDark = ref(false)
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

const menuItems = [
  { icon: '◇', label: '마이페이지', path: '/mypage' },
  { icon: '▦', label: '학습 대시보드', path: '/learning' },
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

const curriculumStatus = computed(() => mapCurriculumStatus(curriculum.value?.status))

const curriculumDescription = computed(() =>
  curriculum.value?.recommendation_reason ||
  curriculum.value?.goal ||
  '커리큘럼 설명이 아직 등록되지 않았습니다.',
)

const steps = computed(() => {
  const rawSteps = curriculum.value?.steps || []
  return rawSteps.map(mapStep)
})

const completedCount = computed(() =>
  steps.value.filter((step) => step.status === 'COMPLETED').length,
)

const totalCount = computed(() => steps.value.length)

const progressPct = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round((completedCount.value / totalCount.value) * 100)
})

const currentStep = computed(() => {
  const currentStepId = curriculum.value?.current_step_id
  return steps.value.find((step) => step.id === currentStepId) ||
    steps.value.find((step) => step.status === 'IN_PROGRESS') ||
    null
})

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
  const status = mapCurriculumStatus(item.status)
  return {
    id: item.id,
    title: item.title,
    status,
    progress: status === 'COMPLETED' ? 100 : 0,
    updated: formatRelativeDate(item.updated_at || item.created_at),
  }
}

function mapCurriculumStatus(status) {
  if (status === 'ACTIVE') return 'IN_PROGRESS'
  if (status === 'DRAFT') return 'NOT_STARTED'
  if (status === 'PAUSED') return 'PAUSED'
  if (status === 'COMPLETED') return 'COMPLETED'
  return 'NOT_STARTED'
}

function mapStep(step) {
  const progress = step.step_progress
  const status = mapStepStatus(progress?.status, step.id)

  return {
    id: step.id,
    order: step.step_order,
    title: step.title,
    description: step.description,
    estimatedHours: step.estimated_hours || 0,
    difficulty: mapDifficulty(step.difficulty_level),
    resources: (step.resources || []).map(mapResource),
    status,
  }
}

function mapStepStatus(progressStatus, stepId) {
  if (progressStatus === 'COMPLETED') return 'COMPLETED'
  if (
    progressStatus === 'IN_PROGRESS' ||
    progressStatus === 'PAUSED' ||
    curriculum.value?.current_step_id === stepId
  ) {
    return 'IN_PROGRESS'
  }
  return 'PENDING'
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

  try {
    const result = await action()

    if (result?.next_step_exists && successMessage === '현재 Step을 완료했습니다.') {
      await startCurriculumLearning(curriculumId.value)
    }

    await loadPageData()
    await loadSidebarCurricula()
    showToast(successMessage)
  } catch (error) {
    showToast(error.message || '요청 처리에 실패했습니다.')
  } finally {
    actionLoading.value = false
  }
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
  if (curriculumStatus.value !== 'IN_PROGRESS') return
  if (!currentStep.value) return

  runLearningAction(
    () => completeCurrentStep(curriculumId.value),
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

function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
}
</script>
