"""
handwriting_twostep.py

Two-step inference for your YOLOv8 handwriting model:
1) Crop to ink region (no ML).
2) Upscale if small.
3) Normalize polarity (optional, helps when training/test are inverted).
4) YOLO predict.
5) Score = (Reversal + Corrected) / total detections.

Usage (PowerShell / CMD):
  python handwriting_twostep.py --model "runs/detect/train/weights/best.pt" --source "path/to/image.jpg"
  python handwriting_twostep.py --model "models/best.pt" --source "path/to/folder" --save_vis

Recommended for tough real photos:
  python handwriting_twostep.py --model ".../best.pt" --source "test-1.jpg" --conf 0.05 --imgsz 1280 --save_vis

Outputs:
- Prints risk + counts
- Optionally saves annotated crop images under ./outputs_vis/
"""

import argparse
from pathlib import Path
from collections import Counter

import cv2
import numpy as np
from ultralytics import YOLO


# ----------------------------
# Config defaults (edit if you want)
# ----------------------------
DEFAULT_CLASS_NAMES = ["Normal", "Reversal", "Corrected"]  # must match your data.yaml order
CLASS_NORMAL = 0
CLASS_REVERSAL = 1
CLASS_CORRECTED = 2

DEFAULT_CONF = 0.10     # lower for real photos than your usual 0.25
DEFAULT_IMGSZ = 1024    # higher than 640 helps small letters
DEFAULT_MIN_SIDE_UPSCALE_TO = 900  # make crop at least this big on smallest side if small

DEFAULT_PAD = 20
DEFAULT_MIN_AREA_FRAC = 0.02  # if detected ink region < 2% image area, skip crop

# Polarity normalization: if image is mostly bright background, invert to match "white ink on dark"
DEFAULT_NORMALIZE_POLARITY = True


# ----------------------------
# Polarity normalization
# ----------------------------
def normalize_polarity_if_needed(bgr: np.ndarray, enabled: bool = True):
    """
    If enabled and the image background is mostly bright (mean gray > 127),
    invert it so strokes become bright on dark background.
    Returns: (bgr_out, inverted_bool)
    """
    if not enabled:
        return bgr, False

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    if float(np.mean(gray)) > 127.0:
        inv = 255 - gray
        out = cv2.cvtColor(inv, cv2.COLOR_GRAY2BGR)
        return out, True

    return bgr, False


# ----------------------------
# Preprocessing: crop to ink region
# ----------------------------
def crop_to_ink_region(bgr: np.ndarray, pad: int = DEFAULT_PAD, min_area_frac: float = DEFAULT_MIN_AREA_FRAC):
    """
    Finds the largest 'ink' region and crops to it.
    Returns: (cropped_bgr, bbox=(x0,y0,x1,y1) in original coords, used_crop: bool)
    """
    H, W = bgr.shape[:2]
    full_bbox = (0, 0, W, H)

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Improve local contrast for faint strokes
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # Ink extraction: ink is darker than paper -> invert threshold => ink becomes white
    thr = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31, 7
    )

    # Connect strokes and remove specks
    k = np.ones((3, 3), np.uint8)
    thr = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, k, iterations=2)
    thr = cv2.morphologyEx(thr, cv2.MORPH_OPEN, k, iterations=1)

    contours, _ = cv2.findContours(thr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return bgr, full_bbox, False

    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    if area < (min_area_frac * H * W):
        return bgr, full_bbox, False

    x, y, w, h = cv2.boundingRect(c)
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(W, x + w + pad)
    y1 = min(H, y + h + pad)

    cropped = bgr[y0:y1, x0:x1]
    return cropped, (x0, y0, x1, y1), True


def upscale_if_small(bgr: np.ndarray, min_side: int = DEFAULT_MIN_SIDE_UPSCALE_TO):
    """
    Upscales image if its smaller side is < min_side.
    Returns: (resized_bgr, scale_factor)
    """
    h, w = bgr.shape[:2]
    m = min(h, w)
    if m >= min_side:
        return bgr, 1.0

    scale = float(min_side) / float(m)
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))
    out = cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    return out, scale


# ----------------------------
# Scoring
# ----------------------------
def score_from_result(res, class_names=None):
    """
    res: ultralytics Result
    returns dict with risk + counts + total
    """
    if class_names is None:
        class_names = DEFAULT_CLASS_NAMES

    if res.boxes is None or len(res.boxes) == 0:
        return {
            "risk": 0.0,
            "counts": {name: 0 for name in class_names},
            "total": 0,
        }

    cls_ids = [int(c) for c in res.boxes.cls.tolist()]
    counts = Counter(cls_ids)
    total = sum(counts.values())

    named = {name: counts.get(i, 0) for i, name in enumerate(class_names)}

    reversal = counts.get(CLASS_REVERSAL, 0)
    corrected = counts.get(CLASS_CORRECTED, 0)
    risk = (reversal + corrected) / total if total > 0 else 0.0

    return {
        "risk": float(risk),
        "counts": named,
        "total": int(total),
    }


# ----------------------------
# Inference
# ----------------------------
def run_on_image(model: YOLO, img_path: Path, conf: float, imgsz: int, save_vis: bool, out_dir: Path,
                 normalize_polarity: bool):
    bgr = cv2.imread(str(img_path))
    if bgr is None:
        return {"image": str(img_path), "error": "Could not read image"}

    # Step A: crop to ink region
    crop_bgr, bbox, used_crop = crop_to_ink_region(bgr)

    # Step B: upscale crop if small
    crop_bgr, scale = upscale_if_small(crop_bgr)

    # Step C: normalize polarity if needed
    crop_bgr, inverted = normalize_polarity_if_needed(crop_bgr, enabled=normalize_polarity)

    # Step D: YOLO predict (on numpy image)
    res = model.predict(crop_bgr, conf=conf, imgsz=imgsz, verbose=False)[0]

    # Step E: score
    out = score_from_result(res, DEFAULT_CLASS_NAMES)
    out.update({
        "image": str(img_path),
        "used_crop": bool(used_crop),
        "crop_bbox_original": bbox,
        "crop_upscale_factor": float(scale),
        "polarity_inverted": bool(inverted),
        "conf": float(conf),
        "imgsz": int(imgsz),
    })

    if save_vis:
        out_dir.mkdir(parents=True, exist_ok=True)
        annotated = res.plot()  # BGR image with boxes/labels
        save_path = out_dir / f"{img_path.stem}_annotated_crop.jpg"
        cv2.imwrite(str(save_path), annotated)
        out["annotated_crop_path"] = str(save_path)

    return out


def iter_images(source: Path):
    exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    if source.is_file():
        yield source
        return
    for p in sorted(source.rglob("*")):
        if p.suffix.lower() in exts:
            yield p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="Path to YOLOv8 weights (best.pt)")
    ap.add_argument("--source", required=True, help="Path to an image or folder of images")
    ap.add_argument("--conf", type=float, default=DEFAULT_CONF, help="Confidence threshold (try 0.05–0.25)")
    ap.add_argument("--imgsz", type=int, default=DEFAULT_IMGSZ, help="Inference image size (try 640–1280)")
    ap.add_argument("--save_vis", action="store_true", help="Save annotated crop images")
    ap.add_argument("--out_dir", default="outputs_vis", help="Where to save visualizations")

    ap.add_argument(
        "--normalize_polarity",
        action="store_true",
        help="Invert black-on-white inputs to match white-on-dark training style (recommended)."
    )
    ap.add_argument(
        "--no_normalize_polarity",
        action="store_true",
        help="Disable polarity normalization."
    )

    args = ap.parse_args()

    model_path = Path(args.model)
    source = Path(args.source)
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not source.exists():
        raise FileNotFoundError(f"Source not found: {source}")

    # Polarity normalization flag logic
    if args.no_normalize_polarity:
        normalize_polarity = False
    elif args.normalize_polarity:
        normalize_polarity = True
    else:
        normalize_polarity = DEFAULT_NORMALIZE_POLARITY

    model = YOLO(str(model_path))
    out_dir = Path(args.out_dir)

    results = []
    for img in iter_images(source):
        r = run_on_image(
            model, img,
            conf=args.conf,
            imgsz=args.imgsz,
            save_vis=args.save_vis,
            out_dir=out_dir,
            normalize_polarity=normalize_polarity
        )
        results.append(r)
        print(r)

    if source.is_dir():
        detected = [r for r in results if "error" not in r and r.get("total", 0) > 0]
        if detected:
            avg_risk = sum(r["risk"] for r in detected) / len(detected)
            print("\nSUMMARY")
            print(f"Images processed: {len(results)}")
            print(f"Images with detections: {len(detected)}")
            print(f"Average risk (detections only): {avg_risk:.4f}")
        else:
            print("\nSUMMARY")
            print(f"Images processed: {len(results)}")
            print("No detections on any image. Try --conf 0.05 --imgsz 1280, and ensure polarity normalization is on.")


if __name__ == "__main__":
    main()
