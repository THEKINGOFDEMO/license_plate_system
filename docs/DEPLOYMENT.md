# 部署准备说明

## 文档范围

这份文档用于 `Task 07` 的部署准备，包含：
- 本地开发启动方式
- 服务器部署准备
- 环境变量配置
- 模型文件放置方式
- 前端构建与静态资源说明
- 常见部署问题

这份文档不包含模型训练步骤。

## 一、本地开发启动

### 1. 启动 Django 后端

```bash
cd D:/django_project/laji/lunwen/license_plate_system
pip install -r requirements.txt
python backend/manage.py migrate
python backend/manage.py runserver
```

### 2. 启动 Vue 前端

```bash
cd D:/django_project/laji/lunwen/license_plate_system/frontend
npm install
npm run dev
```

默认访问地址：
- 后端：`http://127.0.0.1:8000`
- 前端：`http://127.0.0.1:5173`

## 二、环境变量配置

项目已提供：
- [.env.example](/D:/django_project/laji/lunwen/license_plate_system/.env.example)

建议至少配置：

```text
LPR_YOLO_WEIGHTS=
LPR_CRNN_WEIGHTS=
LPR_CHARSET=
LPR_OUTPUT_DIR=
LPR_DEVICE=cpu
LPR_CONFIDENCE=0.25
DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=
CORS_ALLOWED_ORIGINS=
```

示例说明：
- `LPR_YOLO_WEIGHTS`：YOLO 权重路径
- `LPR_CRNN_WEIGHTS`：CRNN 权重路径
- `LPR_CHARSET`：字符集 `charset.json`
- `LPR_OUTPUT_DIR`：识别结果输出目录
- `LPR_DEVICE`：本地可用 `cpu`，服务器可用 `cuda:0`
- `DJANGO_ALLOWED_HOSTS`：部署域名或服务器 IP，多个值可用逗号分隔
- `CORS_ALLOWED_ORIGINS`：允许访问后端的前端地址，多个值可用逗号分隔

## 三、模型文件说明

模型文件不要提交到 GitHub。

部署时需要把这些文件单独上传到服务器指定目录：
- YOLO 权重 `.pt`
- CRNN 权重 `.pth`
- `charset.json`

然后通过环境变量配置它们的真实路径。

## 四、腾讯云 / 阿里云服务器部署准备

推荐目录结构：

```text
/opt/license_plate_system/
  backend/
  frontend/
  media/
  models/
    yolo/
    crnn/
```

部署前建议准备：
- Python 3.10 左右环境
- Node.js 与 npm
- 虚拟环境
- 可用的 YOLO / CRNN 权重和字符集文件

## 五、后端部署建议

生产环境建议不要直接使用 `runserver`。

可选方案：
- Linux：`gunicorn`
- Windows：`waitress`

示例思路：
- Django 提供 API
- `/media/` 目录由 Django 或 Nginx 暴露
- 模型文件通过环境变量读取

### Linux 示例

```bash
gunicorn backend.wsgi:application --chdir backend --bind 0.0.0.0:8000
```

### Windows 示例

可考虑使用 `waitress` 启动 Django WSGI 应用。

## 六、前端构建与部署

本地构建：

```bash
cd D:/django_project/laji/lunwen/license_plate_system/frontend
npm install
npm run build
```

构建产物位于：

```text
frontend/dist/
```

生产环境建议：
- 前端 `dist` 由 Nginx 托管
- `VITE_API_BASE_URL` 指向正式后端地址

## 七、/media/ 文件访问说明

上传原图、标注图和裁剪图位于：

```text
media/
```

部署后需要确保：
- `/media/` 目录可被访问
- 后端返回的图片 URL 可被浏览器打开

如果使用 Nginx，建议单独配置：
- `/media/` 指向 Django 项目的 `media/`
- `/static/` 或前端构建目录指向 `dist/`

## 八、常见问题

### 1. 跨域问题

现象：
- 浏览器报 CORS 错误

处理：
- 配置 `CORS_ALLOWED_ORIGINS`
- 确认前端真实访问地址已被允许

### 2. 模型路径错误

现象：
- `/api/health/` 返回 `model_ready=false`
- `/api/recognize/` 返回模型文件不存在

处理：
- 检查 `LPR_YOLO_WEIGHTS`
- 检查 `LPR_CRNN_WEIGHTS`
- 检查 `LPR_CHARSET`

### 3. 图片不显示

现象：
- 前端页面无法打开标注图或裁剪图

处理：
- 检查 `/media/` 是否正确暴露
- 检查后端返回的 URL 是否正确
- 检查反向代理是否允许访问媒体目录

### 4. 端口未开放

现象：
- 本机正常，外网无法访问

处理：
- 检查云服务器安全组
- 检查系统防火墙
- 检查 Nginx / gunicorn / waitress 的绑定端口

### 5. 服务器内存不足或 CPU 推理较慢

现象：
- 首次请求加载模型较慢
- 识别过程耗时明显增加

处理：
- 尽量使用更稳定的部署环境
- 复用已加载模型，避免重复加载
- 如果条件允许，可使用 GPU 推理

## 九、部署建议总结

部署时优先遵循这几个原则：
- 模型文件单独管理，不提交 GitHub
- 环境变量统一管理模型路径和运行参数
- Django 后端负责 API 与结果保存
- 前端静态页面单独构建部署
- `media/` 目录单独开放访问
