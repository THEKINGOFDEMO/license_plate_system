# YOLO 训练说明

## 文档目的

本说明只覆盖 `Task 02`：YOLO 车牌检测模型训练准备。

当前阶段只做以下内容：

- AutoDL 环境说明；
- 数据集与配置文件路径说明；
- YOLO 依赖安装；
- YOLO 可用性检查；
- `1 epoch` smoke test；
- 正式训练命令；
- 验证命令；
- 预测命令；
- 训练结果文件说明；
- 论文需要保留的训练结果文件清单。

明确约束：

- 现在**不要做 CRNN**
- 现在**不要做 Django/Vue**
- 现在**不要做系统开发**
- 现在**不要写论文正文内容**

## AutoDL 环境说明

当前 AutoDL 上的关键路径如下：

- 项目路径：
  - `/cloud/cloud-ssd1/projects/license_plate_system`
- YOLO 数据配置文件：
  - `/cloud/cloud-ssd1/lpr_data/ccpd_10000/configs/ccpd_yolo.yaml`
- 训练输出目录：
  - `/cloud/cloud-ssd1/runs/yolo`
- 模型权重目录：
  - `/cloud/cloud-ssd1/models`

重要说明：

- `/cloud` 空间较小，不要把训练输出、模型权重、数据集放到 `/cloud`
- 所有训练相关文件统一放到 `/cloud/cloud-ssd1`

## 数据集路径说明

当前已确认的数据准备状态：

- 使用 `CCPD2019/ccpd_base` 构建了 `10000` 张子集
- 划分结果：
  - `train=8000`
  - `val=1000`
  - `test=1000`
- YOLO 标签已生成 `10000` 个
- CRNN 裁剪图已生成 `10000` 张
- `preview` 检查正常，bbox 能正确框住车牌

本阶段 YOLO 训练只依赖以下数据配置文件：

```text
/cloud/cloud-ssd1/lpr_data/ccpd_10000/configs/ccpd_yolo.yaml
```

建议训练前先确认该文件存在：

```bash
ls -l /cloud/cloud-ssd1/lpr_data/ccpd_10000/configs/ccpd_yolo.yaml
```

## 安装依赖命令

进入项目目录：

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
```

安装当前阶段依赖：

```bash
pip install -r requirements.txt
```

## 检查 YOLO 是否可用

先检查 `yolo` 命令是否可用：

```bash
yolo checks
```

如果你只想确认 Ultralytics 能否被 Python 导入，也可以执行：

```bash
python -c "from ultralytics import YOLO; print('Ultralytics OK')"
```

## 1 epoch smoke test 命令

先创建输出目录：

```bash
mkdir -p /cloud/cloud-ssd1/runs/yolo
mkdir -p /cloud/cloud-ssd1/models
```

`1 epoch` smoke test 命令如下：

```bash
yolo detect train \
  model=yolov8n.pt \
  data=/cloud/cloud-ssd1/lpr_data/ccpd_10000/configs/ccpd_yolo.yaml \
  epochs=1 \
  imgsz=640 \
  batch=16 \
  device=0 \
  workers=4 \
  project=/cloud/cloud-ssd1/runs/yolo \
  name=ccpd10000_yolov8n_smoke
```

## 正式训练命令

当 smoke test 正常后，再执行正式训练：

```bash
yolo detect train \
  model=yolov8n.pt \
  data=/cloud/cloud-ssd1/lpr_data/ccpd_10000/configs/ccpd_yolo.yaml \
  epochs=50 \
  imgsz=640 \
  batch=16 \
  device=0 \
  workers=4 \
  project=/cloud/cloud-ssd1/runs/yolo \
  name=ccpd10000_yolov8n_e50
```

## 验证命令

训练完成后，使用 `best.pt` 做验证：

```bash
yolo detect val \
  model=/cloud/cloud-ssd1/runs/yolo/ccpd10000_yolov8n_e50/weights/best.pt \
  data=/cloud/cloud-ssd1/lpr_data/ccpd_10000/configs/ccpd_yolo.yaml \
  imgsz=640 \
  batch=16 \
  device=0 \
  project=/cloud/cloud-ssd1/runs/yolo \
  name=ccpd10000_yolov8n_val
```

## 预测命令

对测试集图片做预测：

```bash
yolo detect predict \
  model=/cloud/cloud-ssd1/runs/yolo/ccpd10000_yolov8n_e50/weights/best.pt \
  source=/cloud/cloud-ssd1/lpr_data/ccpd_10000/images/test \
  imgsz=640 \
  conf=0.25 \
  device=0 \
  project=/cloud/cloud-ssd1/runs/yolo \
  name=ccpd10000_yolov8n_predict
```

## 训练结果文件说明

正式训练完成后，重点会在下面的训练目录中看到结果：

```text
/cloud/cloud-ssd1/runs/yolo/ccpd10000_yolov8n_e50/
```

通常需要重点关注：

- `weights/best.pt`
- `weights/last.pt`
- `results.png`
- `results.csv`
- `PR_curve.png`
- `P_curve.png`
- `R_curve.png`
- `F1_curve.png`
- `confusion_matrix.png`
- `val_batch0_labels.jpg`
- `val_batch0_pred.jpg`
- `val_batch1_labels.jpg`
- `val_batch1_pred.jpg`
- `val_batch2_labels.jpg`
- `val_batch2_pred.jpg`

验证与预测阶段的输出一般会出现在：

- `/cloud/cloud-ssd1/runs/yolo/ccpd10000_yolov8n_val/`
- `/cloud/cloud-ssd1/runs/yolo/ccpd10000_yolov8n_predict/`

## 论文需要保存哪些训练结果图和权重文件

论文与答辩阶段，建议至少保留下列真实产物：

- `best.pt`
- `last.pt`
- `results.png`
- `PR_curve.png`
- `confusion_matrix.png`
- 至少一组 `val_batch*_pred.jpg`
- 至少一组预测结果图
- 训练日志或 `results.csv`

建议论文中重点对应这些证据：

- 检测指标：
  - Precision
  - Recall
  - mAP@0.5
  - mAP@0.5:0.95
- 训练过程曲线图
- 验证批次可视化结果
- 测试集预测示例图

## 推荐执行顺序

建议在 AutoDL 上按下面顺序执行：

1. 安装依赖
2. 执行 `yolo checks`
3. 执行 `1 epoch` smoke test
4. 确认 smoke test 输出目录和结果图正常
5. 执行 `50 epoch` 正式训练
6. 使用 `best.pt` 运行验证
7. 使用 `best.pt` 对测试集做预测

## 当前结论

当前 `Task 02` 的目标是把 YOLO 训练准备、命令、脚本和结果保留要求整理完整。

这一步**不包含**：

- CRNN 训练
- Django/Vue 开发
- 系统联调
- 论文正文撰写
