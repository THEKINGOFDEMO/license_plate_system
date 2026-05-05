<template>
  <teleport to="body">
    <div v-if="visible && record" class="modal-backdrop" @click.self="$emit('close')">
      <section class="modal-card">
        <div class="modal-header">
          <div>
            <h3>记录详情</h3>
            <p>{{ record.original_filename || "--" }}</p>
          </div>
          <button class="modal-close" type="button" @click="$emit('close')">×</button>
        </div>

        <div class="detail-grid">
          <article class="detail-item">
            <span>状态</span>
            <strong>{{ record.status || "--" }}</strong>
          </article>
          <article class="detail-item">
            <span>车牌号</span>
            <strong>{{ record.plate_text || "--" }}</strong>
          </article>
          <article class="detail-item">
            <span>置信度</span>
            <strong>{{ formatConfidence(record.yolo_confidence) }}</strong>
          </article>
          <article class="detail-item">
            <span>时间</span>
            <strong>{{ formatDate(record.created_at) }}</strong>
          </article>
          <article class="detail-item detail-span">
            <span>BBox</span>
            <strong>{{ formatBbox(record.bbox) }}</strong>
          </article>
        </div>

        <div class="image-result-grid detail-images">
          <div class="image-card">
            <h4>标注结果图</h4>
            <img v-if="record.annotatedUrl" :src="record.annotatedUrl" alt="标注结果图" />
            <p v-else>暂无标注图</p>
          </div>
          <div class="image-card">
            <h4>车牌裁剪图</h4>
            <img v-if="record.cropUrl" :src="record.cropUrl" alt="车牌裁剪图" />
            <p v-else>暂无裁剪图</p>
          </div>
        </div>
      </section>
    </div>
  </teleport>
</template>

<script setup>
defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  record: {
    type: Object,
    default: null,
  },
});

defineEmits(["close"]);

function formatConfidence(value) {
  return typeof value === "number" ? value.toFixed(4) : "--";
}

function formatDate(value) {
  if (!value) {
    return "--";
  }
  return value.replace("T", " ").replace("Z", "");
}

function formatBbox(bbox) {
  return Array.isArray(bbox) && bbox.length === 4 ? `[${bbox.join(", ")}]` : "--";
}
</script>
