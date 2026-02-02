from pathlib import Path

# .../OFI/src/ofi/paths.py -> parents[2] 就是 OFI 根目录
ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"
PROCESSED_TICKS_DIR = DATA_DIR / "processed" / "ticks"
RAW_TICKS_DIR = DATA_DIR / "raw" / "ticks"
OFI_FEATURES_DIR = DATA_DIR / "features" / "ofi_minute"
LABELS_DIR = DATA_DIR / "labels" / "minute_returns"
REPORTS_DIR = ROOT / "reports"
