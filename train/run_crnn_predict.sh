#!/usr/bin/env bash
set -euo pipefail

# Run CRNN prediction on the prepared CCPD test crop directory.

PROJECT_ROOT="/cloud/cloud-ssd1/projects/license_plate_system"
CHECKPOINT="/cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn/best.pth"
INPUT_PATH="/cloud/cloud-ssd1/lpr_data/ccpd_10000/crnn/images/test"

cd "${PROJECT_ROOT}"

python train/predict_crnn.py \
  --input "${INPUT_PATH}" \
  --checkpoint "${CHECKPOINT}" \
  --device cuda:0
