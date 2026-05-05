<template>
  <div class="stats-chart-shell">
    <VChart class="stats-chart-canvas" :option="option" autoresize />
  </div>
</template>

<script setup>
import { computed } from "vue";
import VChart, { THEME_KEY } from "vue-echarts";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { PieChart } from "echarts/charts";
import { LegendComponent, TitleComponent, TooltipComponent } from "echarts/components";
import { provide } from "vue";

use([CanvasRenderer, PieChart, TitleComponent, TooltipComponent, LegendComponent]);
provide(THEME_KEY, "light");

const props = defineProps({
  total: {
    type: Number,
    default: 0,
  },
  ok: {
    type: Number,
    default: 0,
  },
  noDetection: {
    type: Number,
    default: 0,
  },
  error: {
    type: Number,
    default: 0,
  },
});

const option = computed(() => ({
  backgroundColor: "transparent",
  tooltip: {
    trigger: "item",
    formatter: "{b}<br/>{c} 次 ({d}%)",
  },
  legend: {
    bottom: 0,
    left: "center",
    itemWidth: 14,
    itemHeight: 14,
    textStyle: {
      color: "#6e5846",
      fontSize: 13,
    },
  },
  title: {
    text: String(props.total ?? 0),
    subtext: "累计记录",
    left: "center",
    top: "39%",
    textStyle: {
      color: "#34261c",
      fontSize: 26,
      fontWeight: 700,
    },
    subtextStyle: {
      color: "#6e5846",
      fontSize: 13,
      lineHeight: 18,
    },
  },
  series: [
    {
      name: "状态分布",
      type: "pie",
      radius: ["54%", "74%"],
      center: ["50%", "42%"],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 12,
        borderColor: "#fff7ee",
        borderWidth: 4,
      },
      label: {
        show: true,
        color: "#6e5846",
        formatter: "{b}\n{c}",
        fontSize: 12,
      },
      labelLine: {
        length: 14,
        length2: 10,
      },
      data: [
        { value: props.ok, name: "识别成功", itemStyle: { color: "#1f6b54" } },
        { value: props.noDetection, name: "未检测到车牌", itemStyle: { color: "#d88636" } },
        { value: props.error, name: "错误记录", itemStyle: { color: "#c15a4c" } },
      ],
    },
  ],
}));
</script>
