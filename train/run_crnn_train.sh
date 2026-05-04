#!/usr/bin/env bash
set -euo pipefail

# Formal CRNN training on the CCPD 10000 subset.

PROJECT_ROOT="/cloud/cloud-ssd1/projects/license_plate_system"
DATA_ROOT="/cloud/cloud-ssd1/lpr_data/ccpd_10000/crnn"
TRAIN_FILE="${DATA_ROOT}/train.txt"
VAL_FILE="${DATA_ROOT}/val.txt"
TEST_FILE="${DATA_ROOT}/test.txt"
OUTPUT_DIR="/cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn"

mkdir -p "/cloud/cloud-ssd1/runs/crnn"

cd "${PROJECT_ROOT}"

python train/train_crnn.py \
  --data-root "${DATA_ROOT}" \
  --train-file "${TRAIN_FILE}" \
  --val-file "${VAL_FILE}" \
  --test-file "${TEST_FILE}" \
  --epochs 50 \
  --batch-size 64 \
  --lr 0.001 \
  --output-dir "${OUTPUT_DIR}" \
  --device cuda:0 \
  --img-height 32 \
  --img-width 160
