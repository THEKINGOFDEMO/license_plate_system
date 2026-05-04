# CRNN 训练说明

## 文档目的

本说明只覆盖 `Task 03`：CRNN 车牌字符识别模型训练准备。

当前阶段只做：

- CRNN 数据读取
- 字符集说明
- 模型结构说明
- smoke test
- 正式训练
- 验证
- 预测
- 结果保存说明

当前阶段不做：

- Django/Vue
- 系统开发
- YOLO+CRNN 串联推理
- 论文正文撰写

## CRNN 数据格式

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

每行格式类似：

```text
images/train/xxx.jpg    皖A12345
```

读取规则：

- 使用相对路径相对于 `data-root` 解析图片位置；
- 图像统一 resize 到 `height=32`、`width=160`；
- 默认使用灰度输入；
- 标签编码为 CTC Loss 可用格式；
- 不做字符分割，直接学习整牌字符序列。

## 字符集

当前 CRNN 字符集覆盖 CCPD 常见字符类型：

- 中文省份简称
- 英文字母
- 数字
- `警`
- `学`
- `O`

CTC blank 不作为真实字符，内部索引固定为 `0`。

## 模型结构

当前实现使用标准 CRNN 思路：

```text
输入车牌裁剪图
  -> CNN 特征提取
  -> 序列特征重排
  -> BiLSTM
  -> BiLSTM
  -> 全连接分类
  -> CTC Loss
```

模型特点：

- 使用 `CNN + BiLSTM + CTC Loss`
- 输入为整张车牌裁剪图
- 输出为完整车牌字符序列
- 不做手动字符切分

## 依赖安装

在 AutoDL 上先进入项目目录：

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
```

安装依赖：

```bash
pip install -r requirements.txt
```

## smoke test 命令

`1 epoch` smoke test 用于验证：

- 数据读取是否正常
- 模型前向传播是否正常
- CTC Loss 是否能计算
- 反向传播是否正常
- checkpoint 是否能保存

执行命令：

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
bash train/run_crnn_smoke.sh
```

输出目录：

```text
/cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn_smoke
```

## 正式训练命令

正式训练脚本默认配置：

- `epochs=50`
- `batch_size=64`
- `img_height=32`
- `img_width=160`
- `optimizer=Adam`
- `loss=CTC Loss`

执行命令：

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
bash train/run_crnn_train.sh
```

默认输出目录：

```text
/cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn
```

## 验证命令

训练完成后，使用 `best.pth` 进行验证：

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
bash train/run_crnn_eval.sh
```

验证脚本会输出：

- 字符准确率
- 整牌准确率
- 若干真实标签与预测结果样例

## 预测命令

对单张图片或目录进行预测：

目录预测脚本：

```bash
cd /cloud/cloud-ssd1/projects/license_plate_system
bash train/run_crnn_predict.sh
```

如果你想手动预测单张图，也可以执行：

```bash
python train/predict_crnn.py \
  --input /cloud/cloud-ssd1/lpr_data/ccpd_10000/crnn/images/test/example.jpg \
  --checkpoint /cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn/best.pth \
  --device cuda:0
```

## 结果保存位置

smoke test 输出目录：

```text
/cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn_smoke
```

正式训练输出目录：

```text
/cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn
```

训练完成后，重点关注：

- `best.pth`
- `last.pth`
- `history.json`

## 论文中需要保存哪些结果

建议论文与答辩阶段至少保留下列真实产物：

- `best.pth`
- `last.pth`
- 训练日志
- `history.json`
- 验证阶段输出的字符准确率
- 验证阶段输出的整牌准确率
- 若干真实标签与预测结果样例
- 若干测试集预测样例

建议论文中重点保留这些真实证据：

- CRNN 模型结构说明
- 训练配置说明
- 字符准确率
- 整牌准确率
- 预测样例对比

## 推荐执行顺序

建议在 AutoDL 上按下面顺序执行：

1. 安装依赖
2. 运行 `bash train/run_crnn_smoke.sh`
3. 确认 smoke test 输出正常
4. 运行 `bash train/run_crnn_train.sh`
5. 运行 `bash train/run_crnn_eval.sh`
6. 运行 `bash train/run_crnn_predict.sh`

## 当前结论

当前 `Task 03` 的目标是把 CRNN 训练准备、训练脚本、评估脚本、预测脚本和结果保留要求整理完整。

这一步不包含：

- Django/Vue
- 系统开发
- YOLO+CRNN 串联推理
