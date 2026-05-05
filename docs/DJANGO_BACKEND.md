# Django 后端说明

## 文档范围

这份文档覆盖当前 Django 后端接口与联调方式，包括：
- 健康检查接口
- 图片识别接口
- 历史记录接口
- 统计接口
- 本地启动方式
- 常见问题

## 当前接口

已实现接口：
- `GET /api/health/`
- `GET /api/stats/`
- `POST /api/recognize/`
- `GET /api/records/`

## 安装依赖

```bash
cd D:/django_project/laji/lunwen/license_plate_system
pip install -r requirements.txt
```

## 模型路径配置

通过环境变量配置：
- `LPR_YOLO_WEIGHTS`
- `LPR_CRNN_WEIGHTS`
- `LPR_CHARSET`
- `LPR_OUTPUT_DIR`
- `LPR_DEVICE`
- `LPR_CONFIDENCE`

示例请参考：
- [\.env.example](/D:/django_project/laji/lunwen/license_plate_system/.env.example)

## 启动后端

```bash
cd D:/django_project/laji/lunwen/license_plate_system
python backend/manage.py migrate
python backend/manage.py runserver
```

默认地址：
- [http://127.0.0.1:8000](http://127.0.0.1:8000)

## 1. 健康检查接口

请求：

```http
GET /api/health/
```

返回示例：

```json
{
  "status": "ok",
  "model_ready": true
}
```

说明：
- `status=ok` 表示后端服务可访问
- `model_ready=true` 表示模型路径有效且可成功加载

## 2. 统计接口

请求：

```http
GET /api/stats/
```

返回格式：

```json
{
  "status": "ok",
  "total": 10,
  "ok": 7,
  "no_detection": 2,
  "error": 1
}
```

说明：
- `total`：累计识别记录数
- `ok`：识别成功数
- `no_detection`：未检测到车牌数
- `error`：错误数

如果当前没有记录，也会返回：

```json
{
  "status": "ok",
  "total": 0,
  "ok": 0,
  "no_detection": 0,
  "error": 0
}
```

## 3. 上传识别接口

请求：

```http
POST /api/recognize/
Content-Type: multipart/form-data
```

字段：
- `image`

`curl` 示例：

```bash
curl -X POST http://127.0.0.1:8000/api/recognize/ \
  -F "image=@D:/django_project/laji/lunwen/test_images/car_001.jpg"
```

识别成功返回示例：

```json
{
  "status": "ok",
  "plate_text": "皖A12345",
  "bbox": [120, 210, 280, 260],
  "yolo_confidence": 0.98,
  "annotated_image_url": "http://127.0.0.1:8000/media/results/annotated/xxx.jpg",
  "crop_image_url": "http://127.0.0.1:8000/media/results/crops/xxx.jpg",
  "record_id": 1
}
```

未检测到车牌返回示例：

```json
{
  "status": "no_detection",
  "message": "未检测到车牌",
  "record_id": 2
}
```

## 4. 历史记录接口

请求：

```http
GET /api/records/
```

支持查询参数：
- `page`
- `page_size`
- `status`
- `keyword`

示例：

```http
GET /api/records/?page=1&page_size=10&status=ok&keyword=皖A
```

返回格式：

```json
{
  "status": "ok",
  "count": 100,
  "page": 1,
  "page_size": 10,
  "results": [...],
  "records": [...]
}
```

说明：
- `results` 为当前页数据
- `records` 为兼容旧前端调用保留的字段
- 支持按状态筛选与按文件名/车牌号关键词搜索

## 首页与系统说明页的功能定位

前端总览页 `/` 主要依赖：
- `/api/health/`
- `/api/stats/`
- `/api/records/?page=1&page_size=5`

前端系统说明页 `/about` 主要展示静态说明，不依赖新的推理接口。

## 历史记录页支持能力

前端历史记录页支持：
- 分页
- 状态筛选
- 关键词搜索
- 详情弹窗

后端配合提供：
- 统一分页返回格式
- `annotated_image_url`
- `crop_image_url`

## 输出保存位置

- 上传原图：`media/uploads/`
- 标注图：`media/results/annotated/`
- 裁剪图：`media/results/crops/`

## 常见问题

### 1. `/api/health/` 中 `model_ready=false`

原因：
- 模型权重路径错误
- 字符集路径错误

处理：
- 检查 `LPR_YOLO_WEIGHTS`
- 检查 `LPR_CRNN_WEIGHTS`
- 检查 `LPR_CHARSET`

### 2. `/api/recognize/` 返回错误

原因：
- 上传文件不是有效图片
- 模型未正确加载
- 推理过程异常

处理：
- 先访问 `/api/health/`
- 再检查后端终端日志

### 3. `/api/records/` 无数据

原因：
- 还没有识别记录
- 当前筛选条件下没有匹配记录

处理：
- 先执行一次图片识别
- 清空 `status` 或 `keyword` 筛选条件

## 如何判断后端接口成功

至少满足：
1. 后端能够正常启动
2. `/api/health/` 返回 `status=ok`
3. `/api/stats/` 返回统计字段
4. `/api/recognize/` 能返回识别结果
5. `/api/records/` 能返回分页、筛选和搜索结果
