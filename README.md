# 基于深度学习的车牌检测与识别系统

## 项目简介

本项目用于本科毕业设计《基于深度学习的车牌检测与识别系统设计与实现》。

固定技术路线如下：

```text
CCPD 数据集
  -> 数据预处理与标注解析
  -> YOLO 车牌检测
  -> CRNN 车牌字符识别
  -> Django 后端集成推理
  -> Vue 前端展示结果
```

项目目标不是单独完成某一部分代码，而是形成一个可训练、可推理、可演示、可写入论文的完整闭环系统。

## 当前阶段

当前已完成：

- `Task 00 - 仓库初始化`
- `Task 01 - CCPD 文件名解析与数据集转换`
- `Task 01.5 - 真实数据转换验证辅助功能`

尚未实现：

- YOLO 训练脚本；
- CRNN 模型与训练；
- 统一推理流水线；
- Django 后端接口；
- Vue 前端页面。

## 推荐环境

- Python 3.9 或 3.10
- PyTorch
- OpenCV 或 Pillow
- Django
- Vue

说明：

- 正式模型训练环境为 AutoDL + NVIDIA GPU；
- 本地环境主要用于代码开发、联调、推理演示和论文截图；
- 当前仓库初始化阶段还没有锁定全部依赖版本。

## 虚拟环境

当前项目建议先进入你自己的虚拟环境，再运行测试或数据转换脚本。

如果你使用的是这个虚拟环境：

`D:\venv_home\plate_recognition\.venv\Scripts`

PowerShell 激活命令可以写成：

```powershell
& D:\venv_home\plate_recognition\.venv\Scripts\Activate.ps1
```

如果你平时习惯直接粘贴完整路径执行，也可以继续按你的习惯来。

激活后，建议先确认当前 `python` 是否来自虚拟环境：

```powershell
python -c "import sys; print(sys.executable)"
```

输出路径如果指向你的 `.venv`，就说明当前解释器已经切换正确。

当前数据预处理阶段最少依赖可以先安装：

```powershell
pip install -r requirements.txt
```

## 本地验证命令

建议在本地先只做环境确认、单元测试和小样本脚本检查。

确认当前 `python` 是否来自虚拟环境：

```powershell
python -c "import sys; print(sys.executable)"
```

确认当前环境里的 Pillow 可用：

```powershell
python -c "from PIL import Image; print('Pillow OK')"
```

运行当前已实现的最小测试：

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

## 目录结构

```text
license_plate_system/
├── backend/                 # Django 后端
├── frontend/                # Vue 前端
├── train/                   # 数据转换、训练、评估脚本
├── models/                  # 模型定义、推理封装
├── configs/                 # 配置文件
├── docs/                    # 实验计划、论文素材、截图清单等
├── tests/                   # 最小测试
├── AGENTS.md
├── PROJECT_BRIEF.md
├── TASKS.md
├── README.md
└── .gitignore
```

说明：

- `datasets/`、`weights/`、`runs/`、`media/` 属于本地数据或运行产物，默认不提交到 Git；
- 后续如果需要保留空目录，可继续使用 `.gitkeep`。

## 计划中的运行顺序

建议按如下顺序推进：

1. 完成 CCPD 解析与数据集转换。
2. 完成 YOLO 检测训练流程。
3. 完成 CRNN 识别训练流程。
4. 完成统一图片推理流水线。
5. 完成 Django 后端上传与识别接口。
6. 完成 Vue 前端上传、预览、结果展示与历史记录页面。
7. 补充测试、实验记录、论文材料和截图清单。

## CCPD2019 数据准备

### 下载建议

CCPD 数据集的原始说明可参考官方仓库：

- [CCPD GitHub](https://github.com/detectRecog/CCPD)

本项目当前优先建议先准备 `CCPD2019` 蓝牌数据的一个子目录做验证，再逐步扩展。

这里要特别说明：

- 本地不需要下载完整 `CCPD2019`
- 本地只建议做小样本验证、单元测试和脚本联调
- 真实的大规模数据转换与后续训练，统一放到 `AutoDL + NVIDIA GPU` 环境执行

由于不同下载来源的压缩包目录名可能略有不同，当前仓库只要求：

- `--src` 指向“实际存放 CCPD 图片文件”的目录；
- 目录下图片文件名保留 CCPD 原始命名格式；
- 不要求先放到固定死的仓库路径，但推荐统一放在 `datasets/` 下。

### 推荐本地目录结构

```text
license_plate_system/
├── datasets/
│   └── CCPD2019/
│       └── ccpd_base/
│           ├── 025-95_113-154&383_386&473-...jpg
│           ├── 031-88_102-...
│           └── ...
```

如果你后续还要区分不同子集，也可以继续扩展，例如：

```text
datasets/
└── CCPD2019/
    ├── ccpd_base/
    ├── ccpd_blur/
    ├── ccpd_challenge/
    └── ccpd_tilt/
```

## CCPD 转换命令

### 1. 先做 dry-run 解析检查

这一步只解析文件名并打印前 5 条结果，不复制图片、不生成标签、不裁剪车牌：

```powershell
python train\prepare_ccpd.py --src datasets\CCPD2019\ccpd_base --out . --limit 100 --dry-run
```

适合先确认：

- 文件名是不是标准 CCPD 格式；
- 车牌文本解码是否正常；
- 是否有被跳过的异常文件；
- 100 张样本里大概有多少有效图片。

### 2. 生成 bbox 预览图

这一步会随机保存若干张带车牌框的可视化图片到 `outputs/preview/`：

```powershell
python train\prepare_ccpd.py --src datasets\CCPD2019\ccpd_base --out . --limit 100 --preview 10
```

建议人工检查：

- 红色 bbox 是否框住整块车牌；
- 黄色四点多边形是否落在车牌区域附近；
- 极端倾斜样本是否存在明显框偏移。

### 3. 生成 YOLO 和 CRNN 数据

```powershell
python train\prepare_ccpd.py --src datasets\CCPD2019\ccpd_base --out . --limit 100 --seed 42 --make-yolo --make-crnn
```

运行后将生成：

- `images/train`、`images/val`、`images/test`
- `labels/train`、`labels/val`、`labels/test`
- `configs/ccpd_yolo.yaml`
- `crnn/images/train`、`crnn/images/val`、`crnn/images/test`
- `crnn/train.txt`、`crnn/val.txt`、`crnn/test.txt`

### 4. 同时做转换和预览

```powershell
python train\prepare_ccpd.py --src datasets\CCPD2019\ccpd_base --out . --limit 100 --seed 42 --make-yolo --make-crnn --preview 10
```

## 用 100 张 CCPD 图片做真实转换验证

推荐按下面顺序做一次最小真数据检查：

1. 先执行 dry-run：
   `python train\prepare_ccpd.py --src datasets\CCPD2019\ccpd_base --out . --limit 100 --dry-run`
2. 看终端统计信息，确认 `valid_samples`、`skipped_files` 是否合理。
3. 再执行预览：
   `python train\prepare_ccpd.py --src datasets\CCPD2019\ccpd_base --out . --limit 100 --preview 10`
4. 打开 `outputs/preview/`，人工检查 10 张预览图的 bbox 是否基本正确。
5. 最后执行真实转换：
   `python train\prepare_ccpd.py --src datasets\CCPD2019\ccpd_base --out . --limit 100 --seed 42 --make-yolo --make-crnn`
6. 核对终端统计：
   `train/val/test` 数量、`yolo_labels_written`、`crnn_crops_written`、`skipped_files`
7. 随机打开几张：
   - `images/train/*.jpg`
   - `labels/train/*.txt`
   - `crnn/images/train/*.jpg`
   - `crnn/train.txt`

如果这 100 张样本检查通过，再逐步把 `--limit` 提高到更大的子集。

## 后续任务入口

- `Task 01`：实现 CCPD 文件名解析、YOLO 标签转换、CRNN 裁剪数据生成。
- `Task 02`：补齐 AutoDL 可运行的 YOLO 训练、验证、预测脚本。
- `Task 03`：实现 PyTorch CRNN 与评估脚本。
- `Task 04`：打通检测 + 识别统一推理流水线。
- `Task 05`：实现 Django 后端 API。
- `Task 06`：实现 Vue 前端演示界面。
- `Task 07`：补齐集成说明、测试和常见问题。
- `Task 08`：整理系统设计、算法设计与论文辅助材料。

## 说明

本仓库遵循以下原则：

- 不替换主线技术路线为第三方 OCR 方案；
- 不编造训练指标、实验结果或截图；
- 缺少真实实验输出时，使用 `TODO` 标记并补充真实运行方法；
- 优先完成毕业设计可交付闭环，再做扩展优化。
