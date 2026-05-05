<template>
  <div class="login-shell">
    <section class="login-panel">
      <div class="login-header">
        <span class="eyebrow">系统登录</span>
        <h1>基于深度学习的车牌检测与识别系统</h1>
        <p>请输入管理员账号和密码以进入系统。</p>
      </div>

      <form class="login-form" @submit.prevent="handleLogin">
        <label class="form-field">
          <span>账号</span>
          <input v-model.trim="form.username" type="text" placeholder="请输入账号" />
        </label>

        <label class="form-field">
          <span>密码</span>
          <input v-model="form.password" type="password" placeholder="请输入密码" />
        </label>

        <div v-if="errorMessage" class="login-error">{{ errorMessage }}</div>

        <button class="primary-button login-button" type="submit">登录系统</button>
      </form>

      <div class="login-hint">
        <strong>测试账号：</strong>
        <span>admin / 123456</span>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { DEMO_PASSWORD, DEMO_USERNAME, login } from "@/utils/auth";

const router = useRouter();
const route = useRoute();
const errorMessage = ref("");
const form = reactive({
  username: "",
  password: "",
});

function handleLogin() {
  if (form.username !== DEMO_USERNAME || form.password !== DEMO_PASSWORD) {
    errorMessage.value = "账号或密码不正确。";
    return;
  }

  login(form.username);
  const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/";
  router.push(redirect);
}
</script>
