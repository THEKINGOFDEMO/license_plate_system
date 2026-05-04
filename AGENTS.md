# AGENTS.md

## 项目身份

本仓库用于一个中文本科毕业设计项目：

- 论文题目：基于深度学习的车牌检测与识别系统设计与实现
- 固定技术路线：CCPD 数据集 -> YOLO 车牌检测 -> CRNN 车牌字符识别 -> Django 后端 -> Vue 前端
- 系统目标：支持图片上传、车牌定位、车牌裁剪、字符识别、结果可视化展示，并尽量支持识别历史记录。

## 必须遵守的范围

1. 不要把主线替换成 PaddleOCR、HyperLPR、EasyOCR 或第三方 OCR API。
2. 除非用户明确要求临时做 baseline，否则论文和系统必须保持 YOLO + CRNN。
3. 不要伪造训练指标、实验结果、数据集规模、截图或模型效果。
4. 缺少真实指标时，用 TODO 标记，并提供生成指标的脚本或命令。
5. 默认不要直接训练完整 CCPD 全量数据集，应先支持子集采样训练，再通过配置支持扩展到更多数据。
6. AutoDL 租 NVIDIA GPU 是正式训练方案，不需要围绕本地 AMD 显卡改技术路线。

## 推荐仓库结构

除非用户已有明确结构，否则优先按下面结构组织项目：

```text
license_plate_system/
├── backend/                 # Django 后端
├── frontend/                # Vue 前端
├── datasets/                # 本地数据集工作区，通常加入 .gitignore
├── models/                  # 模型定义、推理封装
├── train/                   # 数据转换、训练、评估脚本
├── configs/                 # yaml/json 配置文件
├── weights/                 # 训练权重，通常加入 .gitignore
├── docs/                    # 论文相关资料、实验记录、截图清单
├── tests/                   # 最小测试
├── PROJECT_BRIEF.md
├── TASKS.md
└── README.md
```

## 核心交付物

### 1. 数据预处理

需要完成：

- 解析 CCPD 图片文件名中的标注信息；
- 生成 YOLO 检测标签；
- 根据车牌框裁剪车牌图片，生成 CRNN 识别标签；
- 按固定随机种子划分 train/val/test；
- 输出清晰的数据目录结构和转换日志。

### 2. YOLO 车牌检测

要求：

- 默认使用 Ultralytics YOLOv8n 或 YOLOv8s，除非用户另有指定；
- 提供 train、val、predict 命令；
- 保留训练产物：best.pt、results.png、PR_curve.png、confusion_matrix.png、val_batch_pred.jpg、检测示例图；
- 指标包括 Precision、Recall、mAP@0.5、mAP@0.5:0.95。

### 3. CRNN 字符识别

要求：

- 使用 PyTorch 实现或集成 CRNN；
- 使用 CTC Loss，避免手动字符分割；
- 支持 CCPD 中常见的中文省份简称、英文字符和数字；
- 提供训练、验证、预测和评估脚本；
- 指标包括字符准确率和整牌准确率；
- 支持保存 checkpoint 和断点恢复。

### 4. 统一推理流水线

流程：

```text
输入图片 -> YOLO 检测车牌 -> 裁剪车牌区域 -> CRNN 识别字符 -> 返回 JSON -> 保存可视化图片
```

输出 JSON 至少包含：

- bbox；
- plate_text；
- confidence，如果可用；
- crop_path；
- annotated_image_path；
- error message，如果检测或识别失败。

### 5. Web 系统

要求：

- Django 后端提供图片上传、模型推理、历史记录接口；
- Vue 前端提供图片上传、预览、识别按钮、标注结果展示、车牌号展示和历史记录表；
- UI 以稳定、清晰、容易答辩演示为第一优先级，不追求复杂炫酷效果；
- 默认使用 SQLite，降低部署复杂度。

### 6. 文档

至少包含：

- README：安装、训练、运行、常见问题；
- docs/experiment_plan.md：训练与评估计划；
- docs/thesis_notes.md：论文写作素材；
- docs/screenshot_checklist.md：答辩和论文截图清单。

## 开发规则

- Python 建议使用 3.9 或 3.10。
- CRNN 使用 PyTorch。
- 图像处理使用 OpenCV 或 Pillow。
- 数据处理、训练、评估脚本使用 argparse 命令行参数。
- 路径、模型、训练参数尽量放入配置文件，不要硬编码。
- datasets、weights、runs、media、node_modules、__pycache__ 不应提交到 Git。
- 每个脚本都应输出清楚的进度信息和错误信息。
- 采样和数据划分尽量使用固定随机种子，保证可复现。
- 优先写小函数和可测试模块，不要把所有逻辑堆到一个大脚本中。
- 不要无关重构，优先完成毕业设计可交付闭环。

## Codex 工作流程

每次修改代码前：

1. 阅读 AGENTS.md、PROJECT_BRIEF.md、TASKS.md 和当前任务相关文件；
2. 用 3-6 条总结本次任务；
3. 说明计划新增或修改哪些文件；
4. 然后再开始实现。

每次修改代码后：

1. 运行最小相关测试、语法检查或 smoke test；
2. 准确说明修改了哪些文件；
3. 给出用户下一步在本地或 AutoDL 上要运行的命令；
4. 诚实列出未完成 TODO；
5. 不要声称已经完成未实际运行的训练或评估。

## 诚实原则

- 没有实际训练，就不能说模型已经训练成功。
- 没有真实日志，就不能写具体准确率、mAP 或耗时。
- 如果缺少数据集或权重，只能创建配置、占位说明和运行指令，不能伪造文件。
- 如果需要 GPU 训练，应提供 AutoDL 可执行命令和环境说明。
- 论文相关材料可以整理结构和模板，但真实实验结果必须来自真实训练或评估输出。
