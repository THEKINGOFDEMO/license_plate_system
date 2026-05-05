<template>
  <section class="page-header compact-page-header">
    <div>
      <span class="eyebrow">技术说明</span>
      <h2>系统架构、技术路线与实验指标说明</h2>
      <p>本页集中展示系统实现结构、核心技术路线、实验指标和适用范围说明。</p>
    </div>
  </section>

  <section class="panel architecture-panel">
    <div class="panel-header">
      <h3>系统架构图</h3>
      <p>展示从用户访问到前后端交互、模型推理和结果存储的调用关系。</p>
    </div>
    <ArchitectureDiagram />
  </section>

  <section class="panel route-panel">
    <div class="panel-header">
      <h3>技术路线图</h3>
      <p>展示从数据准备到 Web 系统实现的整体技术路线。</p>
    </div>
    <div class="tech-route-flow">
      <template v-for="(step, index) in routeSteps" :key="step.title">
        <article class="route-step">
          <strong>{{ step.title }}</strong>
          <span>{{ step.description }}</span>
        </article>
        <div v-if="index < routeSteps.length - 1" class="route-arrow" aria-hidden="true"></div>
      </template>
    </div>
  </section>

  <section class="panel records-panel">
    <div class="panel-header">
      <h3>实验指标表</h3>
      <p>展示车牌检测、字符识别和串联推理阶段的实验结果。</p>
    </div>
    <div class="table-scroll">
      <table class="records-table metrics-table">
        <thead>
          <tr>
            <th>模块</th>
            <th>指标</th>
            <th>结果</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>YOLO 检测</td>
            <td>mAP50</td>
            <td>0.995</td>
          </tr>
          <tr>
            <td>CRNN 识别</td>
            <td>字符准确率</td>
            <td>0.9883</td>
          </tr>
          <tr>
            <td>CRNN 识别</td>
            <td>整牌准确率</td>
            <td>0.9350</td>
          </tr>
          <tr>
            <td>串联推理</td>
            <td>整牌准确率</td>
            <td>0.9450</td>
          </tr>
          <tr>
            <td>串联推理</td>
            <td>字符准确率</td>
            <td>0.9916</td>
          </tr>
          <tr>
            <td>串联推理</td>
            <td>测试图片数</td>
            <td>1000</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <section class="panel about-scope-panel">
    <div class="panel-header">
      <h3>适用范围说明</h3>
    </div>
    <p class="about-scope-copy">
      当前模型主要基于普通中国车牌数据训练，对清晰、正面、无遮挡的普通车牌识别效果较好。
      对于新能源车牌、模糊图像、强反光、严重倾斜或遮挡场景，识别结果可能存在误差。
    </p>
  </section>
</template>

<script setup>
import ArchitectureDiagram from "@/components/ArchitectureDiagram.vue";

const routeSteps = [
  { title: "CCPD 数据集", description: "构建车牌检测与识别训练数据基础。" },
  { title: "数据预处理", description: "生成 YOLO 标签和 CRNN 训练样本。" },
  { title: "YOLO 训练", description: "完成车牌区域检测模型训练与验证。" },
  { title: "CRNN 训练", description: "完成车牌字符识别模型训练与评估。" },
  { title: "串联推理", description: "完成检测、裁剪、识别的一体化推理。" },
  { title: "Django / Vue 系统", description: "提供接口服务、结果展示与记录查询。" },
];
</script>
