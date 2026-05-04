# YOLO + CRNN 串联推理说明

## 文档范围

这份文档只覆盖 `Task 04` 的算法推理流水线：
- 单图推理
- 目录推理
- YOLO 检测
- 车牌裁剪
- CRNN 识别
- 可视化结果保存
- `predictions.csv` 保存

这一步不包含：
- Django/Vue
- 系统开发
- 模型重新训练

## 默认模型路径

YOLO 权重：

```text
/cloud/cloud-ssd1/models/yolo/yolov8n_ccpd10000_best.pt
```

CRNN 权重：

```text
/cloud/cloud-ssd1/models/crnn/crnn_ccpd10000_best.pth
```

CRNN 字符集：

```text
/cloud/cloud-ssd1/models/crnn/charset.json
```

## 默认输入与输出

默认测试输入目录：

```text
/cloud/cloud-ssd1/lpr_data/ccpd_10000/images/test
```

默认输出目录：

```text
/cloud/cloud-ssd1/runs/pipeline/ccpd10000_yolo_crnn_predict
```

输出目录下会生成：
- `predictions.csv`
- `annotated/`
- `crops/`

## 依赖安装

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
pip install -r requirements.txt
```

## 导入路径说明

为避免直接运行脚本时出现：

```text
ModuleNotFoundError: No module named 'train'
```

当前项目已经同时做了两层处理：
- `inference/license_plate_pipeline.py` 会自动把项目根目录加入 `sys.path`
- `train/run_pipeline_predict.sh` 会显式导出 `PYTHONPATH`

因此下面两种方式都应能正常运行：

```bash
python inference/license_plate_pipeline.py ...
```

```bash
bash train/run_pipeline_predict.sh
```

## 推理脚本

主推理脚本：

```text
inference/license_plate_pipeline.py
```

支持参数：
- `--source`
- `--yolo-weights`
- `--crnn-weights`
- `--charset`
- `--output-dir`
- `--conf`
- `--device`
- `--img-height`
- `--img-width`

## 目录推理

推荐直接运行封装脚本：

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
bash train/run_pipeline_predict.sh
```

这会默认对下面目录做推理：

```text
/cloud/cloud-ssd1/lpr_data/ccpd_10000/images/test
```

## 单图推理

如果你要测试一张图片，可以直接运行：

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
python inference/license_plate_pipeline.py \
  --source /cloud/cloud-ssd1/lpr_data/ccpd_10000/images/test/example.jpg \
  --yolo-weights /cloud/cloud-ssd1/models/yolo/yolov8n_ccpd10000_best.pt \
  --crnn-weights /cloud/cloud-ssd1/models/crnn/crnn_ccpd10000_best.pth \
  --charset /cloud/cloud-ssd1/models/crnn/charset.json \
  --output-dir /cloud/cloud-ssd1/runs/pipeline/ccpd10000_yolo_crnn_single \
  --conf 0.25 \
  --device cuda:0 \
  --img-height 32 \
  --img-width 160
```

## predictions.csv 说明

推理完成后会保存：

```text
predictions.csv
```

字段包括：
- `image_path`
- `image_rel_path`
- `status`
- `detection_index`
- `bbox_x1`
- `bbox_y1`
- `bbox_x2`
- `bbox_y2`
- `yolo_confidence`
- `plate_text`
- `crop_path`
- `annotated_image_path`
- `error_message`

记录规则：
- 每个检测框对应一行
- 如果一张图检测到多个车牌，会有多行
- 如果一张图没有检测到车牌，也会写一行，`status=no_detection`
- 如果识别或裁剪失败，也会保留错误状态和错误信息

## 本次真实目录推理结果

这次在 AutoDL 上对测试目录完成真实推理后，结果如下：
- `total rows: 1000`
- `status ok: 1000`
- `no_detection: 0`
- `plate_correct: 945`
- `pipeline plate_accuracy: 0.945`
- `pipeline char_accuracy: 0.9915714285714285`

这些结果来自已完成的真实运行，不是估计值。

## 如何判断串联推理成功

至少满足这些条件：
1. 命令正常结束，没有报路径、依赖、CUDA 或权重加载错误。
2. 输出目录下生成了：
   - `predictions.csv`
   - `annotated/`
   - `crops/`
3. `predictions.csv` 中：
   - 有检测结果的图片应出现 `status=ok`
   - 没检测到车牌的图片应出现 `status=no_detection`
4. `annotated/` 中的可视化图应能看到：
   - 车牌框
   - YOLO 置信度
   - CRNN 识别文本
5. `crops/` 中保存的车牌裁剪图应与检测框位置基本一致。

## 当前建议

当前串联推理已经能跑通，下一步如果继续做系统集成，建议优先复用：
- `predictions.csv` 的字段结构
- `annotated/` 的标注结果图
- `crops/` 的车牌裁剪图

这一步先只完成算法推理流水线，不进入 Django/Vue。
