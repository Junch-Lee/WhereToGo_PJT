import { createRouter, createWebHistory } from 'vue-router';
import { isAuthenticated } from '../utils/auth';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/pages/user/HomePage.vue'),
  },
  {
    path: '/signup',
    name: 'Signup',
    component: () => import('@/pages/auth/SignupPage.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/auth/LoginPage.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/mypage',
    name: 'MyPage',
    component: () => import('@/pages/user/MyPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/curriculum/:id',
    name: 'CurriculumDetail',
    component: () => import('@/pages/user/CurriculumDetailPage.vue'),
    meta: { requiresAuth: true },
  },

  /**
   * 홈 화면에서 학습 목표를 입력한 뒤 이동하는 질문 화면입니다.
   *
   * HomePage.vue의 handleSubmit에서:
   * sessionStorage.setItem('interview_goal', goal);
   * router.push('/chat');
   *
   * 위 코드와 연결됩니다.
   */
  {
    path: '/chat',
    name: 'ChatInterview',
    component: () => import('@/pages/user/ChatInterview.vue'),
    meta: { requiresAuth: true },
  },

  /**
   * ChatInterview.vue에서 질문 완료 후 이동하는 요약 화면입니다.
   *
   * 아직 InterviewSummary.vue 파일이 없다면,
   * 이 라우트는 주석 처리하거나 파일 생성 후 사용하면 됩니다.
   */
  {
    path: '/interview/summary',
    name: 'InterviewSummary',
    component: () => import('@/pages/user/InterviewSummary.vue'),
    meta: { requiresAuth: true },
  },
  {
  path: '/curriculum/result',
  name: 'CurriculumResult',
  component: () => import('@/pages/user/CurriculumResult.vue'),
  meta: { requiresAuth: true },
  },
  {
    path: '/learning',
    name: 'Learning',
    component: () => import('@/pages/user/LearningDashboard.vue'),
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const loggedIn = isAuthenticated();

  if (to.meta.requiresAuth && !loggedIn) {
    return {
      path: '/login',
      query: { redirect: to.fullPath },
    };
  }

  if (to.meta.guestOnly && loggedIn) {
    return '/';
  }

  return true;
});

export default router;
