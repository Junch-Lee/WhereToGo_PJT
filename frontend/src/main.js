import { createApp } from 'vue';
import App from './App.vue';
import router from './router';

import '@/assets/styles/variables.css';
import '@/assets/styles/global.css';
import '@/assets/styles/user-shell.css';

createApp(App).use(router).mount('#app');
