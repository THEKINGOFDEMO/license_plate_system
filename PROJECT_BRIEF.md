# PROJECT_BRIEF.md

## 项目名称

基于深度学习的车牌检测与识别系统设计与实现

## 项目定位

这是一个本科毕业设计项目，需要完成：

```text
算法训练 + Web 系统实现 + 实验测试 + 论文材料
```

最终目标不是单纯写代码，而是形成一个可以答辩展示、可以写入论文的完整闭环。

## 固定技术路线

```text
CCPD 数据集
  -> 数据清洗、标注解析、增强、划分
  -> YOLO 系列模型完成车牌区域检测
  -> CRNN + CTC 完成车牌字符序列识别
  -> Django 后端集成模型推理
  -> Vue 前端完成上传、展示、可视化
```

## 已确定约束

- 使用 AutoDL 租 NVIDIA GPU 训练模型。
- 不需要围绕本地 AMD 显卡设计替代方案。
- 模型训练阶段在 AutoDL 完成。
- 本地主要用于 Django/Vue 开发、系统集成、模型推理演示和论文截图。
- 主线不能改成 PaddleOCR、HyperLPR、EasyOCR 或纯第三方 OCR 接口调用。
- 训练结果、实验指标和截图必须来自真实运行，不允许编造。

## 最小可交付系统

优先实现下面闭环：

1. 用户上传图片；
2. Django 后端保存图片；
3. YOLO 检测车牌框；
4. 根据检测框裁剪车牌区域；
5. CRNN 识别车牌字符；
6. 后端返回 JSON；
7. Vue 前端展示原图、检测框、识别结果；
8. 保存识别记录，并能简单查看历史记录。

## 推荐模型选择

- 检测模型：YOLOv8n 或 YOLOv8s。
- 识别模型：PyTorch CRNN，结构为 CNN + BiLSTM + CTC Loss。
- 数据集：CCPD2019 蓝牌为主；时间充足时再考虑 CCPD-Green 新能源车牌。

## 论文中需要保留的证据

- 数据预处理说明和截图；
- YOLO 训练日志、训练曲线、检测示例图；
- CRNN 训练日志、loss/accuracy 曲线、识别示例；
- 系统运行截图；
- 检测指标：Precision、Recall、mAP@0.5、mAP@0.5:0.95；
- 识别指标：字符准确率、整牌准确率；
- 系统测试表：上传、检测、识别、展示、历史记录。

## 目录建议

```text
backend/
frontend/
train/
models/
configs/
docs/
tests/
weights/        # gitignored
datasets/       # gitignored
runs/           # gitignored
```

## 当前阶段优先级

1. 搭建仓库骨架和 README；
2. 完成 CCPD 解析、YOLO 标签生成、CRNN 裁剪数据生成；
3. 完成 YOLO 训练脚本；
4. 完成 CRNN 模型与训练脚本；
5. 完成统一推理流水线；
6. 完成 Django + Vue 最小可运行系统；
7. 补充实验记录和论文资料。
