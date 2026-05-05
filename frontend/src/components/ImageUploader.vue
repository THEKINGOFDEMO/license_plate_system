<template>
  <section class="panel upload-panel">
    <div class="panel-header">
      <h3>上传图片</h3>
      <p>支持常见图片格式，建议上传车牌区域清晰、无遮挡、角度较正的普通车牌图片。</p>
    </div>

    <label class="upload-dropzone" for="image-input">
      <input id="image-input" class="hidden-input" type="file" accept="image/*" @change="onChange" />
      <div v-if="previewUrl" class="upload-preview">
        <img :src="previewUrl" alt="预览图" />
      </div>
      <div v-else class="upload-placeholder">
        <strong>点击选择图片</strong>
        <span>选择后将在右侧展示识别结果</span>
      </div>
    </label>

    <div class="file-meta" v-if="selectedFileName">
      当前文件：<strong>{{ selectedFileName }}</strong>
    </div>

    <div class="action-row">
      <button class="primary-button" type="button" @click="$emit('submit')" :disabled="loading">
        {{ loading ? "识别中..." : "开始识别" }}
      </button>
      <button class="secondary-button" type="button" @click="$emit('reset')" :disabled="loading">
        重新选择图片
      </button>
    </div>
  </section>
</template>

<script setup>
const props = defineProps({
  previewUrl: {
    type: String,
    default: "",
  },
  selectedFileName: {
    type: String,
    default: "",
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["file-selected", "reset", "submit"]);

function onChange(event) {
  const file = event.target.files?.[0];
  if (!file) {
    return;
  }
  emit("file-selected", file);
}
</script>
