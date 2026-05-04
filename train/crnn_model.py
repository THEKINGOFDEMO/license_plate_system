"""CRNN model definition for plate character recognition."""

from __future__ import annotations

import torch
from torch import nn


class BidirectionalLSTM(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, output_size: int) -> None:
        super().__init__()
        self.rnn = nn.LSTM(input_size, hidden_size, bidirectional=True)
        self.embedding = nn.Linear(hidden_size * 2, output_size)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        recurrent, _ = self.rnn(inputs)
        time_steps, batch_size, hidden_size = recurrent.size()
        output = self.embedding(recurrent.view(time_steps * batch_size, hidden_size))
        return output.view(time_steps, batch_size, -1)


class CRNN(nn.Module):
    """CNN + BiLSTM recognizer for license plate text."""

    def __init__(
        self,
        img_height: int,
        img_width: int,
        num_channels: int,
        num_classes: int,
        hidden_size: int = 256,
    ) -> None:
        super().__init__()
        if img_height <= 0 or img_width <= 0:
            raise ValueError("img_height and img_width must be positive.")

        # Keep width downsampling moderate so the output time steps remain
        # comfortably above the 7-8 characters expected in CCPD labels.
        self.cnn = nn.Sequential(
            nn.Conv2d(num_channels, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # H/2, W/2
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # H/4, W/4
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),  # H/8, W/4
            nn.Conv2d(256, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),  # H/16, W/4
            nn.Conv2d(512, 512, kernel_size=(2, 1), stride=1, padding=0),  # H->1, keep W
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
        )

        with torch.no_grad():
            dummy = torch.zeros(1, num_channels, img_height, img_width)
            features = self.cnn(dummy)
            _, channels, feature_height, feature_width = features.shape
            self.sequence_feature_dim = channels * feature_height
            self.output_time_steps = feature_width

        self.sequence_projection = nn.Linear(self.sequence_feature_dim, hidden_size)
        self.rnn = nn.Sequential(
            BidirectionalLSTM(hidden_size, hidden_size, hidden_size),
            BidirectionalLSTM(hidden_size, hidden_size, num_classes),
        )

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        features = self.cnn(images)
        batch_size, channels, feature_height, feature_width = features.size()
        features = features.permute(3, 0, 1, 2).contiguous()
        features = features.view(feature_width, batch_size, channels * feature_height)
        features = self.sequence_projection(features)
        return self.rnn(features)
