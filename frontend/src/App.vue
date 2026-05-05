<template>
  <div :class="showShell ? 'app-shell' : 'login-app-shell'">
    <template v-if="showShell">
      <header class="topbar">
        <div class="brand">
          <span class="brand-badge">LPR</span>
          <div>
            <h1>基于深度学习的车牌检测与识别系统</h1>
            <p>YOLO 车牌检测 + CRNN 字符识别 + Django / Vue 应用</p>
          </div>
        </div>

        <div class="topbar-right">
          <nav class="nav-tabs">
            <RouterLink to="/" class="nav-link">首页</RouterLink>
            <RouterLink to="/recognize" class="nav-link">车牌识别</RouterLink>
            <RouterLink to="/records" class="nav-link">历史记录</RouterLink>
            <RouterLink to="/about" class="nav-link">系统说明</RouterLink>
          </nav>

          <div class="user-bar">
            <span class="user-pill">管理员：{{ loginUser }}</span>
            <button class="logout-button" type="button" @click="handleLogout">退出登录</button>
          </div>
        </div>
      </header>
    </template>

    <main :class="showShell ? 'page-shell' : 'login-page-shell'">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";
import { getLoginUser, logout } from "@/utils/auth";

const route = useRoute();
const router = useRouter();
const showShell = computed(() => route.name !== "login");
const loginUser = computed(() => getLoginUser());

function handleLogout() {
  logout();
  router.push({ name: "login" });
}
</script>
