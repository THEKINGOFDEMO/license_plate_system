<template>
  <section class="panel result-panel">
    <div class="panel-header">
      <h3>识别结果</h3>
      <p>展示后端返回的识别状态、检测坐标、置信度以及结果图片。</p>
    </div>

    <div v-if="loading" class="state-box">
      <strong>正在调用后端接口...</strong>
      <span>系统正在执行车牌检测与字符识别，请稍候。</span>
    </div>

    <div v-else-if="errorMessage" class="state-box state-error">
      <strong>识别失败</strong>
      <span>{{ errorMessage }}</span>
    </div>

    <div v-else-if="result?.status === 'no_detection'" class="state-box state-warn">
      <strong>未检测到车牌</strong>
      <span>{{ result.message || "未检测到车牌，请尝试上传更清晰、车牌区域更明显的图片。" }}</span>
      <div class="scope-note">
        {{ scopeNote }}
      </div>
    </div>

    <div v-else-if="result?.status === 'error'" class="state-box state-error">
      <strong>识别失败</strong>
      <span>{{ result.message || errorMessage }}</span>
      <div class="scope-note">
        {{ scopeNote }}
      </div>
    </div>

    <div v-else-if="result?.status === 'ok'" class="result-content">
      <div class="result-summary">
        <article class="summary-card accent-blue">
          <span>识别状态</span>
          <strong>识别成功</strong>
        </article>
        <article class="summary-card accent-green">
          <span>车牌号</span>
          <strong>{{ result.plate_text }}</strong>
        </article>
        <article class="summary-card accent-gold">
          <span>YOLO 置信度</span>
          <strong>{{ formatConfidence(result.yolo_confidence) }}</strong>
        </article>
        <article class="summary-card accent-blue">
          <span>BBox 坐标</span>
          <strong>{{ formatBbox(result.bbox) }}</strong>
        </article>
      </div>

      <div class="image-result-grid">
        <div class="image-card">
          <h4>标注结果图</h4>
          <img v-if="result.annotated_image_url" :src="result.annotated_image_url" alt="标注结果图" />
          <p v-else>暂无标注结果图</p>
        </div>
        <div class="image-card">
          <h4>车牌裁剪图</h4>
          <img v-if="result.crop_image_url" :src="result.crop_image_url" alt="车牌裁剪图" />
          <p v-else>暂无裁剪结果图</p>
        </div>
      </div>

      <div class="scope-note">
        {{ scopeNote }}
      </div>
    </div>

    <div v-else class="state-box">
      <strong>等待识别</strong>
      <span>{{ emptyMessage }}</span>
    </div>
  </section>
</template>

<script setup>
defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  result: {
    type: Object,
    default: null,
  },
  errorMessage: {
    type: String,
    default: "",
  },
  emptyMessage: {
    type: String,
    default: "",
  },
  scopeNote: {
    type: String,
    default: "",
  },
});

function formatConfidence(value) {
  if (typeof value !== "number") {
    return "--";
  }
  return value.toFixed(4);
}

function formatBbox(bbox) {
  if (!Array.isArray(bbox) || bbox.length !== 4) {
    return "--";
  }
  return `[${bbox.join(", ")}]`;
}
</script>
