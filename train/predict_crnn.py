"""Predict plate text for one image or a directory of cropped plate images."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import torch

try:
    from train.crnn_dataset import CRNNCharset
    from train.crnn_model import CRNN
except ImportError:
    from crnn_dataset import CRNNCharset
    from crnn_model import CRNN


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Predict plate text with a trained CRNN model.")
    parser.add_argument("--input", required=True, help="Single image path or directory path.")
    parser.add_argument("--checkpoint", required=True, help="Path to best.pth or another checkpoint.")
    parser.add_argument("--device", default="cuda:0", help="Prediction device.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    device = torch.device(args.device if torch.cuda.is_available() or args.device == "cpu" else "cpu")
    checkpoint = torch.load(Path(args.checkpoint).resolve(), map_location=device)
    charset = CRNNCharset(checkpoint["charset"])

    model = CRNN(
        img_height=int(checkpoint["img_height"]),
        img_width=int(checkpoint["img_width"]),
        num_channels=1 if bool(checkpoint["grayscale"]) else 3,
        num_classes=charset.num_classes,
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    input_path = Path(args.input).resolve()
    image_paths = collect_image_paths(input_path)
    for image_path in image_paths:
        prediction = predict_single_image(
            model=model,
            image_path=image_path,
            charset=charset,
            img_height=int(checkpoint["img_height"]),
            img_width=int(checkpoint["img_width"]),
            grayscale=bool(checkpoint["grayscale"]),
            device=device,
        )
        print(f"{image_path}\t{prediction}")
    return 0


def collect_image_paths(input_path: Path) -> List[Path]:
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        paths = sorted(path for path in input_path.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)
        if not paths:
            raise FileNotFoundError(f"No image files found under directory: {input_path}")
        return paths
    raise FileNotFoundError(f"Input path does not exist: {input_path}")


@torch.no_grad()
def predict_single_image(
    model: CRNN,
    image_path: Path,
    charset: CRNNCharset,
    img_height: int,
    img_width: int,
    grayscale: bool,
    device: torch.device,
) -> str:
    from PIL import Image
    import numpy as np

    image_mode = "L" if grayscale else "RGB"
    with Image.open(image_path) as image:
        image = image.convert(image_mode)
        image = image.resize((img_width, img_height), Image.BILINEAR)
        array = np.asarray(image, dtype=np.float32) / 255.0

    if grayscale:
        array = array[None, :, :]
    else:
        array = np.transpose(array, (2, 0, 1))

    image_tensor = torch.from_numpy(array).unsqueeze(0).to(device)
    logits = model(image_tensor)
    indices = logits.argmax(dim=2).squeeze(1).cpu().tolist()
    return charset.decode_indices(indices)


if __name__ == "__main__":
    raise SystemExit(main())
