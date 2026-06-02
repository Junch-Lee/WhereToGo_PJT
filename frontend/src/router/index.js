import { createRouter, createWebHistory } from 'vue-router';

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
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/auth/LoginPage.vue'),
  },
  // {
  //   path: '/chat',
  //   name: 'Chat',
  //   component: () => import('@/pages/user/HomePage.vue'),
  // },
  // {
  //   path: '/learning',
  //   name: 'Learning',
  //   component: () => import('@/pages/user/HomePage.vue'),
  // },
  // {
  //   path: '/mypage',
  //   name: 'MyPage',
  //   component: () => import('@/pages/user/HomePage.vue'),
  // },
  // {
  //   path: '/curriculum/:id',
  //   name: 'CurriculumDetail',
  //   component: () => import('@/pages/user/HomePage.vue'),
  // },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;