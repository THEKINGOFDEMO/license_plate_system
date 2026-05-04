# DATA_AND_TRAINING.md

## 数据集

主数据集使用 CCPD。该项目需要从 CCPD 图片文件名中解析标注信息。

## CCPD 文件名字段

常见 CCPD 文件名由 7 个字段组成，用短横线分隔：

```text
area-tilt-bbox-four_points-license-brightness-blur.jpg
```

示例：

```text
025-95_113-154&383_386&473-386&473_177&454_154&383_363&402-0_0_22_27_27_33_16-37-15.jpg
```

重点解析字段：

- bbox：例如 `154&383_386&473`，表示车牌左上角和右下角坐标；
- four_points：车牌四个顶点坐标；
- license：例如 `0_0_22_27_27_33_16`，表示省份、字母、后五位字符的索引；
- brightness 和 blur 可作为复杂场景分析的参考字段。

## 字符集

除非实际数据集版本需要调整，否则优先使用下面 CCPD 常见字符集：

```python
PROVINCES = ["皖", "沪", "津", "渝", "冀", "晋", "蒙", "辽", "吉", "黑", "苏", "浙", "京", "闽", "赣", "鲁", "豫", "鄂", "湘", "粤", "桂", "琼", "川", "贵", "云", "藏", "陕", "甘", "青", "宁", "新", "警", "学", "O"]
ALPHABETS = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "O"]
ADS = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "O"]
```

## YOLO 标签格式

一张图片中默认一个车牌时，标签格式为：

```text
0 x_center y_center width height
```

所有坐标都需要除以图片宽高进行归一化。

## CRNN 数据格式

推荐标签文件格式：

```text
relative/path/to/crop.jpg\t湘A12345
```

即：车牌裁剪图片相对路径 + Tab + 车牌文本。

## 推荐子集训练策略

不要一开始就训练全量 CCPD。建议先使用小子集跑通流程：

```text
train: 10000-30000 images
val: 2000-5000 images
test: 2000-5000 images
```

要求：

- 使用固定随机种子；
- 先用小样本确认脚本无误；
- 再扩大训练规模；
- 所有实验规模和指标必须真实记录。

## AutoDL 训练流程

建议流程：

1. 在 AutoDL 创建 RTX 4090 或 RTX 3090 实例；
2. 上传或挂载 CCPD 数据集；
3. 克隆或上传本项目仓库；
4. 创建 Python/PyTorch 环境；
5. 安装依赖；
6. 运行 CCPD 转换脚本；
7. 训练 YOLO；
8. 验证 YOLO 并保存检测示例图；
9. 训练 CRNN；
10. 验证 CRNN 并保存识别结果；
11. 下载 best.pt、crnn_best.pth、训练曲线、评估日志和示例图片；
12. 本地集成到 Django + Vue 系统中。

## 预期训练产物

YOLO：

- best.pt；
- results.png；
- PR_curve.png；
- confusion_matrix.png；
- val_batch_pred.jpg；
- detection demo images；
- Precision；
- Recall；
- mAP@0.5；
- mAP@0.5:0.95。

CRNN：

- crnn_best.pth；
- train loss log；
- validation accuracy log；
- recognition demo images 或 text output；
- character-level accuracy；
- plate-level accuracy。

## 论文写作注意

如果某些指标还没有真实训练出来，论文草稿中只能写 TODO，不要填估计值。等 AutoDL 训练完成后，再把真实日志和图片整理到 docs/experiment_results.md。
