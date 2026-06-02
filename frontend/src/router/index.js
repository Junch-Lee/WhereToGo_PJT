import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  {
    path: '/',
    redirect: '/signup',
  },
  {
    path: '/signup',
    name: 'Signup',
    component: () => import('@/pages/auth/SignupPage.vue'),
  },
  // {
  //   path: '/login',
  //   name: 'Login',
  //   component: () => import('@/pages/auth/LoginPage.vue'),
  // },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;