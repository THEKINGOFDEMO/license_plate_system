# 中文 Codex 项目任务包使用说明

## 会不会影响中文使用？

不会。这个任务包已经改成中文内容，文件名保留英文是为了兼容开发习惯和 Codex 项目指令机制。

尤其要注意：

- `AGENTS.md` 这个文件名不要改；
- `PROJECT_BRIEF.md`、`TASKS.md` 等文件名也建议保留；
- 文件内容可以是中文；
- 技术关键词保留英文更好，例如 YOLO、CRNN、Django、Vue、AutoDL、PyTorch、CCPD。

## 使用步骤

1. 创建一个新的毕业设计项目仓库，例如：

```text
license_plate_system/
```

2. 把本任务包中的文件复制到仓库根目录：

```text
AGENTS.md
PROJECT_BRIEF.md
TASKS.md
CODEX_PROMPTS.md
DATA_AND_TRAINING.md
DOCS_TODO.md
README_FOR_USER.md
```

3. 用 Codex 打开这个仓库。

4. 第一句发给 Codex：

```text
请先阅读 AGENTS.md、PROJECT_BRIEF.md、TASKS.md。只总结你理解到的项目目标、技术路线、目录结构和当前任务拆分，不要修改代码。
```

5. 它总结正确后，再发：

```text
请阅读 AGENTS.md、PROJECT_BRIEF.md、TASKS.md，然后只完成 Task 00。完成后说明修改了哪些文件、如何验证、下一步该做什么。
```

6. 后续按 Task 01、Task 02、Task 03 的顺序推进。

## 重要原则

不要一次性让 Codex 完成全部项目。正确做法是：

```text
一次只派一个任务
每次完成后检查文件
能运行就提交或备份
报错就把命令和报错原样发回 Codex
```

## 你和 Codex 的分工

Codex 适合负责：

- 项目目录；
- 数据预处理脚本；
- YOLO 训练脚本；
- CRNN 模型代码；
- Django 后端；
- Vue 前端；
- README；
- 实验结果整理脚本。

你需要负责：

- 下载和放置 CCPD 数据集；
- 在 AutoDL 上运行训练命令；
- 保存真实训练日志和结果图；
- 下载 best.pt、crnn_best.pth；
- 本地运行系统并截图；
- 把真实指标用于论文。

## 论文相关

文献综述、外文翻译、中期检查、论文初稿、答辩 PPT 可以先让 Codex 整理 Markdown 结构，但最终论文文本建议再单独润色。真实实验结果必须来自训练日志，不能让 Codex 编造。
