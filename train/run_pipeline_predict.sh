#!/usr/bin/env bash
set -euo pipefail

# YOLO + CRNN pipeline inference on CCPD test images.
# This script only performs prediction and does not retrain any model.

PROJECT_ROOT="/cloud/cloud-ssd1/projects/license_plate_system"
SOURCE="/cloud/cloud-ssd1/lpr_data/ccpd_10000/images/test"
YOLO_WEIGHTS="/cloud/cloud-ssd1/models/yolo/yolov8n_ccpd10000_best.pt"
CRNN_WEIGHTS="/cloud/cloud-ssd1/models/crnn/crnn_ccpd10000_best.pth"
CHARSET="/cloud/cloud-ssd1/models/crnn/charset.json"
OUTPUT_DIR="/cloud/cloud-ssd1/runs/pipeline/ccpd10000_yolo_crnn_predict"

mkdir -p "/cloud/cloud-ssd1/runs/pipeline"

cd "${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

python inference/license_plate_pipeline.py \
  --source "${SOURCE}" \
  --yolo-weights "${YOLO_WEIGHTS}" \
  --crnn-weights "${CRNN_WEIGHTS}" \
  --charset "${CHARSET}" \
  --output-dir "${OUTPUT_DIR}" \
  --conf 0.25 \
  --device cuda:0 \
  --img-height 32 \
  --img-width 160
