# AutoDL 运行说明

## 文档目的

本说明用于指导在 AutoDL 环境中完成当前阶段的数据准备与验证工作，包括：

- 安装基础工具；
- clone 当前 GitHub 仓库；
- 安装 `requirements.txt`；
- 运行单元测试；
- 下载并解压 `CCPD2019`；
- 用 `100` 张图片执行 `dry-run`、`preview`、`--make-yolo --make-crnn`；
- 确认真实数据转换结果无误。

当前文档只覆盖 `Task 01 / Task 01.5`。

明确约束：

- 现在**不要进入 Task 02**
- 现在**不要写 YOLO/CRNN 训练代码**
- 只有真实数据转换验证通过后，才能进入 `Task 02`

## AutoDL 推荐目录结构

在当前 AutoDL 环境中，推荐统一使用如下目录：

```text
/cloud/
├── projects/
│   └── license_plate_system
└── cloud-ssd1/
    ├── datasets
    │   └── CCPD2019
    └── lpr_data
```

对应职责如下：

- `/cloud/projects/license_plate_system`
  - 当前 GitHub 项目代码
- `/cloud/cloud-ssd1/datasets`
  - 原始数据集存放目录
- `/cloud/cloud-ssd1/lpr_data`
  - `prepare_ccpd.py` 转换后的输出目录

## 1. 安装 git、clone 仓库、安装 requirements.txt、运行单元测试

### 1.1 安装 git

如果 AutoDL 镜像里还没有 `git`，先执行：

```bash
apt-get update
apt-get install -y git
```

### 1.2 创建项目目录并 clone 仓库

```bash
mkdir -p /cloud/projects
cd /cloud/projects
git clone <你的GitHub仓库地址> license_plate_system
cd /cloud/projects/license_plate_system
```

如果仓库已经 clone 过，可以执行：

```bash
cd /cloud/projects/license_plate_system
git pull
```

### 1.3 安装 requirements.txt

```bash
cd /cloud/projects/license_plate_system
pip install -r requirements.txt
```

### 1.4 运行单元测试

```bash
cd /cloud/projects/license_plate_system
python -m unittest discover -s tests -p "test_*.py" -v
```

如果测试通过，说明当前 `Task 01 / Task 01.5` 代码基础状态正常。

## 2. 创建数据目录

```bash
mkdir -p /cloud/cloud-ssd1/datasets
mkdir -p /cloud/cloud-ssd1/lpr_data
```

建议后续把 CCPD2019 放在：

```text
/cloud/cloud-ssd1/datasets/CCPD2019
```

## 3. 下载 CCPD2019 到 /cloud/cloud-ssd1/datasets 的命令

由于数据源可能不同，这里给出通用命令模板。

先进入数据目录：

```bash
mkdir -p /cloud/cloud-ssd1/datasets/CCPD2019
cd /cloud/cloud-ssd1/datasets/CCPD2019
```

如果你已经拿到直接下载链接，可以使用：

```bash
wget -O ccpd_base.zip "<CCPD2019下载链接>"
```

如果目标资源需要断点续传，可以使用：

```bash
wget -c -O ccpd_base.zip "<CCPD2019下载链接>"
```

如果你是从浏览器或平台面板上传文件，也建议最终把压缩包放到：

```text
/cloud/cloud-ssd1/datasets/CCPD2019/ccpd_base.zip
```

## 4. 解压 CCPD2019 的命令

如果是 `zip`：

```bash
cd /cloud/cloud-ssd1/datasets/CCPD2019
unzip ccpd_base.zip
```

如果是 `tar`：

```bash
cd /cloud/cloud-ssd1/datasets/CCPD2019
tar -xf ccpd_base.tar
```

如果是 `tar.gz`：

```bash
cd /cloud/cloud-ssd1/datasets/CCPD2019
tar -xzf ccpd_base.tar.gz
```

最终请确保原始图片目录类似这样：

```text
/cloud/cloud-ssd1/datasets/CCPD2019/ccpd_base/
├── 025-95_113-154&383_386&473-...jpg
├── 031-88_102-...jpg
└── ...
```

## 5. 使用 100 张图片进行 dry-run

先进入项目目录：

```bash
cd /cloud/projects/license_plate_system
```

执行 `dry-run`：

```bash
python train/prepare_ccpd.py \
  --src /cloud/cloud-ssd1/datasets/CCPD2019/ccpd_base \
  --out /cloud/cloud-ssd1/lpr_data \
  --limit 100 \
  --dry-run
```

这一步只会：

- 解析文件名；
- 打印前 `5` 条解析结果；
- 输出统计信息；
- 检查是否有无效文件名被跳过。

建议重点看：

- `valid_samples`
- `skipped_files`
- 前几条样本的 `plate` 和 `bbox`

## 6. 使用 100 张图片进行 preview

在 `dry-run` 正常后，执行：

```bash
cd /cloud/projects/license_plate_system
python train/prepare_ccpd.py \
  --src /cloud/cloud-ssd1/datasets/CCPD2019/ccpd_base \
  --out /cloud/cloud-ssd1/lpr_data \
  --limit 100 \
  --preview 10
```

预览图会输出到：

```text
/cloud/cloud-ssd1/lpr_data/outputs/preview/
```

你需要人工检查：

- 红色 bbox 是否基本框住整块车牌；
- 黄色四点多边形是否落在车牌附近；
- 是否存在明显错框、偏框、漏框问题。

## 7. 使用 100 张图片执行 --make-yolo --make-crnn

确认 `preview` 没问题之后，再执行真实转换：

```bash
cd /cloud/projects/license_plate_system
python train/prepare_ccpd.py \
  --src /cloud/cloud-ssd1/datasets/CCPD2019/ccpd_base \
  --out /cloud/cloud-ssd1/lpr_data \
  --limit 100 \
  --seed 42 \
  --make-yolo \
  --make-crnn
```

如果你希望转换时顺便继续保存预览图，也可以执行：

```bash
cd /cloud/projects/license_plate_system
python train/prepare_ccpd.py \
  --src /cloud/cloud-ssd1/datasets/CCPD2019/ccpd_base \
  --out /cloud/cloud-ssd1/lpr_data \
  --limit 100 \
  --seed 42 \
  --make-yolo \
  --make-crnn \
  --preview 10
```

生成结果会写到：

```text
/cloud/cloud-ssd1/lpr_data/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
├── labels/
│   ├── train/
│   ├── val/
│   └── test/
├── crnn/
│   ├── images/
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   ├── train.txt
│   ├── val.txt
│   └── test.txt
├── configs/
│   └── ccpd_yolo.yaml
└── outputs/
    └── preview/
```

## 8. 真实数据转换后的检查项

完成真实转换后，至少检查以下内容：

1. 终端统计信息：
   - `train/val/test`
   - `yolo_labels_written`
   - `crnn_crops_written`
   - `skipped_files`
2. 随机抽查 YOLO 输出：
   - `/cloud/cloud-ssd1/lpr_data/images/train`
   - `/cloud/cloud-ssd1/lpr_data/labels/train`
3. 随机抽查 CRNN 输出：
   - `/cloud/cloud-ssd1/lpr_data/crnn/images/train`
   - `/cloud/cloud-ssd1/lpr_data/crnn/train.txt`
4. 再次检查预览图：
   - `/cloud/cloud-ssd1/lpr_data/outputs/preview/`

## 9. 何时才能进入 Task 02

必须同时满足以下条件，才能进入 `Task 02`：

1. `python -m unittest discover -s tests -p "test_*.py" -v` 通过；
2. `dry-run` 输出正常；
3. `preview` 人工确认 bbox 基本正确；
4. `--make-yolo --make-crnn` 真实转换成功；
5. 抽查后的 YOLO 标签、CRNN 裁剪图、清单文件都没有明显错误。

在这之前：

- **不要进入 Task 02**
- **不要写训练脚本**
- **不要开始 YOLO/CRNN 训练**

## 当前阶段结论

当前阶段在 AutoDL 上的核心目标不是训练，而是先把真实数据转换流程跑通、看对、验明白。

只有真实数据转换验证通过后，下一步才是进入 `Task 02`。
