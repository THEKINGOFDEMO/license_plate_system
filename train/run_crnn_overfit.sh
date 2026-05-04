#!/usr/bin/env bash
set -euo pipefail

# Overfit test for CRNN on a tiny CCPD subset.
# This is the first command to run during CRNN diagnosis.

PROJECT_ROOT="/cloud/cloud-ssd1/projects/license_plate_system"
DATA_ROOT="/cloud/cloud-ssd1/lpr_data/ccpd_10000/crnn"
TRAIN_FILE="${DATA_ROOT}/train.txt"
TEST_FILE="${DATA_ROOT}/test.txt"
OUTPUT_DIR="/cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn_overfit"

mkdir -p "/cloud/cloud-ssd1/runs/crnn"

cd "${PROJECT_ROOT}"

python train/train_crnn.py \
  --data-root "${DATA_ROOT}" \
  --train-file "${TRAIN_FILE}" \
  --val-file "${TRAIN_FILE}" \
  --test-file "${TEST_FILE}" \
  --epochs 150 \
  --batch-size 16 \
  --lr 0.001 \
  --output-dir "${OUTPUT_DIR}" \
  --device cuda:0 \
  --img-height 32 \
  --img-width 160 \
  --max-train-samples 64 \
  --max-val-samples 64 \
  --sample-seed 42 \
  --debug-sample-count 10 \
  --debug-image-count 10
