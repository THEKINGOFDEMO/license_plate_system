# TASKS.md

这个文件是给 Codex 使用的任务板。每次只让 Codex 做一个任务，不要一次性要求完成全部项目。

---

## Task 00 - 仓库初始化

目标：创建清晰、稳定的项目骨架。

验收标准：

- 创建 README.md，说明项目目标、目录结构和运行顺序；
- 创建 .gitignore，排除 datasets、weights、runs、media、node_modules、__pycache__ 等；
- 创建目录：backend、frontend、train、models、configs、docs、tests；
- 创建 docs/experiment_plan.md 和 docs/thesis_notes.md 占位文件；
- 不实现模型训练，不引入复杂依赖。

建议给 Codex 的提示词：

```text
请阅读 AGENTS.md、PROJECT_BRIEF.md、TASKS.md，然后只完成 Task 00。创建项目骨架、README、.gitignore 和 docs 占位文件。不要实现模型训练。完成后说明修改了哪些文件、如何验证、下一步该做什么。
```

---

## Task 01 - CCPD 解析与数据集转换

目标：解析 CCPD 图片文件名，为 YOLO 和 CRNN 生成训练数据。

验收标准：

- 新增 train/ccpd_utils.py，实现 CCPD 文件名解析；
- 新增 train/prepare_ccpd.py，支持命令行参数：
  - --src
  - --out
  - --limit
  - --seed
  - --train-ratio
  - --val-ratio
  - --test-ratio
  - --make-yolo
  - --make-crnn
- 生成 YOLO 格式：
  - images/train、images/val、images/test
  - labels/train、labels/val、labels/test
  - configs/ccpd_yolo.yaml
- 生成 CRNN 格式：
  - crnn/images/train、crnn/images/val、crnn/images/test
  - crnn/train.txt、crnn/val.txt、crnn/test.txt
- 添加一个基于示例 CCPD 文件名的解析单元测试；
- 如果数据集路径不存在，应给出清晰报错，不要崩溃或伪造数据。

建议提示词：

```text
请只完成 Task 01。实现 CCPD 文件名解析、YOLO 标签转换、CRNN 车牌裁剪数据生成和一个最小测试。不要假设数据集已经存在，路径错误时要给出清晰提示。
```

---

## Task 02 - YOLO 训练流程

目标：让车牌检测模型训练流程可以直接在 AutoDL 上运行。

验收标准：

- 新增 train/train_yolo.py 或 scripts/train_yolo.sh；
- 默认使用 YOLOv8n，也可以通过参数改为 YOLOv8s；
- 从 configs/ccpd_yolo.yaml 读取数据配置；
- 提供 train、val、predict 的命令；
- README 和 docs/experiment_plan.md 记录预期输出路径；
- 不在本地运行完整训练。

建议提示词：

```text
请只完成 Task 02。添加 AutoDL 可用的 YOLO 训练、验证、预测流程，默认使用 YOLOv8n。不要在本地跑完整训练，只提供脚本、命令和说明。
```

---

## Task 03 - CRNN 模型与训练

目标：实现 PyTorch CRNN + CTC 车牌字符识别。

验收标准：

- 新增 models/crnn.py；
- 新增 train/crnn_dataset.py；
- 新增 train/train_crnn.py；
- 新增 train/eval_crnn.py；
- 新增 models/charset.py，定义 CCPD 字符集；
- 支持 checkpoint 保存和断点恢复；
- 评估输出字符准确率和整牌准确率；
- 提供 CPU smoke test 或 tiny fake dataset，用于快速检查模型、dataloader 和损失函数逻辑。

建议提示词：

```text
请只完成 Task 03。用 PyTorch 实现 CRNN 识别训练与评估，使用 CTC Loss。加入 tiny smoke test，保证没有完整 CCPD 数据时也能检查语法和数据流。
```

---

## Task 04 - 统一推理流水线

目标：把 YOLO 检测器和 CRNN 识别器串起来。

验收标准：

- 新增 models/detector.py；
- 新增 models/recognizer.py；
- 新增 models/pipeline.py；
- 新增 scripts/predict_image.py；
- 输入包括图片路径、YOLO 权重、CRNN checkpoint；
- 输出 JSON，包含 bbox、plate_text、confidence、crop_path、annotated_image_path；
- 保存标注后的结果图，便于论文和答辩截图；
- 如果权重不存在，应清晰提示，而不是报一堆底层错误。

建议提示词：

```text
请只完成 Task 04。构建图片推理流水线，能加载 YOLO 和 CRNN 权重完成检测识别；如果权重缺失，要给出清晰错误信息，不要伪造结果。
```

---

## Task 05 - Django 后端

目标：创建后端 API，支持上传图片和调用推理流水线。

验收标准：

- 在 backend 下创建 Django 项目；
- 创建 recognition app；
- 提供接口：
  - POST /api/recognize/：上传图片并返回识别结果；
  - GET /api/records/：返回历史识别记录；
- 上传图片、裁剪图、标注图保存到 media；
- 默认使用 SQLite 保存记录；
- 支持 CORS，便于 Vue 调用；
- 提供清晰的安装和运行说明。

建议提示词：

```text
请只完成 Task 05。构建 Django 后端 API，封装已有推理流水线，实现图片上传识别和历史记录查询。保持简单稳定，适合毕业设计演示。
```

---

## Task 06 - Vue 前端

目标：创建用户可操作的演示界面。

验收标准：

- 在 frontend 下创建 Vue 项目；
- 页面包含图片上传、图片预览、识别按钮、识别结果文本、标注图片展示和历史记录表；
- 使用简单 API 封装调用 Django 接口；
- UI 简洁、稳定、容易截图；
- 提供运行说明。

建议提示词：

```text
请只完成 Task 06。构建 Vue 前端，实现图片上传、预览、调用后端识别、展示标注图和车牌结果、查看历史记录。界面保持清晰稳定，不要过度设计。
```

---

## Task 07 - 集成与测试

目标：让整个项目容易运行、调试和答辩演示。

验收标准：

- 添加端到端运行指南；
- 添加解析器测试和推理流水线失败场景测试；
- 添加示例配置文件；
- 添加 AutoDL 训练和本地部署常见问题；
- 确保 README 中能看出从数据准备到系统演示的完整路径。

建议提示词：

```text
请只完成 Task 07。补充集成说明、最小测试、示例配置和常见问题，重点是让系统容易运行和调试。
```

---

## Task 08 - 论文辅助材料

目标：基于项目代码和真实日志整理论文素材。

验收标准：

- 新增 docs/system_design.md；
- 新增 docs/algorithm_design.md；
- 更新 docs/experiment_plan.md；
- 新增 docs/midterm_check_draft.md；
- 新增 docs/thesis_outline.md；
- 新增 docs/screenshot_checklist.md；
- 不编造实验结果，缺失真实结果的地方用 TODO 标记。

建议提示词：

```text
请只完成 Task 08。根据当前已实现系统和固定 YOLO+CRNN+Django+Vue 路线，整理论文辅助 Markdown。不要编造实验结果，缺失真实日志或截图的地方用 TODO 标记。
```
