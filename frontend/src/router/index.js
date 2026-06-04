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
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/auth/LoginPage.vue'),
  },
  {
    path: '/mypage',
    name: 'MyPage',
    component: () => import('@/pages/user/MyPage.vue'),
    meta: { requiresAuth: true },
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
  //   path: '/curriculum/:id',
  //   name: 'CurriculumDetail',
  //   component: () => import('@/pages/user/HomePage.vue'),
  // },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const loggedIn = isAuthenticated();

  if (to.meta.requiresAuth && !loggedIn) {
    return {
      path: "/login",
      query: {redirect: to.fullPath}
    };
  }

  if (to.meta.guestOnly && loggedIn) {
    return "/";
  }

  return true;
})

export default router;
