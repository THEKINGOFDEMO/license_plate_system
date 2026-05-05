<template>
  <section class="page-header">
    <div>
      <span class="eyebrow">车牌识别</span>
      <h2>上传车辆图片并调用后端完成识别</h2>
      <p>上传字段名固定为 <code>image</code>，系统将按“图片上传 → 车牌检测 → 车牌裁剪 → 字符识别 → 结果保存”的流程完成处理。</p>
    </div>
    <div class="status-chip" :class="{ ready: healthReady }">
      后端状态：{{ healthReady ? "已连接" : "待确认" }}
    </div>
  </section>

  <section class="flow-strip panel">
    <span>图片上传</span>
    <span>车牌检测</span>
    <span>车牌裁剪</span>
    <span>字符识别</span>
    <span>结果保存</span>
  </section>

  <section class="recognize-layout">
    <ImageUploader
      :preview-url="previewUrl"
      :selected-file-name="selectedFile?.name || ''"
      :loading="loading"
      @file-selected="handleFileSelected"
      @reset="resetSelection"
      @submit="submitRecognition"
    />

    <ResultCard
      :loading="loading"
      :result="result"
      :error-message="errorMessage"
      :empty-message="emptyMessage"
      scope-note="当前模型主要面向普通车牌场景，新能源车牌或复杂场景可能存在识别误差。"
    />
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import ImageUploader from "@/components/ImageUploader.vue";
import ResultCard from "@/components/ResultCard.vue";
import { fetchHealth, recognizeImage } from "@/api/recognition";

const selectedFile = ref(null);
const previewUrl = ref("");
const loading = ref(false);
const result = ref(null);
const errorMessage = ref("");
const emptyMessage = ref("请先选择一张本地图片，再开始识别。");
const healthReady = ref(false);

function revokePreview() {
  if (previewUrl.value?.startsWith("blob:")) {
    URL.revokeObjectURL(previewUrl.value);
  }
}

function handleFileSelected(file) {
  revokePreview();
  selectedFile.value = file;
  previewUrl.value = URL.createObjectURL(file);
  result.value = null;
  errorMessage.value = "";
  emptyMessage.value = "";
}

function resetSelection() {
  revokePreview();
  selectedFile.value = null;
  previewUrl.value = "";
  result.value = null;
  errorMessage.value = "";
  emptyMessage.value = "请重新选择图片。";
}

async function loadHealth() {
  try {
    const response = await fetchHealth();
    healthReady.value = Boolean(response.data?.model_ready);
  } catch (error) {
    healthReady.value = false;
  }
}

async function submitRecognition() {
  if (!selectedFile.value) {
    errorMessage.value = "请先选择要识别的图片。";
    return;
  }

  loading.value = true;
  result.value = null;
  errorMessage.value = "";
  emptyMessage.value = "";

  try {
    const response = await recognizeImage(selectedFile.value);
    result.value = response.data;
    if (response.data?.status === "no_detection") {
      emptyMessage.value =
        response.data?.message || "未检测到车牌，请尝试上传更清晰、车牌区域更明显的图片。";
    }
  } catch (error) {
    result.value = null;
    errorMessage.value = error.message || "识别失败";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadHealth();
});
</script>
