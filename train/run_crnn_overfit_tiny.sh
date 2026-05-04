#!/usr/bin/env bash
set -euo pipefail

# Tiny overfit test for CRNN on only 8 CCPD samples.
# This is the strongest quick check for whether the model/CTC pipeline can memorize data.

PROJECT_ROOT="/cloud/cloud-ssd1/projects/license_plate_system"
DATA_ROOT="/cloud/cloud-ssd1/lpr_data/ccpd_10000/crnn"
TRAIN_FILE="${DATA_ROOT}/train.txt"
TEST_FILE="${DATA_ROOT}/test.txt"
OUTPUT_DIR="/cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn_overfit_tiny"

mkdir -p "/cloud/cloud-ssd1/runs/crnn"

cd "${PROJECT_ROOT}"

python train/train_crnn.py \
  --data-root "${DATA_ROOT}" \
  --train-file "${TRAIN_FILE}" \
  --val-file "${TRAIN_FILE}" \
  --test-file "${TEST_FILE}" \
  --epochs 300 \
  --batch-size 8 \
  --lr 0.001 \
  --output-dir "${OUTPUT_DIR}" \
  --device cuda:0 \
  --img-height 32 \
  --img-width 160 \
  --max-train-samples 8 \
  --max-val-samples 8 \
  --sample-seed 42 \
  --debug-sample-count 8 \
  --debug-image-count 8 \
  --eval-train-subset \
  --sample-pred-count 8 \
  --sample-pred-interval 10
