"""
OFI Research Package
Order Flow Imbalance 研究工具包

一键运行：
    python -m src.ofi --config configs/data.yaml
"""

from .paths import ROOT, DATA_DIR, PROCESSED_TICKS_DIR, OFI_FEATURES_DIR, REPORTS_DIR
from .io import load_processed_day, load_ofi_features, save_ofi_features
from .features_ofi import compute_ofi_per_tick, compute_ofi_minute, aggregate_to_minute
from .clean import clean_lob_data, qc_one_day, qc_parquet_file
from .evaluate import (
    compute_ic, ic_summary, compute_quantile_returns, backtest_simple,
    regression_analysis, classification_analysis, subsample_analysis
)
from .pipeline import run_all

__version__ = "0.1.0"

__all__ = [
    "ROOT",
    "DATA_DIR", 
    "PROCESSED_TICKS_DIR",
    "OFI_FEATURES_DIR",
    "REPORTS_DIR",
    "load_processed_day",
    "load_ofi_features",
    "save_ofi_features",
    "compute_ofi_per_tick",
    "compute_ofi_minute",
    "aggregate_to_minute",
    "clean_lob_data",
    "qc_one_day",
    "qc_parquet_file",
    "compute_ic",
    "ic_summary",
    "compute_quantile_returns",
    "backtest_simple",
    "regression_analysis",
    "classification_analysis",
    "subsample_analysis",
    "run_all",
]
