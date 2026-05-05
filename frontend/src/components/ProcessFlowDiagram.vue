<template>
  <div class="diagram-shell">
    <svg class="process-svg" viewBox="0 0 1120 280" role="img" aria-label="系统运行流程图">
      <defs>
        <linearGradient id="processCardBg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#fffdf9" />
          <stop offset="100%" stop-color="#f8f1e7" />
        </linearGradient>
        <linearGradient id="processBadgeBg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#1f6b54" />
          <stop offset="100%" stop-color="#2f8e70" />
        </linearGradient>
        <filter id="softShadow" x="-20%" y="-20%" width="140%" height="160%">
          <feDropShadow dx="0" dy="12" stdDeviation="12" flood-color="rgba(55,33,14,0.14)" />
        </filter>
      </defs>

      <g v-for="(step, index) in steps" :key="step.title">
        <rect
          :x="60 + index * 212"
          y="46"
          width="160"
          height="188"
          rx="26"
          fill="url(#processCardBg)"
          stroke="rgba(95, 72, 46, 0.14)"
          filter="url(#softShadow)"
        />
        <rect
          :x="104 + index * 212"
          y="66"
          width="72"
          height="72"
          rx="24"
          fill="url(#processBadgeBg)"
        />
        <text
          :x="140 + index * 212"
          y="111"
          text-anchor="middle"
          fill="#ffffff"
          font-size="28"
          font-weight="700"
        >
          {{ step.icon }}
        </text>
        <text
          :x="140 + index * 212"
          y="168"
          text-anchor="middle"
          fill="#34261c"
          font-size="24"
          font-weight="700"
        >
          {{ step.title }}
        </text>
        <text
          :x="140 + index * 212"
          y="202"
          text-anchor="middle"
          fill="#6e5846"
          font-size="16"
        >
          {{ step.line1 }}
        </text>
        <text
          :x="140 + index * 212"
          y="226"
          text-anchor="middle"
          fill="#6e5846"
          font-size="16"
        >
          {{ step.line2 }}
        </text>

        <g v-if="index < steps.length - 1">
          <path
            :d="`M ${220 + index * 212} 140 H ${252 + index * 212} H ${276 + index * 212}`"
            fill="none"
            stroke="#8ab7a5"
            stroke-width="4"
            stroke-linecap="round"
          />
          <path
            :d="`M ${276 + index * 212} 140 l -12 -12 M ${276 + index * 212} 140 l -12 12`"
            fill="none"
            stroke="#8ab7a5"
            stroke-width="4"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </g>
      </g>
    </svg>
  </div>
</template>

<script setup>
const steps = [
  { icon: "图", title: "图片上传", line1: "用户上传待识别", line2: "的车辆图片" },
  { icon: "检", title: "车牌检测", line1: "YOLO 模型定位", line2: "车牌区域" },
  { icon: "裁", title: "车牌裁剪", line1: "根据检测框提取", line2: "车牌图像" },
  { icon: "识", title: "字符识别", line1: "CRNN 模型输出", line2: "完整字符序列" },
  { icon: "存", title: "结果保存", line1: "保存识别结果、", line2: "标注图与记录" },
];
</script>
