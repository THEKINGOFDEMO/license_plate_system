<template>
  <section class="page-header compact-page-header">
    <div>
      <span class="eyebrow">系统总览</span>
      <h2>车牌检测与识别系统运行概况</h2>
      <p>首页用于展示系统状态、识别统计、最近记录和常用入口，便于快速了解当前运行情况。</p>
    </div>
  </section>

  <section class="overview-grid">
    <article class="panel overview-card">
      <span class="metric-label">后端状态</span>
      <strong :class="healthState.status ? 'status-text-ok' : 'status-text-error'">
        {{ healthState.status ? "已连接" : "未连接" }}
      </strong>
    </article>
    <article class="panel overview-card">
      <span class="metric-label">模型状态</span>
      <strong :class="healthState.modelReady ? 'status-text-ok' : 'status-text-warn'">
        {{ healthState.modelReady ? "可用" : "未配置" }}
      </strong>
    </article>
    <article class="panel overview-card">
      <span class="metric-label">当前用户</span>
      <strong>{{ currentUser }}</strong>
    </article>
  </section>

  <section class="home-two-column">
    <article class="panel home-summary-panel">
      <div class="panel-header">
        <h3>识别统计</h3>
        <p>展示当前系统累计记录及不同状态的数量分布。</p>
      </div>
      <div class="stats-grid compact-stats-grid">
        <article class="stat-card stat-neutral">
          <span class="metric-label">累计识别次数</span>
          <strong>{{ stats.total }}</strong>
        </article>
        <article class="stat-card stat-ok">
          <span class="metric-label">识别成功次数</span>
          <strong>{{ stats.ok }}</strong>
        </article>
        <article class="stat-card stat-warn">
          <span class="metric-label">未检测次数</span>
          <strong>{{ stats.noDetection }}</strong>
        </article>
        <article class="stat-card stat-error">
          <span class="metric-label">错误次数</span>
          <strong>{{ stats.error }}</strong>
        </article>
      </div>
      <div class="chart-caption">
        <span class="chart-caption-mark ok"></span>
        <span>识别成功</span>
        <span class="chart-caption-mark warn"></span>
        <span>未检测到车牌</span>
        <span class="chart-caption-mark error"></span>
        <span>错误记录</span>
      </div>
      <StatsDistributionChart
        :total="stats.total"
        :ok="stats.ok"
        :no-detection="stats.noDetection"
        :error="stats.error"
      />
    </article>

    <article class="panel quick-entry-panel">
      <div class="panel-header">
        <h3>快捷入口</h3>
        <p>提供识别、记录查询和技术说明的快速访问入口。</p>
      </div>
      <div class="quick-entry-grid">
        <RouterLink to="/recognize" class="quick-entry-card">
          <div class="quick-entry-icon">识</div>
          <strong>开始识别</strong>
          <span>上传车辆图片并执行车牌检测与识别。</span>
        </RouterLink>
        <RouterLink to="/records" class="quick-entry-card">
          <div class="quick-entry-icon">记</div>
          <strong>查看历史记录</strong>
          <span>按状态、关键词和分页方式查看识别记录。</span>
        </RouterLink>
        <RouterLink to="/about" class="quick-entry-card">
          <div class="quick-entry-icon">说</div>
          <strong>查看系统说明</strong>
          <span>查看系统架构、技术路线和实验指标。</span>
        </RouterLink>
      </div>
    </article>
  </section>

  <section class="panel home-process-panel">
    <div class="panel-header">
      <h3>运行流程图</h3>
      <p>展示从图片输入到识别结果保存的系统处理流程。</p>
    </div>
    <ProcessFlowDiagram />
  </section>

  <section class="panel records-panel home-records-panel">
    <div class="panel-header split-header">
      <div>
        <h3>最近识别记录</h3>
        <p>展示最近 5 条识别记录，用于快速查看系统近期处理结果。</p>
      </div>
      <RouterLink to="/records" class="secondary-button">查看全部记录</RouterLink>
    </div>

    <div v-if="recordLoading" class="state-box">
      <strong>正在加载最近记录...</strong>
    </div>

    <div v-else-if="recordError" class="state-box state-error">
      <strong>加载失败</strong>
      <span>{{ recordError }}</span>
    </div>

    <div v-else-if="!recentRecords.length" class="state-box">
      <strong>暂无记录</strong>
      <span>当前还没有识别记录。</span>
    </div>

    <div v-else class="table-scroll">
      <table class="records-table compact-table">
        <thead>
          <tr>
            <th>时间</th>
            <th>状态</th>
            <th>车牌号</th>
            <th>置信度</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="record in recentRecords" :key="record.record_id || record.id">
            <td>{{ formatDateTime(record.created_at) }}</td>
            <td>
              <span class="table-status" :class="`status-${record.status}`">{{ formatStatus(record.status) }}</span>
            </td>
            <td>{{ record.plate_text || "--" }}</td>
            <td>{{ formatConfidence(record.yolo_confidence) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { RouterLink } from "vue-router";
import StatsDistributionChart from "@/components/StatsDistributionChart.vue";
import ProcessFlowDiagram from "@/components/ProcessFlowDiagram.vue";
import { fetchHealth, fetchRecords, getStats } from "@/api/recognition";
import { getLoginUser } from "@/utils/auth";
import { formatConfidence, formatDateTime, formatStatus } from "@/utils/format";

const healthState = reactive({
  status: false,
  modelReady: false,
});

const stats = reactive({
  total: 0,
  ok: 0,
  noDetection: 0,
  error: 0,
});

const recentRecords = ref([]);
const recordLoading = ref(false);
const recordError = ref("");
const currentUser = computed(() => getLoginUser());

async function loadHealth() {
  try {
    const response = await fetchHealth();
    healthState.status = response.data?.status === "ok";
    healthState.modelReady = Boolean(response.data?.model_ready);
  } catch (error) {
    healthState.status = false;
    healthState.modelReady = false;
  }
}

async function loadStats() {
  try {
    const response = await getStats();
    stats.total = Number(response.data?.total ?? 0);
    stats.ok = Number(response.data?.ok ?? 0);
    stats.noDetection = Number(response.data?.no_detection ?? 0);
    stats.error = Number(response.data?.error ?? 0);
  } catch (error) {
    stats.total = 0;
    stats.ok = 0;
    stats.noDetection = 0;
    stats.error = 0;
  }
}

async function loadRecentRecords() {
  recordLoading.value = true;
  recordError.value = "";
  try {
    const response = await fetchRecords({ page: 1, page_size: 5 });
    recentRecords.value = response.data?.results || response.data?.records || [];
  } catch (error) {
    recentRecords.value = [];
    recordError.value = error.message || "加载最近记录失败";
  } finally {
    recordLoading.value = false;
  }
}

onMounted(() => {
  loadHealth();
  loadStats();
  loadRecentRecords();
});
</script>
