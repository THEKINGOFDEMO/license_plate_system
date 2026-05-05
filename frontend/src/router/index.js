import { createRouter, createWebHistory } from "vue-router";
import { isLoggedIn } from "@/utils/auth";
import AboutView from "@/views/AboutView.vue";
import HomeView from "@/views/HomeView.vue";
import LoginView from "@/views/LoginView.vue";
import RecognizeView from "@/views/RecognizeView.vue";
import RecordsView from "@/views/RecordsView.vue";

const routes = [
  {
    path: "/login",
    name: "login",
    component: LoginView,
    meta: { guestOnly: true, pageTitle: "登录" },
  },
  { path: "/", name: "home", component: HomeView, meta: { requiresAuth: true, pageTitle: "首页" } },
  { path: "/recognize", name: "recognize", component: RecognizeView, meta: { requiresAuth: true, pageTitle: "车牌识别" } },
  { path: "/records", name: "records", component: RecordsView, meta: { requiresAuth: true, pageTitle: "历史记录" } },
  { path: "/about", name: "about", component: AboutView, meta: { requiresAuth: true, pageTitle: "系统说明" } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach((to) => {
  const loggedIn = isLoggedIn();
  if (to.meta.requiresAuth && !loggedIn) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  if (to.meta.guestOnly && loggedIn) {
    return { name: "home" };
  }
  return true;
});

export default router;
