# CRNN 训练说明

## 文档范围

这份文档只覆盖 CRNN 车牌字符识别训练相关内容，包括：
- 数据格式
- 字符集与 CTC 约定
- smoke test
- overfit test
- 正式训练
- 评估与预测
- 训练输出与诊断文件

这份文档不包含：
- Django/Vue
- 系统开发
- YOLO+CRNN 串联推理

## 数据路径

当前 CRNN 数据根目录：

```text
/cloud/cloud-ssd1/lpr_data/ccpd_10000/crnn
```

清单文件：
- `/cloud/cloud-ssd1/lpr_data/ccpd_10000/crnn/train.txt`
- `/cloud/cloud-ssd1/lpr_data/ccpd_10000/crnn/val.txt`
- `/cloud/cloud-ssd1/lpr_data/ccpd_10000/crnn/test.txt`

图像目录：
- `/cloud/cloud-ssd1/lpr_data/ccpd_10000/crnn/images/train`
- `/cloud/cloud-ssd1/lpr_data/ccpd_10000/crnn/images/val`
- `/cloud/cloud-ssd1/lpr_data/ccpd_10000/crnn/images/test`

manifest 每行格式：

```text
images/train/xxx.jpg    皖A12345
```

## 字符集与 CTC 约定

当前实现会根据 `train/val/test` manifest 中真实出现的字符动态构建字符集，并保存到：

```text
charset.json
```

关键约定：
- `blank_index = 0`
- 真实字符索引从 `1` 开始
- 模型输出类别数 `C = charset_size + 1`
- 输入图像默认 resize 到 `32x160`
- 默认使用灰度输入
- CTC 解码采用标准 greedy decode：
  - 逐时间步取 `argmax`
  - 折叠连续重复 token
  - 移除 blank

## 诊断输出

训练启动时会在输出目录保存这些文件：
- `charset.json`
- `train_manifest_summary.json`
- `val_manifest_summary.json`
- `test_manifest_summary.json`
- `dataset_debug_samples.json`
- `debug_shapes.json`
- `history.json`
- `history.csv`
- `train.log`

其中 `debug_shapes.json` 会保存：
- `image_tensor_shape`
- `model_output_shape`
- `T`
- `num_classes`
- `max_label_length`
- `min_target_length`
- `max_target_length`
- `sample_input_lengths`
- `sample_target_lengths`
- `blank_index`
- `charset_size`
- `whether min_input_length >= max_target_length`

训练开始时终端也会明确打印：
- `Charset size`
- `Max label length`
- `Model output time steps T`
- `Output classes C`
- `input_lengths sample`
- `target_lengths sample`
- `Label roundtrip OK`

如果 `T < max_label_length`，训练脚本会直接报错停止。

## 依赖安装

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
pip install -r requirements.txt
```

## Smoke Test

作用：
- 验证数据读取是否正常
- 验证前向传播、CTC Loss、反向传播是否正常
- 验证 checkpoint 是否能保存

命令：

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
bash train/run_crnn_smoke.sh
```

输出目录：

```text
/cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn_smoke
```

## Overfit Test

64 张样本 overfit：

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
bash train/run_crnn_overfit.sh
```

用途：
- 判断模型是否能在极小训练子集上学习到完整车牌
- 辅助定位 CTC、标签、解码、结构是否仍有 bug

输出目录：

```text
/cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn_overfit
```

## Tiny Overfit Test

8 张样本 tiny overfit 是当前最强的链路验证。

命令：

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
bash train/run_crnn_overfit_tiny.sh
```

默认配置：
- `epochs=1000`
- `batch_size=8`
- `lr=0.003`
- `grad_clip=5.0`
- `early_stop_train_plate_acc=1.0`
- 每 `50` 个 epoch 打印完整 `8` 条 `gt/pred`
- 训练和评估都只使用同一批 `8` 张训练样本

输出目录：

```text
/cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn_overfit_tiny
```

## Tiny Overfit 成功标准

重点看训练集本身，不是 val：
- `train_plate_acc` 明显上升，不能长期停在 `0`
- 最理想情况是 `train_plate_acc` 接近或达到 `1.0`
- `train.log` 末尾打印的 8 条最终样例中，大多数 `pred` 应与 `gt` 完全一致
- `final_train_predictions.csv` 中 `exact_match` 的和应与终端打印的 `x/8` 一致

如果 tiny overfit 仍失败，不要直接进入正式训练。

## final_train_predictions.csv

当训练脚本启用了 `--eval-train-subset`，训练结束后会额外保存：

```text
final_train_predictions.csv
```

该文件至少包含：
- `image_path`
- `gt`
- `pred`
- `gt_len`
- `pred_len`
- `exact_match`
- `edit_distance`

另外会额外保存：
- `char_match_count`
- `char_total`

指标复核方式：
- `train_plate_acc = exact_match` 列的均值
- `train_char_acc = sum(char_match_count) / sum(char_total)`

## 正式训练

命令：

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
bash train/run_crnn_train.sh
```

默认输出目录：

```text
/cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn
```

建议只有在这些条件都满足后再进入正式训练：
- smoke test 通过
- tiny overfit 能明显记住 8 张样本
- 64 张 overfit 也有明显提升

## 评估

命令：

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
bash train/run_crnn_eval.sh
```

评估输出重点关注：
- 字符准确率
- 整牌准确率
- 若干 `gt/pred` 样例

## 预测

目录预测脚本：

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
bash train/run_crnn_predict.sh
```

也可以单图预测：

```bash
python train/predict_crnn.py \
  --input /cloud/cloud-ssd1/lpr_data/ccpd_10000/crnn/images/test/example.jpg \
  --checkpoint /cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn/best.pth \
  --device cuda:0
```

## 结果保存建议

训练完成后建议保留：
- `best.pth`
- `last.pth`
- `charset.json`
- `debug_shapes.json`
- `train_manifest_summary.json`
- `val_manifest_summary.json`
- `dataset_debug_samples.json`
- `history.json`
- `history.csv`
- `train.log`
- `final_train_predictions.csv`

## 当前诊断建议

如果 tiny overfit 在 `1000` epoch 后仍无法达到较高的 `train_plate_acc`，先不要直接正式训练。下一步优先考虑：
- 更强的 CRNN 主干
- 更稳的解码策略，例如 beam search
- 固定 7 位车牌的多位置分类 baseline

这一步先只作为诊断建议，不在当前任务里直接实现这些替代方案。
