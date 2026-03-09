# speech_module.py
# Train + infer a Dysarthria (speech) classifier from the Kaggle dataset.
# Output: speech_risk in [0,1] = P(dysarthria)

import argparse
import os
from pathlib import Path
import random
from typing import Tuple
import soundfile as sf


import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

import librosa


# -----------------------------
# Reproducibility
# -----------------------------
def seed_all(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


# -----------------------------
# Feature extraction (MFCC)
# -----------------------------
def extract_mfcc(
    wav_path: str,
    sr: int = 16000,
    n_mfcc: int = 40,
    seconds: float = 3.0,
) -> np.ndarray:
    # Load using soundfile (works with your converted PCM wavs)
    y, native_sr = sf.read(wav_path, dtype="float32", always_2d=False)

    # stereo -> mono
    if isinstance(y, np.ndarray) and y.ndim == 2:
        y = y.mean(axis=1)

    # resample if needed
    if native_sr != sr:
        y = librosa.resample(y, orig_sr=native_sr, target_sr=sr)

    target_len = int(sr * seconds)
    if len(y) < target_len:
        y = np.pad(y, (0, target_len - len(y)))
    else:
        y = y[:target_len]

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    return mfcc.astype(np.float32)


def normalize_mfcc(mfcc: np.ndarray) -> np.ndarray:
    """
    Per-sample normalization. Keeps training stable across loudness differences.
    """
    mu = mfcc.mean()
    sigma = mfcc.std() + 1e-6
    return (mfcc - mu) / sigma


# -----------------------------
# Dataset
# -----------------------------
LABEL_MAP = {"non_dysarthria": 0, "dysarthria": 1}


class DysarthriaDataset(Dataset):
    def __init__(self, df: pd.DataFrame, root_dir: Path, audio_root: Path, sr=16000, n_mfcc=40, seconds=3.0):
        
        self.audio_root = audio_root

        self.df = df.reset_index(drop=True)
        self.root_dir = root_dir
        self.sr = sr
        self.n_mfcc = n_mfcc
        self.seconds = seconds

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx: int):
        row = self.df.iloc[idx]
        label_str = row["is_dysarthria"]
        y = LABEL_MAP[label_str]

        # filenames in CSV already include "torgo_data/..."
       # CSV has: torgo_data/<subdir>/<file.wav>
        rel = Path(row["filename"])
        if len(rel.parts) > 0 and rel.parts[0].lower() == "torgo_data":
            rel = Path(*rel.parts[1:])

        wav_path = self.audio_root / rel
        wav_path = str(wav_path)


        mfcc = extract_mfcc(wav_path, sr=self.sr, n_mfcc=self.n_mfcc, seconds=self.seconds)
        mfcc = normalize_mfcc(mfcc)

        # CNN expects NCHW, we provide CHW per sample
        x = torch.from_numpy(mfcc).unsqueeze(0)  # (1, n_mfcc, T)
        y = torch.tensor(y, dtype=torch.long)
        return x, y


# -----------------------------
# Model (small CNN)
# -----------------------------
class SmallCNN(nn.Module):
    def __init__(self, n_classes=2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),

            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.fc = nn.Linear(64, n_classes)

    def forward(self, x):
        x = self.net(x)
        x = x.flatten(1)
        return self.fc(x)


# -----------------------------
# Train/val utilities
# -----------------------------
@torch.no_grad()
def evaluate(model, loader, device) -> Tuple[float, float]:
    model.eval()
    correct = 0
    total = 0
    loss_sum = 0.0
    loss_fn = nn.CrossEntropyLoss()

    for x, y in loader:
        x, y = x.to(device), y.to(device)
        logits = model(x)
        loss = loss_fn(logits, y)
        loss_sum += float(loss.item()) * y.size(0)

        preds = logits.argmax(dim=1)
        correct += int((preds == y).sum().item())
        total += int(y.size(0))

    avg_loss = loss_sum / max(1, total)
    acc = correct / max(1, total)
    return avg_loss, acc


def train_one_epoch(model, loader, device, optimizer) -> Tuple[float, float]:
    model.train()
    loss_fn = nn.CrossEntropyLoss()
    loss_sum = 0.0
    correct = 0
    total = 0

    for x, y in loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        logits = model(x)
        loss = loss_fn(logits, y)
        loss.backward()
        optimizer.step()

        loss_sum += float(loss.item()) * y.size(0)
        preds = logits.argmax(dim=1)
        correct += int((preds == y).sum().item())
        total += int(y.size(0))

    return (loss_sum / max(1, total)), (correct / max(1, total))


def stratified_split(df: pd.DataFrame, val_frac=0.2, seed=42):
    # simple stratified split by label
    rng = np.random.default_rng(seed)
    dfs = []
    for label in df["is_dysarthria"].unique():
        sub = df[df["is_dysarthria"] == label].copy()
        idx = np.arange(len(sub))
        rng.shuffle(idx)
        cut = int(len(sub) * (1.0 - val_frac))
        train_idx = idx[:cut]
        val_idx = idx[cut:]
        dfs.append((sub.iloc[train_idx], sub.iloc[val_idx]))
    train_df = pd.concat([x[0] for x in dfs]).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    val_df = pd.concat([x[1] for x in dfs]).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return train_df, val_df


# -----------------------------
# Inference: wav -> speech_risk
# -----------------------------
@torch.no_grad()
def speech_risk(model_path: str, wav_path: str, device: str = "cpu",
                sr: int = 16000, n_mfcc: int = 40, seconds: float = 3.0) -> float:
    model = SmallCNN(n_classes=2).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    mfcc = extract_mfcc(wav_path, sr=sr, n_mfcc=n_mfcc, seconds=seconds)
    mfcc = normalize_mfcc(mfcc)
    x = torch.from_numpy(mfcc).unsqueeze(0).unsqueeze(0).to(device)  # (1,1,n_mfcc,T)

    logits = model(x)
    prob = torch.softmax(logits, dim=1)[0, 1].item()  # P(dysarthria)
    return float(prob)


# -----------------------------
# Main CLI
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, required=True, help="Dataset root folder containing torgo_data_pcm16k/")
    ap.add_argument("--csv", type=str, default="torgo_data/data.csv", help="CSV path relative to root")
    ap.add_argument("--mode", type=str, choices=["train", "infer"], required=True)
    ap.add_argument("--out", type=str, default="speech_cnn.pt", help="Where to save/load model")
    ap.add_argument("--audio_root", type=str, default="torgo_pcm16k", help="Audio root folder (relative to --root)")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--sr", type=int, default=16000)
    ap.add_argument("--n_mfcc", type=int, default=40)
    ap.add_argument("--seconds", type=float, default=3.0)
    ap.add_argument("--infer_wav", type=str, default=None, help="Wav path for infer mode")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    seed_all(args.seed)

    root_dir = Path(args.root)
    csv_path = root_dir / args.csv
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    audio_root = root_dir / args.audio_root
    if not audio_root.exists():
        raise FileNotFoundError(f"Audio root not found: {audio_root}")

    if args.mode == "train":
        df = pd.read_csv(csv_path)
        # Safety checks
        if not set(["is_dysarthria", "gender", "filename"]).issubset(df.columns):
            raise RuntimeError(f"Unexpected CSV columns: {df.columns.tolist()}")

        train_df, val_df = stratified_split(df, val_frac=0.2, seed=args.seed)

        train_ds = DysarthriaDataset(train_df, root_dir, audio_root, sr=args.sr, n_mfcc=args.n_mfcc, seconds=args.seconds)
        val_ds   = DysarthriaDataset(val_df, root_dir, audio_root, sr=args.sr, n_mfcc=args.n_mfcc, seconds=args.seconds)


        train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True, num_workers=0)
        val_loader = DataLoader(val_ds, batch_size=args.batch, shuffle=False, num_workers=0)

        model = SmallCNN(n_classes=2).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

        best_val_acc = -1.0
        for epoch in range(1, args.epochs + 1):
            tr_loss, tr_acc = train_one_epoch(model, train_loader, device, optimizer)
            va_loss, va_acc = evaluate(model, val_loader, device)

            print(f"Epoch {epoch:02d}/{args.epochs} | "
                  f"train loss {tr_loss:.4f} acc {tr_acc:.4f} | "
                  f"val loss {va_loss:.4f} acc {va_acc:.4f}")

            if va_acc > best_val_acc:
                best_val_acc = va_acc
                torch.save(model.state_dict(), args.out)
                print(f"Saved best model -> {args.out} (val acc {best_val_acc:.4f})")

        print(f"Done. Best val acc: {best_val_acc:.4f}")
        return

    # Infer
    if args.infer_wav is None:
        raise ValueError("--infer_wav is required in infer mode")

    model_path = Path(args.out)
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    prob = speech_risk(
        model_path=str(model_path),
        wav_path=args.infer_wav,
        device=device,
        sr=args.sr,
        n_mfcc=args.n_mfcc,
        seconds=args.seconds,
    )

    print({"speech_risk": round(prob, 4), "model": str(model_path), "wav": args.infer_wav})


if __name__ == "__main__":
    main()
