<template>
  <div class="mypage-page">
    <UserSidebar :open="sidebarOpen" @close="closeSidebar" />

    <div class="mypage-main">
      <header class="mypage-header">
        <BrandMenuButton @click="toggleSidebar" />

        <h1>마이페이지</h1>
      </header>

      <main class="mypage-content">
        <div class="mypage-container">
          <p v-if="pageError" class="page-error">
            {{ pageError }}
          </p>

          <section class="mypage-card basic-info-card">
            <div class="card-header basic-info-header">
              <h2>기본 정보</h2>

              <button
                type="button"
                class="outline-button basic-info-edit-button"
                @click="openAccountModal"
              >
                <span v-html="icons.edit"></span>
                수정
              </button>
            </div>

            <div class="basic-info-grid">
              <div class="basic-info-item basic-info-email">
                <p>이메일</p>
                <strong>{{ accountInfo.email || '-' }}</strong>
              </div>

              <div class="basic-info-item">
                <p>닉네임</p>
                <strong>{{ accountInfo.nickname || '-' }}</strong>
              </div>

              <div class="basic-info-item">
                <p>가입일</p>
                <strong>{{ formatDate(accountInfo.created_at) }}</strong>
              </div>
            </div>

            <div class="account-security-section">
              <h3>계정 보안</h3>

              <div class="account-security-row">
                <div class="account-security-copy">
                  <p>비밀번호</p>
                  <span>계정 보안을 위해 주기적으로 변경해주세요.</span>
                </div>

                <button
                  type="button"
                  class="password-change-button"
                  @click="openPasswordModal"
                >
                  <span>변경하기</span>
                  <span class="password-change-arrow" aria-hidden="true">→</span>
                </button>
              </div>
            </div>
          </section>

          <section class="mypage-card">
            <div class="card-header">
              <h2>학습 프로필</h2>

              <button
                type="button"
                class="outline-button"
                @click="openProfileModal"
              >
                <span v-html="icons.edit"></span>
                수정
              </button>
            </div>

            <div class="info-grid">
              <div class="info-item">
                <p>관심 학습 분야</p>
                <strong>{{ selectedTopicNames || '선택한 관심 분야가 없습니다.' }}</strong>
              </div>

              <div class="info-item">
                <p>주간 학습 가능 시간</p>
                <strong>주 {{ profileInfo.available_weekly_hours || 0 }}시간</strong>
              </div>

              <div class="info-item">
                <p>선호 학습 방식</p>
                <strong>{{ preferredLearningStyleLabel }}</strong>
              </div>
            </div>
          </section>

          <section class="mypage-card">
            <h2 class="section-title">생성한 커리큘럼</h2>

            <p v-if="isLoadingCurricula" class="empty-topic-text">
              커리큘럼을 불러오는 중입니다...
            </p>

            <p v-else-if="curriculumLoadError" class="modal-error">
              커리큘럼 목록을 불러오지 못했습니다. 잠시 후 다시 시도해주세요.
            </p>

            <p v-else-if="curricula.length === 0" class="empty-topic-text">
              아직 생성한 커리큘럼이 없습니다.
            </p>

            <div v-else class="curriculum-list">
              <div
                v-for="curriculum in curricula"
                :key="curriculum.id"
                class="curriculum-row"
                @click="navigateTo(`/curriculum/${curriculum.id}`)"
              >
                <div class="curriculum-main">
                  <p>{{ curriculum.title }}</p>

                  <div class="curriculum-meta">
                    <span>{{ curriculum.goal }}</span>
                    <span>{{ getStatusLabel(curriculum.status) }}</span>
                    <span>{{ curriculum.target_weeks }}주</span>
                    <span>주 {{ curriculum.weekly_available_hours }}시간</span>
                    <span>{{ getLearningStyleLabel(curriculum.preferred_learning_style) }}</span>
                    <span>생성 {{ formatDate(curriculum.created_at) }}</span>
                    <span>수정 {{ formatDate(curriculum.updated_at) }}</span>
                  </div>
                </div>

                <button type="button" class="outline-button small">
                  보기
                </button>
              </div>
            </div>
          </section>

          <section class="mypage-card">
            <h2 class="section-title">학습 통계</h2>

            <div class="stats-grid">
              <div class="stat-card">
                <strong>{{ curricula.length }}</strong>
                <span>생성한 커리큘럼</span>
              </div>

              <div class="stat-card">
                <strong>{{ completedCurriculumCount }}</strong>
                <span>완료한 커리큘럼</span>
              </div>

              <div class="stat-card">
                <strong>45</strong>
                <span>학습 일수</span>
              </div>

              <div class="stat-card">
                <strong>120</strong>
                <span>총 학습 시간</span>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>

    <div
      v-if="isAccountModalOpen"
      class="modal-overlay"
      @click.self="closeAccountModal"
    >
      <section class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="account-modal-title">
        <div class="modal-header">
          <div>
            <h2 id="account-modal-title">기본 정보 수정</h2>
            <p>닉네임만 변경할 수 있습니다.</p>
          </div>

          <button type="button" class="modal-close-button" aria-label="닫기" @click="closeAccountModal">
            <svg viewBox="0 0 24 24" class="button-icon">
              <path d="M18 6 6 18M6 6l12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
            </svg>
          </button>
        </div>

        <label class="form-field">
          <span>닉네임</span>
          <input
            v-model="accountDraft.nickname"
            type="text"
            maxlength="30"
            placeholder="닉네임을 입력하세요"
          />
        </label>

        <p v-if="accountModalError" class="modal-error">{{ accountModalError }}</p>

        <div class="modal-actions">
          <button type="button" class="outline-button" @click="closeAccountModal">
            취소
          </button>
          <button
            type="button"
            class="primary-button"
            :disabled="isSavingAccount"
            @click="saveAccountInfo"
          >
            {{ isSavingAccount ? '저장 중...' : '저장' }}
          </button>
        </div>
      </section>
    </div>

    <div
      v-if="isPasswordModalOpen"
      class="modal-overlay"
      @click.self="closePasswordModal"
    >
      <section class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="password-modal-title">
        <div class="modal-header">
          <div>
            <h2 id="password-modal-title">비밀번호 변경</h2>
            <p>현재 비밀번호 확인 후 새 비밀번호로 변경합니다.</p>
          </div>

          <button type="button" class="modal-close-button" aria-label="닫기" @click="closePasswordModal">
            <svg viewBox="0 0 24 24" class="button-icon">
              <path d="M18 6 6 18M6 6l12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
            </svg>
          </button>
        </div>

        <div class="form-stack">
          <label class="form-field">
            <span>현재 비밀번호</span>
            <input
              v-model="passwordForm.current_password"
              type="password"
              autocomplete="current-password"
              placeholder="현재 비밀번호"
            />
          </label>

          <label class="form-field">
            <span>새 비밀번호</span>
            <input
              v-model="passwordForm.new_password"
              type="password"
              autocomplete="new-password"
              placeholder="새 비밀번호"
            />
          </label>

          <label class="form-field">
            <span>새 비밀번호 확인</span>
            <input
              v-model="passwordForm.new_password_confirm"
              type="password"
              autocomplete="new-password"
              placeholder="새 비밀번호 확인"
            />
          </label>
        </div>

        <p v-if="passwordModalError" class="modal-error">{{ passwordModalError }}</p>
        <p v-if="passwordModalMessage" class="modal-success">{{ passwordModalMessage }}</p>

        <div class="modal-actions">
          <button type="button" class="outline-button" @click="closePasswordModal">
            취소
          </button>
          <button
            type="button"
            class="primary-button"
            :disabled="isChangingPassword"
            @click="changeUserPassword"
          >
            {{ isChangingPassword ? '변경 중...' : '비밀번호 변경' }}
          </button>
        </div>
      </section>
    </div>

    <div
      v-if="isProfileModalOpen"
      class="modal-overlay"
      @click.self="closeProfileModal"
    >
      <section class="modal-panel large" role="dialog" aria-modal="true" aria-labelledby="profile-modal-title">
        <div class="modal-header">
          <div>
            <h2 id="profile-modal-title">학습 프로필 수정</h2>
            <p>학습 가능 시간과 관심 분야를 조정합니다.</p>
          </div>

          <button type="button" class="modal-close-button" aria-label="닫기" @click="closeProfileModal">
            <svg viewBox="0 0 24 24" class="button-icon">
              <path d="M18 6 6 18M6 6l12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
            </svg>
          </button>
        </div>

        <label class="form-field">
          <span>주간 학습 가능 시간</span>
          <input
            v-model.number="profileDraft.available_weekly_hours"
            type="number"
            min="0"
            max="168"
            placeholder="예: 10"
          />
        </label>

        <label class="form-field">
          <span>선호 학습 방식</span>
          <select v-model="profileDraft.preferred_learning_style">
            <option value="">선택하지 않음</option>
            <option
              v-for="style in learningStyleOptions"
              :key="style.value"
              :value="style.value"
            >
              {{ style.label }}
            </option>
          </select>
        </label>

        <div class="topic-picker">
          <div class="selected-topic-area">
            <p class="field-label">선택한 관심 분야</p>

            <div v-if="draftSelectedTopics.length" class="selected-topic-list">
              <button
                v-for="topic in draftSelectedTopics"
                :key="topic.id"
                type="button"
                class="selected-topic-chip"
                @click="removeTopic(topic.id)"
              >
                {{ topic.name }}
                <span aria-hidden="true">x</span>
              </button>
            </div>

            <p v-else class="empty-topic-text">
              선택한 관심 분야가 없습니다.
            </p>
          </div>

          <label class="form-field">
            <span>관심 분야 검색</span>
            <input
              v-model="topicSearchKeyword"
              type="text"
              placeholder="검색어를 입력하세요"
            />
          </label>

          <div v-if="topicSearchKeyword.trim()" class="topic-search-results">
            <button
              v-for="topic in filteredTopics"
              :key="topic.id"
              type="button"
              class="topic-result-button"
              :disabled="profileDraft.topic_ids.includes(topic.id)"
              @click="addTopic(topic.id)"
            >
              <span>{{ topic.name }}</span>
              <small>{{ profileDraft.topic_ids.includes(topic.id) ? '선택됨' : '추가' }}</small>
            </button>

            <p v-if="filteredTopics.length === 0" class="empty-topic-text">
              검색 결과가 없습니다.
            </p>
          </div>
        </div>

        <p v-if="profileModalError" class="modal-error">{{ profileModalError }}</p>

        <div class="modal-actions">
          <button type="button" class="outline-button" @click="closeProfileModal">
            취소
          </button>
          <button
            type="button"
            class="primary-button"
            :disabled="isSavingProfile"
            @click="saveProfileInfo"
          >
            {{ isSavingProfile ? '저장 중...' : '저장' }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import UserSidebar from '@/components/user/UserSidebar.vue';
import BrandMenuButton from '@/components/user/BrandMenuButton.vue';
import { useRoute, useRouter } from 'vue-router';
import { getMyCurriculums } from '@/api/curriculumApi';
import { clearAuthStorage } from '@/utils/auth';
import {
  changePassword,
  getMyInfo,
  getMyProfile,
  getTopics,
  updateMyInfo,
  updateMyProfile,
} from '@/api/myPageApi';
import './MyPage.css';
import '@/assets/styles/user-shell.css';

const router = useRouter();
const route = useRoute();

const sidebarOpen = ref(false);
const pageError = ref('');

const isAccountModalOpen = ref(false);
const isPasswordModalOpen = ref(false);
const isProfileModalOpen = ref(false);

const isSavingAccount = ref(false);
const isSavingProfile = ref(false);
const isChangingPassword = ref(false);

const accountModalError = ref('');
const passwordModalError = ref('');
const passwordModalMessage = ref('');
const profileModalError = ref('');
const topicSearchKeyword = ref('');
const curriculumSearchKeyword = ref('');
const curricula = ref([]);
const isLoadingCurricula = ref(false);
const curriculumLoadError = ref('');

const accountInfo = reactive({
  email: '',
  nickname: '',
  created_at: '',
});

const accountDraft = reactive({
  nickname: '',
});

const profileInfo = reactive({
  available_weekly_hours: 0,
  preferred_learning_style: '',
  topic_ids: [],
});

const profileDraft = reactive({
  available_weekly_hours: 0,
  preferred_learning_style: '',
  topic_ids: [],
});

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  new_password_confirm: '',
});

const topics = ref([]);

const learningStyleOptions = [
  { value: 'theory', label: '이론 중심' },
  { value: 'practice', label: '실습 중심' },
  { value: 'project', label: '프로젝트 중심' },
  { value: 'video', label: '영상 강의 중심' },
  { value: 'text', label: '문서/책 중심' },
  { value: 'balanced', label: '균형형' },
];

const statusLabels = {
  DRAFT: '초안',
  ACTIVE: '진행 중',
  COMPLETED: '완료',
  ARCHIVED: '보관됨',
};

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
  edit: `
    <svg viewBox="0 0 24 24" class="button-icon">
      <path d="M12 20h9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
    </svg>
  `,
};

const menuItems = [
  { icon: icons.user, label: '마이페이지', path: '/mypage' },
  { icon: icons.chart, label: '학습 대시보드', path: '/learning' },
];

const selectedTopicNames = computed(() => {
  const selected = topics.value.filter((topic) =>
    profileInfo.topic_ids.includes(topic.id),
  );

  return selected.map((topic) => topic.name).join(', ');
});

const completedCurriculumCount = computed(() => {
  return curricula.value.filter((curriculum) => curriculum.status === 'COMPLETED').length;
});

const filterSidebarCurricula = (items) => {
  const keyword = curriculumSearchKeyword.value.trim().toLowerCase();

  if (!keyword) return items;

  return items.filter((curriculum) =>
    curriculum.title.toLowerCase().includes(keyword),
  );
};

const mapCurriculumForSidebar = (curriculum) => ({
  id: curriculum.id,
  title: curriculum.title,
  status: curriculum.status,
  statusLabel: getStatusLabel(curriculum.status),
  progress: curriculum.status === 'COMPLETED' ? 100 : 0,
  updated: formatDate(curriculum.updated_at || curriculum.created_at),
});

const inProgressCurricula = computed(() =>
  curricula.value
    .filter((curriculum) => curriculum.status !== 'COMPLETED')
    .map(mapCurriculumForSidebar),
);

const completedCurricula = computed(() =>
  curricula.value
    .filter((curriculum) => curriculum.status === 'COMPLETED')
    .map(mapCurriculumForSidebar),
);

const filteredInProgressCurricula = computed(() =>
  filterSidebarCurricula(inProgressCurricula.value),
);

const filteredCompletedCurricula = computed(() =>
  filterSidebarCurricula(completedCurricula.value),
);

const hasNoCurriculums = computed(() => curricula.value.length === 0);
const hasNoFilteredCurriculums = computed(
  () =>
    Boolean(curriculumSearchKeyword.value.trim()) &&
    filteredInProgressCurricula.value.length === 0 &&
    filteredCompletedCurricula.value.length === 0,
);

const preferredLearningStyleLabel = computed(() => {
  const selected = learningStyleOptions.find(
    (style) => style.value === profileInfo.preferred_learning_style,
  );

  return selected?.label || '선택한 선호 학습 방식이 없습니다.';
});

const draftSelectedTopics = computed(() => {
  return topics.value.filter((topic) => profileDraft.topic_ids.includes(topic.id));
});

const filteredTopics = computed(() => {
  const keyword = topicSearchKeyword.value.trim().toLowerCase();

  if (!keyword) return [];

  return topics.value.filter((topic) =>
    topic.name.toLowerCase().includes(keyword),
  );
});

const loadCurriculums = async () => {
  curriculumLoadError.value = '';
  isLoadingCurricula.value = true;

  try {
    const curriculumList = await getMyCurriculums();
    curricula.value = Array.isArray(curriculumList) ? curriculumList : [];
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

const navigateTo = (path) => {
  router.push(path);
  closeSidebar();
};

const handleLogout = () => {
  clearAuthStorage();
  router.push('/login');
};

const closeAnyModal = () => {
  if (isAccountModalOpen.value) closeAccountModal();
  if (isPasswordModalOpen.value) closePasswordModal();
  if (isProfileModalOpen.value) closeProfileModal();
};

const handleEscKey = (event) => {
  if (event.key !== 'Escape') return;

  if (sidebarOpen.value) {
    closeSidebar();
    return;
  }

  closeAnyModal();
};

const formatDate = (dateString) => {
  if (!dateString) return '-';

  return new Date(dateString).toLocaleDateString('ko-KR');
};

const setAccountInfo = (data) => {
  accountInfo.email = data.email || '';
  accountInfo.nickname = data.nickname || '';
  accountInfo.created_at = data.created_at || '';
};

const setProfileInfo = (data) => {
  profileInfo.available_weekly_hours = data.available_weekly_hours || 0;
  profileInfo.preferred_learning_style = data.preferred_learning_style || '';
  profileInfo.topic_ids = (data.interest_topics || []).map((topic) => topic.id);
};

const getStatusLabel = (status) => {
  return statusLabels[status] || status || '-';
};

const getLearningStyleLabel = (value) => {
  const selected = learningStyleOptions.find((style) => style.value === value);
  return selected?.label || '-';
};

const loadMyPage = async () => {
  pageError.value = '';
  curriculumLoadError.value = '';
  isLoadingCurricula.value = true;

  try {
    const [myInfo, myProfile, topicList, curriculumList] = await Promise.all([
      getMyInfo(),
      getMyProfile(),
      getTopics(),
      getMyCurriculums(),
    ]);

    setAccountInfo(myInfo);
    setProfileInfo(myProfile);
    topics.value = topicList;
    curricula.value = Array.isArray(curriculumList) ? curriculumList : [];
  } catch (error) {
    pageError.value =
      error?.message || '마이페이지 정보를 불러오지 못했습니다.';
    curriculumLoadError.value =
      error?.message || '커리큘럼 목록을 불러오지 못했습니다.';
  } finally {
    isLoadingCurricula.value = false;
  }
};

const openAccountModal = () => {
  accountDraft.nickname = accountInfo.nickname;
  accountModalError.value = '';
  isAccountModalOpen.value = true;
};

function closeAccountModal() {
  isAccountModalOpen.value = false;
  accountModalError.value = '';
  accountDraft.nickname = accountInfo.nickname;
}

const openPasswordModal = () => {
  passwordForm.current_password = '';
  passwordForm.new_password = '';
  passwordForm.new_password_confirm = '';
  passwordModalError.value = '';
  passwordModalMessage.value = '';
  isPasswordModalOpen.value = true;
};

function closePasswordModal() {
  isPasswordModalOpen.value = false;
  passwordModalError.value = '';
  passwordModalMessage.value = '';
  passwordForm.current_password = '';
  passwordForm.new_password = '';
  passwordForm.new_password_confirm = '';
}

const openProfileModal = () => {
  profileDraft.available_weekly_hours = profileInfo.available_weekly_hours;
  profileDraft.preferred_learning_style = profileInfo.preferred_learning_style;
  profileDraft.topic_ids = [...profileInfo.topic_ids];
  topicSearchKeyword.value = '';
  profileModalError.value = '';
  isProfileModalOpen.value = true;
};

function closeProfileModal() {
  isProfileModalOpen.value = false;
  profileModalError.value = '';
  topicSearchKeyword.value = '';
  profileDraft.available_weekly_hours = profileInfo.available_weekly_hours;
  profileDraft.preferred_learning_style = profileInfo.preferred_learning_style;
  profileDraft.topic_ids = [...profileInfo.topic_ids];
}

const addTopic = (topicId) => {
  if (profileDraft.topic_ids.includes(topicId)) return;

  profileDraft.topic_ids = [...profileDraft.topic_ids, topicId];
};

const removeTopic = (topicId) => {
  profileDraft.topic_ids = profileDraft.topic_ids.filter((id) => id !== topicId);
};

const saveAccountInfo = async () => {
  const nickname = accountDraft.nickname.trim();

  if (!nickname) {
    accountModalError.value = '닉네임을 입력해주세요.';
    return;
  }

  isSavingAccount.value = true;
  accountModalError.value = '';

  try {
    const updated = await updateMyInfo({ nickname });

    setAccountInfo(updated);
    closeAccountModal();
  } catch (error) {
    accountModalError.value = error?.message || '기본 정보 저장에 실패했습니다.';
  } finally {
    isSavingAccount.value = false;
  }
};

const saveProfileInfo = async () => {
  const hours = Number(profileDraft.available_weekly_hours || 0);

  if (hours < 0 || hours > 168) {
    profileModalError.value = '주간 학습 가능 시간은 0 이상 168 이하로 입력해주세요.';
    return;
  }

  isSavingProfile.value = true;
  profileModalError.value = '';

  try {
    const updated = await updateMyProfile({
      available_weekly_hours: hours,
      preferred_learning_style: profileDraft.preferred_learning_style || null,
      topic_ids: profileDraft.topic_ids,
    });

    setProfileInfo(updated);
    closeProfileModal();
  } catch (error) {
    profileModalError.value = error?.message || '학습 프로필 저장에 실패했습니다.';
  } finally {
    isSavingProfile.value = false;
  }
};

const changeUserPassword = async () => {
  passwordModalError.value = '';
  passwordModalMessage.value = '';

  if (
    !passwordForm.current_password ||
    !passwordForm.new_password ||
    !passwordForm.new_password_confirm
  ) {
    passwordModalError.value = '모든 비밀번호 필드를 입력해주세요.';
    return;
  }

  if (passwordForm.new_password !== passwordForm.new_password_confirm) {
    passwordModalError.value = '새 비밀번호가 일치하지 않습니다.';
    return;
  }

  isChangingPassword.value = true;

  try {
    await changePassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
      new_password_confirm: passwordForm.new_password_confirm,
    });

    window.alert('비밀번호가 변경되었습니다.');
    closePasswordModal();
  } catch (error) {
    passwordModalError.value = error?.message || '비밀번호 변경에 실패했습니다.';
  } finally {
    isChangingPassword.value = false;
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleEscKey);
  loadMyPage();
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEscKey);
});
</script>
