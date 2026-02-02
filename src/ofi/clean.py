"""
LOB数据清洗和质量检查
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd


PX_COLS = [f"a{k}_p" for k in range(1, 6)] + [f"b{k}_p" for k in range(1, 6)]
VOL_COLS = [f"a{k}_v" for k in range(1, 6)] + [f"b{k}_v" for k in range(1, 6)]


def clean_lob_data(
    df: pd.DataFrame,
    remove_zero_price: bool = True,
    remove_crossed: bool = True,
    remove_duplicates: bool = True,
    remove_outliers: bool = True,
    outlier_threshold: float = 0.1  # 相对价格变动阈值
) -> pd.DataFrame:
    """
    清洗LOB数据
    
    Args:
        df: 原始LOB数据
        remove_zero_price: 是否移除价格为0或负的行
        remove_crossed: 是否移除交叉盘口（bid >= ask）
        remove_duplicates: 是否移除重复时间戳
        remove_outliers: 是否移除异常价格跳动
        outlier_threshold: 异常价格变动阈值（相对变化）
    
    Returns:
        清洗后的DataFrame
    """
    out = df.copy()
    n_orig = len(out)
    
    # 1. 移除价格 <= 0 的行
    if remove_zero_price:
        price_cols = [c for c in out.columns if c.endswith("_p")]
        bad_price = (out[price_cols] <= 0).any(axis=1) | out[price_cols].isna().any(axis=1)
        out = out[~bad_price]
    
    # 2. 移除交叉盘口
    if remove_crossed:
        crossed = out["a1_p"] <= out["b1_p"]
        out = out[~crossed]
    
    # 3. 移除重复时间戳（保留最后一个）
    if remove_duplicates:
        if "ts" in out.columns:
            out = out.drop_duplicates(subset=["ts"], keep="last")
        elif out.index.name == "ts" or isinstance(out.index, pd.DatetimeIndex):
            out = out[~out.index.duplicated(keep="last")]
    
    # 4. 移除异常价格跳动
    if remove_outliers and len(out) > 0:
        mid = (out["a1_p"] + out["b1_p"]) / 2.0
        mid_ret = mid.pct_change().abs()
        outlier_mask = mid_ret > outlier_threshold
        out = out[~outlier_mask]
    
    n_final = len(out)
    removed = n_orig - n_final
    
    if removed > 0:
        print(f"Cleaned: removed {removed}/{n_orig} rows ({removed/n_orig*100:.2f}%)")
    
    return out


def qc_one_day(df: pd.DataFrame) -> dict:
    """
    对单日LOB数据进行质量检查
    
    Args:
        df: 单日LOB数据
    
    Returns:
        质量指标字典
    """
    if len(df) == 0:
        return {
            "n_rows": 0,
            "dup_ts_ratio": 0,
            "crossed_ratio": 0,
            "bad_price_cnt": 0,
            "spread_median": np.nan,
            "rel_spread_median": np.nan,
        }
    
    n = len(df)
    
    # 重复时间戳比例
    if "ts" in df.columns:
        dup_ratio = df["ts"].duplicated().mean()
    elif isinstance(df.index, pd.DatetimeIndex):
        dup_ratio = df.index.duplicated().mean()
    else:
        dup_ratio = 0
    
    # 交叉盘口比例
    a1 = df["a1_p"]
    b1 = df["b1_p"]
    crossed_ratio = (a1 <= b1).mean()
    
    # 异常价格数量
    px = df[[c for c in PX_COLS if c in df.columns]]
    bad_price_cnt = int(((px <= 0) | px.isna()).any(axis=1).sum())
    
    # 价差统计
    mid = (a1 + b1) / 2.0
    spread = a1 - b1
    spread_median = float(np.nanmedian(spread))
    rel_spread_median = float(np.nanmedian(spread / mid))
    
    return {
        "n_rows": n,
        "dup_ts_ratio": float(dup_ratio),
        "crossed_ratio": float(crossed_ratio),
        "bad_price_cnt": bad_price_cnt,
        "spread_median": spread_median,
        "rel_spread_median": rel_spread_median,
    }


def qc_parquet_file(pq_path: Path) -> dict:
    """
    对parquet文件进行质量检查
    
    Args:
        pq_path: parquet文件路径
    
    Returns:
        质量指标字典（包含文件信息）
    """
    df = pd.read_parquet(pq_path)
    
    qc = qc_one_day(df)
    
    # 添加文件信息
    if "code" in df.columns and len(df) > 0:
        qc["symbol"] = str(df["code"].iloc[0])
    
    if "date" in df.columns and len(df) > 0:
        qc["date"] = str(df["date"].iloc[0])
    
    if "ts" in df.columns and len(df) > 0:
        qc["ts_min"] = df["ts"].min()
        qc["ts_max"] = df["ts"].max()
    
    # 检查截断标记
    if "maybe_truncated" in df.columns:
        mt_ratio = float(np.nanmean(
            pd.to_numeric(df["maybe_truncated"], errors="coerce") > 0
        ))
        qc["maybe_truncated_ratio"] = mt_ratio
    
    qc["file"] = str(pq_path)
    
    return qc
