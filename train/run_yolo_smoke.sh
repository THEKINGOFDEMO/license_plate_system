#!/usr/bin/env bash
set -euo pipefail

# YOLO smoke test for the CCPD 10000 subset on AutoDL.
# All training outputs are written to /cloud/cloud-ssd1/runs/yolo.

PROJECT_ROOT="/cloud/cloud-ssd1/projects/license_plate_system"
DATA_YAML="/cloud/cloud-ssd1/lpr_data/ccpd_10000/configs/ccpd_yolo.yaml"
RUNS_DIR="/cloud/cloud-ssd1/runs/yolo"
MODELS_DIR="/cloud/cloud-ssd1/models"

mkdir -p "${RUNS_DIR}"
mkdir -p "${MODELS_DIR}"

cd "${PROJECT_ROOT}"

yolo detect train \
  model=yolov8n.pt \
  data="${DATA_YAML}" \
  epochs=1 \
  imgsz=640 \
  batch=16 \
  device=0 \
  workers=4 \
  project="${RUNS_DIR}" \
  name=ccpd10000_yolov8n_smoke
