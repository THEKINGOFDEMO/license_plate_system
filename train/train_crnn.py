"""Train a CRNN recognizer on cropped CCPD plate images."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader
from tqdm import tqdm

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
    parser = argparse.ArgumentParser(description="Train a CRNN model on CCPD cropped plate images.")
    parser.add_argument("--data-root", required=True, help="CRNN image root directory.")
    parser.add_argument("--train-file", required=True, help="Path to train.txt manifest.")
    parser.add_argument("--val-file", required=True, help="Path to val.txt manifest.")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs.")
    parser.add_argument("--batch-size", type=int, default=64, help="Training batch size.")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate.")
    parser.add_argument(
        "--output-dir",
        default="/cloud/cloud-ssd1/runs/crnn/ccpd10000_crnn",
        help="Directory used to store checkpoints and logs.",
    )
    parser.add_argument("--device", default="cuda:0", help="Training device, for example cuda:0 or cpu.")
    parser.add_argument("--img-height", type=int, default=32, help="Resized image height.")
    parser.add_argument("--img-width", type=int, default=160, help="Resized image width.")
    parser.add_argument("--workers", type=int, default=4, help="DataLoader worker count.")
    parser.add_argument("--grayscale", action="store_true", default=True, help="Use grayscale inputs.")
    parser.add_argument("--rgb", action="store_true", help="Use RGB inputs instead of grayscale.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    use_grayscale = not args.rgb
    device = torch.device(args.device if torch.cuda.is_available() or args.device == "cpu" else "cpu")
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    charset = CRNNCharset()
    train_dataset = CRNNDataset(
        data_root=args.data_root,
        manifest_path=args.train_file,
        charset=charset,
        img_height=args.img_height,
        img_width=args.img_width,
        grayscale=use_grayscale,
    )
    val_dataset = CRNNDataset(
        data_root=args.data_root,
        manifest_path=args.val_file,
        charset=charset,
        img_height=args.img_height,
        img_width=args.img_width,
        grayscale=use_grayscale,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.workers,
        collate_fn=crnn_collate_fn,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.workers,
        collate_fn=crnn_collate_fn,
    )

    model = CRNN(
        img_height=args.img_height,
        num_channels=1 if use_grayscale else 3,
        num_classes=charset.num_classes,
    ).to(device)
    criterion = nn.CTCLoss(blank=charset.blank_index, zero_infinity=True)
    optimizer = Adam(model.parameters(), lr=args.lr)

    history: List[Dict[str, float]] = []
    best_plate_accuracy = -1.0

    for epoch in range(1, args.epochs + 1):
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device, charset)
        val_loss, char_acc, plate_acc, samples = evaluate(model, val_loader, criterion, device, charset)

        epoch_record = {
            "epoch": float(epoch),
            "train_loss": float(train_loss),
            "val_loss": float(val_loss),
            "char_accuracy": float(char_acc),
            "plate_accuracy": float(plate_acc),
        }
        history.append(epoch_record)

        print(
            f"[train_crnn] epoch={epoch} "
            f"train_loss={train_loss:.4f} val_loss={val_loss:.4f} "
            f"char_acc={char_acc:.4f} plate_acc={plate_acc:.4f}"
        )
        print_sample_predictions(samples)

        checkpoint = {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "charset": charset.characters,
            "img_height": args.img_height,
            "img_width": args.img_width,
            "grayscale": use_grayscale,
            "history": history,
        }
        torch.save(checkpoint, output_dir / "last.pth")

        if plate_acc >= best_plate_accuracy:
            best_plate_accuracy = plate_acc
            torch.save(checkpoint, output_dir / "best.pth")

        (output_dir / "history.json").write_text(
            json.dumps(history, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(f"[train_crnn] Best plate accuracy: {best_plate_accuracy:.4f}")
    print(f"[train_crnn] Outputs saved to: {output_dir}")
    return 0


def train_one_epoch(
    model: CRNN,
    data_loader: DataLoader,
    criterion: nn.CTCLoss,
    optimizer: Adam,
    device: torch.device,
    charset: CRNNCharset,
) -> float:
    del charset
    model.train()
    total_loss = 0.0

    for batch in tqdm(data_loader, desc="train", leave=False):
        images = batch["images"].to(device)
        targets = batch["targets"].to(device)
        target_lengths = batch["target_lengths"].to(device)

        optimizer.zero_grad()
        logits = model(images)
        log_probs = logits.log_softmax(dim=2)
        input_lengths = torch.full(
            size=(images.size(0),),
            fill_value=log_probs.size(0),
            dtype=torch.long,
            device=device,
        )

        loss = criterion(log_probs, targets, input_lengths, target_lengths)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    return total_loss / max(len(data_loader), 1)


@torch.no_grad()
def evaluate(
    model: CRNN,
    data_loader: DataLoader,
    criterion: nn.CTCLoss,
    device: torch.device,
    charset: CRNNCharset,
) -> Tuple[float, float, float, List[Tuple[str, str, str]]]:
    model.eval()
    total_loss = 0.0
    all_predictions: List[str] = []
    all_targets: List[str] = []
    sample_outputs: List[Tuple[str, str, str]] = []

    for batch in tqdm(data_loader, desc="eval", leave=False):
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
            if len(sample_outputs) < 5:
                sample_outputs.append((str(rel_path), str(target_text), str(pred_text)))

    char_acc, plate_acc = compute_accuracy(all_predictions, all_targets)
    return total_loss / max(len(data_loader), 1), char_acc, plate_acc, sample_outputs


def print_sample_predictions(samples: List[Tuple[str, str, str]]) -> None:
    if not samples:
        return
    print("[train_crnn] Sample predictions:")
    for rel_path, target_text, pred_text in samples:
        print(f"  - {rel_path}: gt={target_text} pred={pred_text}")


if __name__ == "__main__":
    raise SystemExit(main())
