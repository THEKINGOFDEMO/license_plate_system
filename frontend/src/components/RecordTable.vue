<template>
  <section class="panel records-panel">
    <div class="panel-header">
      <h3>识别历史</h3>
      <p>支持状态筛选、关键词搜索、分页查看和记录详情预览。</p>
    </div>

    <div class="records-toolbar">
      <label class="toolbar-field">
        <span>状态筛选</span>
        <select :value="statusFilter" @change="$emit('update:status-filter', $event.target.value)">
          <option value="">全部</option>
          <option value="ok">识别成功</option>
          <option value="no_detection">未检测到</option>
          <option value="error">错误</option>
        </select>
      </label>

      <label class="toolbar-field search-field">
        <span>关键词搜索</span>
        <input :value="keyword" type="text" placeholder="按文件名或车牌号搜索" @input="$emit('update:keyword', $event.target.value)" />
      </label>

      <button class="secondary-button" type="button" @click="$emit('refresh')">刷新</button>
    </div>

    <div v-if="loading" class="state-box">
      <strong>正在加载历史记录...</strong>
    </div>

    <div v-else-if="errorMessage" class="state-box state-error">
      <strong>加载失败</strong>
      <span>{{ errorMessage }}</span>
    </div>

    <div v-else-if="!records.length" class="state-box">
      <strong>暂无记录</strong>
      <span>{{ emptyMessage }}</span>
    </div>

    <div v-else class="table-scroll">
      <table class="records-table">
        <thead>
          <tr>
            <th>record_id</th>
            <th>上传文件名</th>
            <th>status</th>
            <th>plate_text</th>
            <th>yolo_confidence</th>
            <th>created_at</th>
            <th>标注图</th>
            <th>裁剪图</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="record in normalizedRecords" :key="record.recordId">
            <td>{{ record.recordId }}</td>
            <td>{{ record.original_filename || "--" }}</td>
            <td>
              <span class="table-status" :class="`status-${record.status}`">{{ formatStatus(record.status) }}</span>
            </td>
            <td>{{ record.plate_text || "--" }}</td>
            <td>{{ formatConfidence(record.yolo_confidence) }}</td>
            <td>{{ formatDate(record.created_at) }}</td>
            <td>
              <a v-if="record.annotatedUrl" :href="record.annotatedUrl" target="_blank" rel="noreferrer">查看标注图</a>
              <span v-else>--</span>
            </td>
            <td>
              <a v-if="record.cropUrl" :href="record.cropUrl" target="_blank" rel="noreferrer">查看裁剪图</a>
              <span v-else>--</span>
            </td>
            <td>
              <button class="table-action" type="button" @click="selectedRecord = record">查看详情</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination-bar" v-if="count > 0">
      <div class="pagination-summary">
        共 {{ count }} 条，第 {{ page }} / {{ totalPages }} 页
      </div>
      <div class="pagination-controls">
        <label class="toolbar-field compact-field">
          <span>每页</span>
          <select :value="pageSize" @change="$emit('page-size-change', Number($event.target.value))">
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
          </select>
        </label>
        <button class="secondary-button" type="button" :disabled="page <= 1" @click="$emit('page-change', page - 1)">上一页</button>
        <button class="secondary-button" type="button" :disabled="page >= totalPages" @click="$emit('page-change', page + 1)">下一页</button>
      </div>
    </div>

    <RecordDetailModal :visible="Boolean(selectedRecord)" :record="selectedRecord" @close="selectedRecord = null" />
  </section>
</template>

<script setup>
import { computed, ref } from "vue";
import { resolveApiBaseUrl } from "@/api/recognition";
import RecordDetailModal from "./RecordDetailModal.vue";

const props = defineProps({
  records: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  errorMessage: {
    type: String,
    default: "",
  },
  emptyMessage: {
    type: String,
    default: "",
  },
  count: {
    type: Number,
    default: 0,
  },
  page: {
    type: Number,
    default: 1,
  },
  pageSize: {
    type: Number,
    default: 10,
  },
  statusFilter: {
    type: String,
    default: "",
  },
  keyword: {
    type: String,
    default: "",
  },
});

defineEmits(["update:status-filter", "update:keyword", "page-change", "page-size-change", "refresh"]);

const selectedRecord = ref(null);
const apiBaseUrl = resolveApiBaseUrl();
const totalPages = computed(() => Math.max(1, Math.ceil(props.count / props.pageSize)));

const normalizedRecords = computed(() =>
  props.records.map((record) => {
    const annotatedUrl = toMediaUrl(record.annotated_image_url || record.annotated_image_path);
    const cropUrl = toMediaUrl(record.crop_image_url || record.crop_image_path);
    return {
      ...record,
      recordId: record.record_id ?? record.id ?? "--",
      annotatedUrl,
      cropUrl,
    };
  })
);

function toMediaUrl(value) {
  if (!value) {
    return "";
  }
  if (typeof value === "string" && value.startsWith("http")) {
    return value;
  }
  if (typeof value !== "string") {
    return "";
  }
  const normalized = value.replace(/\\/g, "/");
  const mediaIndex = normalized.lastIndexOf("/media/");
  if (mediaIndex >= 0) {
    return `${apiBaseUrl}${normalized.slice(mediaIndex)}`;
  }
  return "";
}

function formatStatus(value) {
  if (value === "ok") return "识别成功";
  if (value === "no_detection") return "未检测到";
  if (value === "error") return "错误";
  return value || "--";
}

function formatConfidence(value) {
  return typeof value === "number" ? value.toFixed(4) : "--";
}

function formatDate(value) {
  if (!value) {
    return "--";
  }
  return value.replace("T", " ").replace("Z", "");
}
</script>
