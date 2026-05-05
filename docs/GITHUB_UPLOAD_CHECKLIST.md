# GitHub Upload Checklist

## 可提交内容

- 源代码目录：
  - `inference/`
  - `train/`
  - `backend/`
  - `frontend/src/`
- 前端项目文件：
  - `frontend/package.json`
  - `frontend/package-lock.json`
  - `frontend/vite.config.js`
  - `frontend/index.html`
- 配置与依赖：
  - `requirements.txt`
  - `.gitignore`
  - `.env.example`
- 文档：
  - `docs/`
  - `README.md`
  - `PROJECT_BRIEF.md`
  - `TASKS.md`
- Django migration：
  - `backend/recognition/migrations/*.py`

## 不可提交内容

- 模型权重：
  - `*.pt`
  - `*.pth`
  - `*.onnx`
- 数据集和中间数据：
  - `datasets/`
  - `lpr_data/`
  - `CCPD2019/`
  - `ccpd_10000/`
- 训练和推理输出：
  - `runs/`
  - `outputs/`
  - `artifacts/`
  - `license_plate_artifacts/`
  - `*.tar.gz`
  - `*.zip`
- Django 运行文件：
  - `media/`
  - `db.sqlite3`
  - `backend/db.sqlite3`
  - `*.sqlite3`
- 前端依赖和构建产物：
  - `frontend/node_modules/`
  - `frontend/dist/`
- Python 缓存和虚拟环境：
  - `__pycache__/`
  - `*.pyc`
  - `.venv/`
  - `venv/`
  - `env/`
- 环境变量和本地配置：
  - `.env`
  - `*.env.local`
- 本地测试图片与截图：
  - `test_images/`
  - `demo_images/`
  - `screenshots/`
- IDE 和系统文件：
  - `.idea/`
  - `.vscode/`
  - `.DS_Store`
  - `Thumbs.db`

## 提交前检查命令

先检查当前变更：

```powershell
git status --short
```

查看当前已被 Git 跟踪的文件：

```powershell
git ls-files
```

确认大文件、模型、数据库、压缩包没有进入暂存区：

```powershell
git status --short
git ls-files *.pt *.pth *.onnx *.sqlite3 *.tar.gz *.zip
```

## 如果误追踪了大文件

只从 Git 索引移除，不删除本地文件：

```powershell
git rm --cached <file>
git rm -r --cached <dir>
```

常见示例：

```powershell
git rm --cached backend/db.sqlite3
git rm -r --cached media
git rm -r --cached frontend/node_modules
git rm -r --cached frontend/dist
git rm -r --cached datasets
git rm -r --cached lpr_data
git rm -r --cached runs
git rm -r --cached artifacts
git rm --cached *.pt
git rm --cached *.pth
git rm --cached *.onnx
```

执行后再次检查：

```powershell
git status --short
```

## 推荐提交顺序

1. 先确认 `.gitignore` 已更新。
2. 先提交代码和配置文件。
3. 再提交文档文件。
4. 最后再执行一次 `git status --short`，确认没有模型、数据、数据库、`media/`、`node_modules/`、`dist/` 等内容。

## 额外说明

本项目本地运行需要手动准备模型文件：

- YOLO 权重
- CRNN 权重
- `charset.json`

这些模型文件不上传 GitHub，需在本地或服务器上按文档路径单独准备。
