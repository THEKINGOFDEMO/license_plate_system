#!/usr/bin/env bash
set -euo pipefail

# Validation script for the trained YOLOv8n CCPD detector.
# Uses the best checkpoint produced by the formal training run.

PROJECT_ROOT="/cloud/cloud-ssd1/projects/license_plate_system"
DATA_YAML="/cloud/cloud-ssd1/lpr_data/ccpd_10000/configs/ccpd_yolo.yaml"
RUNS_DIR="/cloud/cloud-ssd1/runs/yolo"
MODELS_DIR="/cloud/cloud-ssd1/models"
BEST_MODEL="/cloud/cloud-ssd1/runs/yolo/ccpd10000_yolov8n_e50/weights/best.pt"

mkdir -p "${RUNS_DIR}"
mkdir -p "${MODELS_DIR}"

cd "${PROJECT_ROOT}"

yolo detect val \
  model="${BEST_MODEL}" \
  data="${DATA_YAML}" \
  imgsz=640 \
  batch=16 \
  device=0 \
  project="${RUNS_DIR}" \
  name=ccpd10000_yolov8n_val
