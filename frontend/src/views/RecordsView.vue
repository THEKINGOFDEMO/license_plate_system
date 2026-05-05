<template>
  <section class="page-header">
    <div>
      <span class="eyebrow">历史记录</span>
      <h2>查看识别记录并进行筛选检索</h2>
      <p>支持按状态、关键词和分页方式查看历史识别结果，并可进一步查看单条记录详情。</p>
    </div>
    <button class="secondary-button" type="button" @click="loadRecords" :disabled="loading">
      {{ loading ? "刷新中..." : "刷新记录" }}
    </button>
  </section>

  <RecordTable
    :records="records"
    :loading="loading"
    :error-message="errorMessage"
    :empty-message="emptyMessage"
    :count="pagination.count"
    :page="pagination.page"
    :page-size="pagination.pageSize"
    :status-filter="filters.status"
    :keyword="filters.keyword"
    @update:status-filter="handleStatusFilterChange"
    @update:keyword="handleKeywordInput"
    @page-change="handlePageChange"
    @page-size-change="handlePageSizeChange"
    @refresh="loadRecords"
  />
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import RecordTable from "@/components/RecordTable.vue";
import { fetchRecords } from "@/api/recognition";

const records = ref([]);
const loading = ref(false);
const errorMessage = ref("");
const emptyMessage = ref("当前还没有历史记录。");
const filters = reactive({
  status: "",
  keyword: "",
});
const pagination = reactive({
  count: 0,
  page: 1,
  pageSize: 10,
});

async function loadRecords() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const response = await fetchRecords({
      page: pagination.page,
      page_size: pagination.pageSize,
      status: filters.status || undefined,
      keyword: filters.keyword || undefined,
    });
    const data = response.data || {};
    records.value = data.results || data.records || [];
    pagination.count = Number(data.count ?? records.value.length);
    pagination.page = Number(data.page ?? pagination.page);
    pagination.pageSize = Number(data.page_size ?? pagination.pageSize);
    if (!records.value.length) {
      emptyMessage.value = "当前筛选条件下没有记录。";
    }
  } catch (error) {
    records.value = [];
    errorMessage.value = error.message || "加载历史记录失败";
  } finally {
    loading.value = false;
  }
}

function handlePageChange(nextPage) {
  pagination.page = nextPage;
  loadRecords();
}

function handlePageSizeChange(nextSize) {
  pagination.pageSize = nextSize;
  pagination.page = 1;
  loadRecords();
}

function handleStatusFilterChange(nextStatus) {
  filters.status = nextStatus;
  pagination.page = 1;
  loadRecords();
}

function handleKeywordInput(nextKeyword) {
  filters.keyword = nextKeyword;
  pagination.page = 1;
  loadRecords();
}

onMounted(() => {
  loadRecords();
});
</script>
