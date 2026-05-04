"""Train a CRNN recognizer on cropped CCPD plate images."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import torch
from PIL import Image
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader
from tqdm import tqdm

try:
    from train.crnn_dataset import (
        CRNNDataset,
        CRNNCharset,
        build_charset_from_manifests,
        compute_accuracy,
        crnn_collate_fn,
        decode_batch_predictions,
        save_debug_records,
        save_manifest_summary,
        summarize_manifest,
    )
    from train.crnn_model import CRNN
except ImportError:
    from crnn_dataset import (
        CRNNDataset,
        CRNNCharset,
        build_charset_from_manifests,
        compute_accuracy,
        crnn_collate_fn,
        decode_batch_predictions,
        save_debug_records,
        save_manifest_summary,
        summarize_manifest,
    )
    from crnn_model import CRNN


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train a CRNN model on CCPD cropped plate images.")
    parser.add_argument("--data-root", required=True, help="CRNN image root directory.")
    parser.add_argument("--train-file", required=True, help="Path to train.txt manifest.")
    parser.add_argument("--val-file", required=True, help="Path to val.txt manifest.")
    parser.add_argument("--test-file", default=None, help="Optional test.txt manifest used for charset diagnostics.")
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
    parser.add_argument("--max-train-samples", type=int, default=None, help="Optional subset size for train manifest.")
    parser.add_argument("--max-val-samples", type=int, default=None, help="Optional subset size for val manifest.")
    parser.add_argument("--sample-seed", type=int, default=42, help="Random seed used for subset sampling.")
    parser.add_argument("--debug-sample-count", type=int, default=10, help="Number of dataset debug samples to print.")
    parser.add_argument(
        "--debug-image-count",
        type=int,
        default=0,
        help="Number of resized debug images to save under output-dir/debug_samples.",
    )
    parser.add_argument("--resume", default=None, help="Optional checkpoint path used to resume training.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    use_grayscale = not args.rgb
    device = torch.device(args.device if torch.cuda.is_available() or args.device == "cpu" else "cpu")
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_paths = [args.train_file, args.val_file]
    if args.test_file:
        manifest_paths.append(args.test_file)

    charset = build_charset_from_manifests(
        data_root=args.data_root,
        manifest_paths=manifest_paths,
    )
    charset.save_json(output_dir / "charset.json")

    train_dataset = CRNNDataset(
        data_root=args.data_root,
        manifest_path=args.train_file,
        charset=charset,
        img_height=args.img_height,
        img_width=args.img_width,
        grayscale=use_grayscale,
        max_samples=args.max_train_samples,
        sample_seed=args.sample_seed,
    )
    val_dataset = CRNNDataset(
        data_root=args.data_root,
        manifest_path=args.val_file,
        charset=charset,
        img_height=args.img_height,
        img_width=args.img_width,
        grayscale=use_grayscale,
        max_samples=args.max_val_samples,
        sample_seed=args.sample_seed,
    )

    train_summary = summarize_manifest(train_dataset.records, args.train_file)
    val_summary = summarize_manifest(val_dataset.records, args.val_file)
    save_manifest_summary(train_summary, output_dir / "train_manifest_summary.json")
    save_manifest_summary(val_summary, output_dir / "val_manifest_summary.json")
    test_summary = None
    if args.test_file:
        test_records = CRNNDataset(
            data_root=args.data_root,
            manifest_path=args.test_file,
            charset=charset,
            img_height=args.img_height,
            img_width=args.img_width,
            grayscale=use_grayscale,
        ).records
        test_summary = summarize_manifest(test_records, args.test_file)
        save_manifest_summary(test_summary, output_dir / "test_manifest_summary.json")

    print_charset_debug_info(charset=charset, train_summary=train_summary, val_summary=val_summary, test_summary=test_summary)

    debug_records = train_dataset.get_debug_records(count=args.debug_sample_count)
    save_debug_records(debug_records, output_dir / "dataset_debug_samples.json")
    print_dataset_debug_samples(debug_records)
    if args.debug_image_count > 0:
        save_debug_images(debug_records, output_dir / "debug_samples", args.debug_image_count, use_grayscale)

    verify_label_roundtrip(charset, "皖A12345")
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
        img_width=args.img_width,
        num_channels=1 if use_grayscale else 3,
        num_classes=charset.num_classes,
    ).to(device)
    criterion = nn.CTCLoss(blank=charset.blank_index, zero_infinity=True)
    optimizer = Adam(model.parameters(), lr=args.lr)

    history: List[Dict[str, float]] = []
    best_plate_accuracy = -1.0
    start_epoch = 1

    if args.resume:
        checkpoint = torch.load(Path(args.resume).resolve(), map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        history = checkpoint.get("history", [])
        best_plate_accuracy = max((float(item["plate_accuracy"]) for item in history), default=-1.0)
        start_epoch = int(checkpoint["epoch"]) + 1
        print(f"[train_crnn] Resumed from checkpoint: {args.resume} at epoch {start_epoch}")

    history_csv_path = output_dir / "history.csv"
    if not history_csv_path.exists() or start_epoch == 1:
        history_csv_path.write_text("epoch,train_loss,val_loss,char_accuracy,plate_accuracy,learning_rate\n", encoding="utf-8")

    print(f"[train_crnn] Model output time steps T={model.output_time_steps}")

    for epoch in range(start_epoch, args.epochs + 1):
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, char_acc, plate_acc, samples = evaluate(model, val_loader, criterion, device, charset)
        learning_rate = float(optimizer.param_groups[0]["lr"])

        epoch_record = {
            "epoch": float(epoch),
            "train_loss": float(train_loss),
            "val_loss": float(val_loss),
            "char_accuracy": float(char_acc),
            "plate_accuracy": float(plate_acc),
            "learning_rate": learning_rate,
        }
        history.append(epoch_record)

        print(
            f"[train_crnn] epoch={epoch} "
            f"train_loss={train_loss:.4f} val_loss={val_loss:.4f} "
            f"char_acc={char_acc:.4f} plate_acc={plate_acc:.4f} lr={learning_rate:.6f}"
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
            "output_time_steps": model.output_time_steps,
        }
        torch.save(checkpoint, output_dir / "last.pth")

        if plate_acc >= best_plate_accuracy:
            best_plate_accuracy = plate_acc
            torch.save(checkpoint, output_dir / "best.pth")

        append_history_csv(history_csv_path, epoch_record)
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
) -> float:
    model.train()
    total_loss = 0.0

    for batch_index, batch in enumerate(tqdm(data_loader, desc="train", leave=False), start=1):
        images = batch["images"].to(device)
        targets = batch["targets"].to(device)
        target_lengths = batch["target_lengths"].to(device)

        optimizer.zero_grad()
        logits = model(images)
        if logits.dim() != 3:
            raise ValueError(f"CRNN forward output must be [T, B, C], got shape {tuple(logits.shape)}")

        log_probs = logits.log_softmax(dim=2)
        input_lengths = torch.full(
            size=(images.size(0),),
            fill_value=log_probs.size(0),
            dtype=torch.long,
            device=device,
        )
        validate_ctc_lengths(
            input_lengths=input_lengths,
            target_lengths=target_lengths,
            time_steps=log_probs.size(0),
            batch_index=batch_index,
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

    for batch_index, batch in enumerate(tqdm(data_loader, desc="eval", leave=False), start=1):
        images = batch["images"].to(device)
        targets = batch["targets"].to(device)
        target_lengths = batch["target_lengths"].to(device)
        texts = batch["texts"]
        image_rel_paths = batch["image_rel_paths"]

        logits = model(images)
        if logits.dim() != 3:
            raise ValueError(f"CRNN forward output must be [T, B, C], got shape {tuple(logits.shape)}")

        log_probs = logits.log_softmax(dim=2)
        input_lengths = torch.full(
            size=(images.size(0),),
            fill_value=log_probs.size(0),
            dtype=torch.long,
            device=device,
        )
        validate_ctc_lengths(
            input_lengths=input_lengths,
            target_lengths=target_lengths,
            time_steps=log_probs.size(0),
            batch_index=batch_index,
        )

        loss = criterion(log_probs, targets, input_lengths, target_lengths)
        total_loss += loss.item()

        predictions = decode_batch_predictions(logits, charset)
        all_predictions.extend(predictions)
        all_targets.extend(texts)

        for rel_path, target_text, pred_text in zip(image_rel_paths, texts, predictions):
            if len(sample_outputs) < 10:
                sample_outputs.append((str(rel_path), str(target_text), str(pred_text)))

    char_acc, plate_acc = compute_accuracy(all_predictions, all_targets)
    return total_loss / max(len(data_loader), 1), char_acc, plate_acc, sample_outputs


def validate_ctc_lengths(
    input_lengths: torch.Tensor,
    target_lengths: torch.Tensor,
    time_steps: int,
    batch_index: int,
) -> None:
    if int(input_lengths.max().item()) > time_steps:
        raise ValueError(
            f"input_lengths exceed time_steps at batch {batch_index}: max_input_length={int(input_lengths.max().item())}, T={time_steps}"
        )
    if int(target_lengths.max().item()) > time_steps:
        raise ValueError(
            f"target_lengths exceed time_steps at batch {batch_index}: max_target_length={int(target_lengths.max().item())}, T={time_steps}"
        )


def verify_label_roundtrip(charset: CRNNCharset, text: str) -> None:
    encoded = charset.encode(text)
    decoded = charset.decode_encoded_text(encoded)
    if decoded != text:
        raise ValueError(f"Label encode/decode roundtrip failed: text={text} decoded={decoded}")
    print(f"[train_crnn] Label roundtrip OK: {text} -> {encoded} -> {decoded}")


def print_charset_debug_info(charset: CRNNCharset, train_summary, val_summary, test_summary=None) -> None:
    print("[train_crnn] Charset diagnostics:")
    print(f"  blank_index={charset.blank_index}")
    print(f"  num_classes_with_blank={charset.num_classes}")
    print(f"  charset_size_without_blank={len(charset.characters)}")
    print(f"  charset_characters={''.join(charset.characters)}")
    print("[train_crnn] Manifest diagnostics:")
    summaries = [train_summary, val_summary]
    if test_summary is not None:
        summaries.append(test_summary)
    for summary in summaries:
        print(
            f"  - manifest={summary.manifest_path} samples={summary.num_samples} "
            f"max_len={summary.max_label_length} min_len={summary.min_label_length} "
            f"avg_len={summary.avg_label_length:.2f}"
        )


def print_dataset_debug_samples(debug_records: Sequence[Dict[str, object]]) -> None:
    print("[train_crnn] Dataset debug samples:")
    for record in debug_records:
        print(
            f"  - path={record['image_rel_path']} "
            f"size={record['original_size']} resized={record['resized_size']} "
            f"label={record['label_text']} encoded={record['encoded_label']}"
        )


def save_debug_images(
    debug_records: Sequence[Dict[str, object]],
    output_dir: Path,
    count: int,
    grayscale: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    image_mode = "L" if grayscale else "RGB"
    for index, record in enumerate(debug_records[:count], start=1):
        source_path = Path(str(record["image_path"]))
        with Image.open(source_path) as image:
            image = image.convert(image_mode)
            resized_size = tuple(record["resized_size"])  # type: ignore[arg-type]
            image = image.resize(resized_size, Image.BILINEAR)
            image.save(output_dir / f"{index:02d}_{source_path.name}")


def append_history_csv(history_csv_path: Path, epoch_record: Dict[str, float]) -> None:
    with history_csv_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                int(epoch_record["epoch"]),
                f"{epoch_record['train_loss']:.6f}",
                f"{epoch_record['val_loss']:.6f}",
                f"{epoch_record['char_accuracy']:.6f}",
                f"{epoch_record['plate_accuracy']:.6f}",
                f"{epoch_record['learning_rate']:.8f}",
            ]
        )


def print_sample_predictions(samples: List[Tuple[str, str, str]]) -> None:
    if not samples:
        return
    print("[train_crnn] Sample predictions:")
    for rel_path, target_text, pred_text in samples:
        print(f"  - {rel_path}: gt={target_text} pred={pred_text}")


if __name__ == "__main__":
    raise SystemExit(main())
