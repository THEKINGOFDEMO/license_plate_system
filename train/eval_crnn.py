"""Evaluate a trained CRNN checkpoint on a CCPD manifest."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple

import torch
from torch import nn
from torch.utils.data import DataLoader

try:
    from train.crnn_dataset import (
        CRNNDataset,
        CRNNCharset,
        compute_accuracy,
        crnn_collate_fn,
        decode_batch_predictions,
    )
    from train.crnn_model import CRNN
except ImportError:
    from crnn_dataset import CRNNDataset, CRNNCharset, compute_accuracy, crnn_collate_fn, decode_batch_predictions
    from crnn_model import CRNN


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate a trained CRNN checkpoint.")
    parser.add_argument("--data-root", required=True, help="CRNN image root directory.")
    parser.add_argument("--manifest-file", required=True, help="Manifest file such as val.txt or test.txt.")
    parser.add_argument("--checkpoint", required=True, help="Path to best.pth or another checkpoint.")
    parser.add_argument("--batch-size", type=int, default=64, help="Evaluation batch size.")
    parser.add_argument("--device", default="cuda:0", help="Evaluation device.")
    parser.add_argument("--workers", type=int, default=4, help="DataLoader worker count.")
    parser.add_argument("--num-samples", type=int, default=10, help="Number of example predictions to print.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    device = torch.device(args.device if torch.cuda.is_available() or args.device == "cpu" else "cpu")
    checkpoint = torch.load(Path(args.checkpoint).resolve(), map_location=device)

    charset = CRNNCharset(checkpoint["charset"])
    dataset = CRNNDataset(
        data_root=args.data_root,
        manifest_path=args.manifest_file,
        charset=charset,
        img_height=int(checkpoint["img_height"]),
        img_width=int(checkpoint["img_width"]),
        grayscale=bool(checkpoint["grayscale"]),
    )
    data_loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.workers,
        collate_fn=crnn_collate_fn,
    )

    model = CRNN(
        img_height=int(checkpoint["img_height"]),
        num_channels=1 if bool(checkpoint["grayscale"]) else 3,
        num_classes=charset.num_classes,
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    criterion = nn.CTCLoss(blank=charset.blank_index, zero_infinity=True)

    val_loss, char_acc, plate_acc, samples = evaluate(
        model=model,
        data_loader=data_loader,
        criterion=criterion,
        device=device,
        charset=charset,
        sample_limit=args.num_samples,
    )

    print(f"[eval_crnn] checkpoint={args.checkpoint}")
    print(f"[eval_crnn] manifest={args.manifest_file}")
    print(f"[eval_crnn] loss={val_loss:.4f}")
    print(f"[eval_crnn] char_accuracy={char_acc:.4f}")
    print(f"[eval_crnn] plate_accuracy={plate_acc:.4f}")
    print("[eval_crnn] Sample predictions:")
    for rel_path, target_text, pred_text in samples:
        print(f"  - {rel_path}: gt={target_text} pred={pred_text}")
    return 0


@torch.no_grad()
def evaluate(
    model: CRNN,
    data_loader: DataLoader,
    criterion: nn.CTCLoss,
    device: torch.device,
    charset: CRNNCharset,
    sample_limit: int,
) -> Tuple[float, float, float, List[Tuple[str, str, str]]]:
    model.eval()
    total_loss = 0.0
    all_predictions: List[str] = []
    all_targets: List[str] = []
    sample_outputs: List[Tuple[str, str, str]] = []

    for batch in data_loader:
        images = batch["images"].to(device)
        targets = batch["targets"].to(device)
        target_lengths = batch["target_lengths"].to(device)
        texts = batch["texts"]
        image_rel_paths = batch["image_rel_paths"]

        logits = model(images)
        log_probs = logits.log_softmax(dim=2)
        input_lengths = torch.full(
            size=(images.size(0),),
            fill_value=log_probs.size(0),
            dtype=torch.long,
            device=device,
        )
        loss = criterion(log_probs, targets, input_lengths, target_lengths)
        total_loss += loss.item()

        predictions = decode_batch_predictions(logits, charset)
        all_predictions.extend(predictions)
        all_targets.extend(texts)

        for rel_path, target_text, pred_text in zip(image_rel_paths, texts, predictions):
            if len(sample_outputs) < sample_limit:
                sample_outputs.append((str(rel_path), str(target_text), str(pred_text)))

    char_acc, plate_acc = compute_accuracy(all_predictions, all_targets)
    return total_loss / max(len(data_loader), 1), char_acc, plate_acc, sample_outputs


if __name__ == "__main__":
    raise SystemExit(main())
