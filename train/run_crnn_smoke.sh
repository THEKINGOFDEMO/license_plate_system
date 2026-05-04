#!/usr/bin/env bash
set -euo pipefail

# 1 epoch smoke test for CCPD CRNN recognition on AutoDL.
# This validates data loading, forward pass, CTC loss, backprop, and checkpoint saving.

PROJECT_ROOT="/cloud/cloud-ssd1/projects/license_plate_system"
DATA_ROOT="/cloud/cloud-ssd1/lpr_data/ccpd_10000/crnn"
TRAIN_FILE="${DATA_ROOT}/train.txt"
VAL_FILE="${DATA_ROOT}/val.txt"
OUTPUT_DIR="/cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn_smoke"

mkdir -p "/cloud/cloud-ssd1/runs/crnn"

cd "${PROJECT_ROOT}"

python train/train_crnn.py \
  --data-root "${DATA_ROOT}" \
  --train-file "${TRAIN_FILE}" \
  --val-file "${VAL_FILE}" \
  --epochs 1 \
  --batch-size 16 \
  --lr 0.001 \
  --output-dir "${OUTPUT_DIR}" \
  --device cuda:0 \
  --img-height 32 \
  --img-width 160
