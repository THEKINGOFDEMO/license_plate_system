#!/usr/bin/env bash
set -euo pipefail

# Evaluate the best CRNN checkpoint on the CCPD validation split.

PROJECT_ROOT="/cloud/cloud-ssd1/projects/license_plate_system"
DATA_ROOT="/cloud/cloud-ssd1/lpr_data/ccpd_10000/crnn"
VAL_FILE="${DATA_ROOT}/val.txt"
CHECKPOINT="/cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn/best.pth"

cd "${PROJECT_ROOT}"

python train/eval_crnn.py \
  --data-root "${DATA_ROOT}" \
  --manifest-file "${VAL_FILE}" \
  --checkpoint "${CHECKPOINT}" \
  --batch-size 64 \
  --device cuda:0
