<template>
  <div class="curriculum-result-page">
    <UserSidebar :open="sidebarOpen" @close="closeSidebar" />

    <div class="result-main-layout">
      <header class="result-header">
        <div class="result-header-left">
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

      <main class="result-content">
        <div class="result-content-inner">
          <div class="go-keyword" aria-hidden="true">
            GO
          </div>

          <h1>당신만의 학습 경로가 완성되었습니다</h1>

          <p class="result-description">
            지금의 목표와 학습 조건을 바탕으로 바로 시작할 수 있는 커리큘럼을 준비했어요.
          </p>

          <section class="summary-strip">
            <div
              v-for="item in summaryItems"
              :key="item.label"
              class="summary-item"
            >
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </section>

          <section class="ai-note">
            <span class="ai-note-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9"></circle>
                <path d="M12 7v6"></path>
                <circle cx="12" cy="17" r="0.8"></circle>
              </svg>
            </span>

            <p>{{ cautionNotice }}</p>
          </section>

          <section class="learning-path-section">
            <h2>학습 경로</h2>

            <div class="learning-path-list">
              <article
                v-for="(week, index) in weeklyPlan"
                :key="week.week"
                class="learning-path-item"
              >
                <div class="path-indicator">
                  <span class="path-number">
                    {{ formatStepNumber(week.week) }}
                  </span>

                  <span
                    v-if="index < weeklyPlan.length - 1"
                    class="path-connector"
                  ></span>
                </div>

                <div class="path-step-content">
                  <button
                    type="button"
                    class="path-step-header"
                    :aria-expanded="expandedStep === week.week"
                    @click="toggleStep(week.week)"
                  >
                    <span class="path-step-main">
                      <span class="path-title-row">
                        <strong>{{ week.title }}</strong>

                        <span
                          :class="[
                            'difficulty-badge',
                            getDifficultyClass(week.difficulty),
                          ]"
                        >
                          {{ week.difficulty }}
                        </span>
                      </span>

                      <span class="path-time">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                          <circle cx="12" cy="12" r="8.5"></circle>
                          <path d="M12 7.5V12l3 2"></path>
                        </svg>

                        {{ week.time }}
                      </span>
                    </span>

                    <span class="expand-icon" aria-hidden="true">
                      <svg
                        v-if="expandedStep === week.week"
                        viewBox="0 0 24 24"
                      >
                        <path d="m6 15 6-6 6 6"></path>
                      </svg>

                      <svg v-else viewBox="0 0 24 24">
                        <path d="m6 9 6 6 6-6"></path>
                      </svg>
                    </span>
                  </button>

                  <Transition name="step-expand">
                    <div
                      v-if="expandedStep === week.week"
                      class="path-step-detail"
                    >
                      <ul>
                        <li
                          v-for="topic in week.topics"
                          :key="topic"
                        >
                          <span class="topic-dot"></span>
                          <span>{{ topic }}</span>
                        </li>
                      </ul>

                      <p>
                        결과물:
                        <strong>{{ week.output }}</strong>
                      </p>
                    </div>
                  </Transition>
                </div>
              </article>
            </div>
          </section>

          <section
            v-if="resources.length"
            class="learning-path-section resource-path-section"
          >
            <h2>추천 학습 자료</h2>

            <div class="resource-list">
              <article
                v-for="resource in resources"
                :key="resource.key || resource.name"
                class="resource-card"
              >
                <div>
                  <span class="resource-type">{{ resource.type }}</span>
                  <strong>{{ resource.name }}</strong>
                </div>

                <p>{{ resource.reason }}</p>
              </article>
            </div>
          </section>

          <section class="result-actions">
            <button
              type="button"
              class="result-primary-button"
              :disabled="isSaving"
              @click="handleSaveAndStart"
            >
              <span>
                {{ isSaving ? '저장 중...' : '저장하고 학습 시작하기' }}
              </span>

              <svg
                v-if="!isSaving"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path d="M5 12h14"></path>
                <path d="m14 7 5 5-5 5"></path>
              </svg>

              <span
                v-else
                class="button-spinner"
                aria-hidden="true"
              ></span>
            </button>

            <p
              v-if="saveMessage"
              class="result-save-message"
            >
              {{ saveMessage }}
            </p>

            <div class="result-secondary-actions">
              <button
                type="button"
                @click="handleRegenerate"
              >
                커리큘럼 다시 생성
              </button>

              <button
                type="button"
                @click="handleEditAnswers"
              >
                인터뷰 내용 수정
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
import UserSidebar from '@/components/user/UserSidebar.vue';
import BrandMenuButton from '@/components/user/BrandMenuButton.vue';
import { useRoute, useRouter } from 'vue-router';
import { getMyCurriculums, saveGeneratedCurriculum } from '@/api/curriculumApi';
import { clearAuthStorage, isAuthenticated } from '@/utils/auth';
import '@/assets/styles/user-shell.css';
import './CurriculumResult.css';

const router = useRouter();
const route = useRoute();

const sidebarOpen = ref(false);
const logoHovered = ref(false);
const curriculumSearchKeyword = ref('');
const curriculums = ref([]);
const isLoadingCurricula = ref(false);
const curriculumLoadError = ref('');
const generatedCurriculum = ref(null);
const expandedStep = ref(1);
const isSaving = ref(false);
const saveMessage = ref('');

const journeyStages = ['WHERE', 'TO', 'GO'];
const currentJourneyStage = 'GO';

const menuItems = [
  { icon: 'user', label: '마이페이지', path: '/mypage' },
  { icon: 'chart', label: '학습 대시보드', path: '/learning' },
];

const fallbackWeeklyPlan = [
  {
    week: 1,
    title: 'Python 기초와 데이터 구조',
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
];

const fallbackResources = [
  {
    key: 'fallback-resource-1',
    type: '실습 자료',
    name: '데이터 분석 입문 실습',
    reason: '초기 단계에서 데이터 조작 흐름을 빠르게 익히기 좋습니다.',
  },
  {
    key: 'fallback-resource-2',
    type: '프로젝트',
    name: '미니 포트폴리오 프로젝트',
    reason: '학습 내용을 결과물로 연결하는 연습에 적합합니다.',
  },
];

const difficultyLabels = {
  beginner: '입문',
  intermediate: '보통',
  advanced: '심화',
};

const statusLabels = {
  DRAFT: '초안',
  ACTIVE: '진행 중',
  COMPLETED: '완료',
  ARCHIVED: '보관됨',
};

const currentPath = computed(() => route.path);
const currentJourneyIndex = computed(() =>
  journeyStages.indexOf(currentJourneyStage),
);
const userProfile = computed(() => generatedCurriculum.value?.user_profile || {});
const generatedSteps = computed(() => generatedCurriculum.value?.steps || []);

const summaryItems = computed(() => {
  const profile = userProfile.value;

  return [
    {
      label: '학습 기간',
      value: `${profile.target_weeks || weeklyPlan.value.length || '-'}주`,
    },
    {
      label: '학습 단계',
      value: `${weeklyPlan.value.length || '-'} Steps`,
    },
    {
      label: '주간 학습',
      value: `주 ${profile.weekly_available_hours || profile.weekly_hours || '-'}시간`,
    },
    {
      label: '목표',
      value: profile.goal || generatedCurriculum.value?.title || '맞춤 커리큘럼',
    },
  ];
});

const recommendationReason = computed(
  () =>
    generatedCurriculum.value?.recommendation_reason ||
    '입력한 목표와 학습 조건을 바탕으로 단계별 학습 경로를 구성했습니다.',
);

const weeklyPlan = computed(() => {
  if (!generatedCurriculum.value || !generatedSteps.value.length) {
    return fallbackWeeklyPlan;
  }

  return generatedSteps.value.map((step, index) => {
    const topics = [
      step.target_topic_slug ? `핵심 주제: ${step.target_topic_slug}` : '',
      step.prerequisite_note ? `선수 지식: ${step.prerequisite_note}` : '',
    ].filter(Boolean);

    return {
      week: step.order || index + 1,
      title: step.title || `학습 단계 ${index + 1}`,
      topics: topics.length ? topics : ['AI가 추천한 단계별 학습 내용'],
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
      const providerName = resource.provider_name
        ? ` · ${resource.provider_name}`
        : '';

      items.push({
        key: `resource-preview-${stepIndex}-${resourceIndex}`,
        type: '학습 자료',
        name: resource.title,
        reason: `${stepIndex + 1}단계 학습 목표와 연결된 추천 자료입니다${providerName}.`,
      });
    });

    (step.preview_courses || []).forEach((course, courseIndex) => {
      const universityName = course.university_name
        ? ` · ${course.university_name}`
        : '';

      items.push({
        key: `course-preview-${stepIndex}-${courseIndex}`,
        type: '강의',
        name: course.course_name,
        reason: `${stepIndex + 1}단계 학습 목표와 연결된 추천 강의입니다${universityName}.`,
      });
    });
  });

  return items;
});

const cautionNotice = computed(() => {
  if (!generatedCurriculum.value) {
    return '학습 중 어렵거나 맞지 않는 단계가 있다면 커리큘럼을 다시 조정할 수 있습니다.';
  }

  const prerequisiteNotes = generatedSteps.value
    .map((step) => step.prerequisite_note)
    .filter(Boolean);

  if (prerequisiteNotes.length) {
    return prerequisiteNotes.join(' ');
  }

  return recommendationReason.value;
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

function formatStepNumber(number) {
  return String(number).padStart(2, '0');
}

function getDifficultyClass(difficulty) {
  if (difficulty === '쉬움' || difficulty === '입문' || difficulty === 'beginner') {
    return 'easy';
  }

  if (difficulty === '심화' || difficulty === 'advanced') {
    return 'hard';
  }

  return 'normal';
}

function toggleStep(week) {
  expandedStep.value = expandedStep.value === week ? null : week;
}

function toggleSidebar() {
  if (!sidebarOpen.value) {
    loadCurriculums();
  }

  sidebarOpen.value = !sidebarOpen.value;
}

function closeSidebar() {
  sidebarOpen.value = false;
}

function handleNavigate(path) {
  router.push(path);
  closeSidebar();
}

async function handleSaveAndStart() {
  if (isSaving.value) return;

  if (!generatedCurriculum.value) {
    saveMessage.value =
      '저장할 AI 커리큘럼 생성 결과가 없습니다. 다시 생성해 주세요.';
    return;
  }

  isSaving.value = true;
  saveMessage.value = '';

  try {
    const response = await saveGeneratedCurriculum(generatedCurriculum.value);
    const curriculumId = response.curriculum_id || response.curriculum?.id;

    if (!curriculumId) {
      saveMessage.value =
        '커리큘럼은 저장됐지만 상세 페이지 정보를 찾지 못했습니다.';
      return;
    }

    sessionStorage.setItem('generated_curriculum_id', String(curriculumId));
    sessionStorage.setItem('saved_curriculum_response', JSON.stringify(response));
    router.push(`/curriculum/${curriculumId}`);
  } catch (error) {
    saveMessage.value =
      error?.message ||
      '커리큘럼 저장 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.';
  } finally {
    isSaving.value = false;
  }
}

function handleRegenerate() {
  router.push('/interview/summary');
}

function handleEditAnswers() {
  router.push('/interview/summary');
}

function loadGeneratedCurriculum() {
  const savedResponse = sessionStorage.getItem('generated_curriculum_response');

  if (!savedResponse) {
    router.replace('/interview/summary');
    return;
  }

  try {
    const parsed = JSON.parse(savedResponse);
    generatedCurriculum.value =
      parsed.generated_curriculum || parsed.curriculum || null;
  } catch (error) {
    generatedCurriculum.value = null;
  }

  if (!generatedCurriculum.value) {
    sessionStorage.removeItem('generated_curriculum_response');
    router.replace('/interview/summary');
  }
}

function handleEscKey(event) {
  if (event.key === 'Escape' && sidebarOpen.value) {
    closeSidebar();
  }
}

function handleLogout() {
  clearAuthStorage();
  closeSidebar();
  router.push('/');
}

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
