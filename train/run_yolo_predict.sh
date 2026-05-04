#!/usr/bin/env bash
set -euo pipefail

# Prediction script for the trained YOLOv8n CCPD detector.
# Runs inference on the prepared test split images.

PROJECT_ROOT="/cloud/cloud-ssd1/projects/license_plate_system"
RUNS_DIR="/cloud/cloud-ssd1/runs/yolo"
MODELS_DIR="/cloud/cloud-ssd1/models"
BEST_MODEL="/cloud/cloud-ssd1/runs/yolo/ccpd10000_yolov8n_e50/weights/best.pt"
TEST_SOURCE="/cloud/cloud-ssd1/lpr_data/ccpd_10000/images/test"

mkdir -p "${RUNS_DIR}"
mkdir -p "${MODELS_DIR}"

cd "${PROJECT_ROOT}"

yolo detect predict \
  model="${BEST_MODEL}" \
  source="${TEST_SOURCE}" \
  imgsz=640 \
  conf=0.25 \
  device=0 \
  project="${RUNS_DIR}" \
  name=ccpd10000_yolov8n_predict
