from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List


def _col(level: int, side: str, kind: str) -> str:
    return f"{side}{level}_{kind}"


def ensure_datetime_index(df: pd.DataFrame, time_col: str = None) -> pd.DataFrame:
    """
    确保DataFrame有datetime索引
    
    Args:
        df: 输入DataFrame
        time_col: 时间列名，如果为None则自动检测 'time' 或 'ts'
    """
    out = df.copy()
    
    # 自动检测时间列
    if time_col is None:
        if "ts" in out.columns:
            time_col = "ts"
        elif "time" in out.columns:
            time_col = "time"
        else:
            raise ValueError("No time column found. Expected 'time' or 'ts'")
    
    # 如果不是 datetime 类型，则转换
    if not pd.api.types.is_datetime64_any_dtype(out[time_col]):
        out[time_col] = pd.to_datetime(out[time_col], errors="coerce")
    
    out = out.dropna(subset=[time_col]).sort_values(time_col)
    out = out.set_index(time_col)
    return out


def compute_ofi_per_tick(df: pd.DataFrame, levels: int = 5) -> pd.DataFrame:
    """
    输出：添加列 ofi1..ofi{levels} 以及 ofi（sum）
    """
    out = df.copy()

    for i in range(1, levels + 1):
        bp = out[_col(i, "b", "p")].astype(float)
        ap = out[_col(i, "a", "p")].astype(float)
        bv = out[_col(i, "b", "v")].astype(float)
        av = out[_col(i, "a", "v")].astype(float)

        bp_prev = bp.shift(1)
        ap_prev = ap.shift(1)
        bv_prev = bv.shift(1)
        av_prev = av.shift(1)

        # Δb_i
        db = np.where(
            bp > bp_prev, bv,
            np.where(bp == bp_prev, bv - bv_prev, -bv_prev)
        )

        # Δa_i
        da = np.where(
            ap < ap_prev, av,
            np.where(ap == ap_prev, av - av_prev, -av_prev)
        )

        ofi_i = db - da
        out[f"ofi{i}"] = ofi_i

    ofi_cols: List[str] = [f"ofi{i}" for i in range(1, levels + 1)]
    out["ofi"] = out[ofi_cols].sum(axis=1, skipna=True)

    # 第一行填 0.0
    out[ofi_cols + ["ofi"]] = out[ofi_cols + ["ofi"]].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return out


def aggregate_to_minute(ofi_tick: pd.DataFrame, bar: str = "1min", agg: str = "sum") -> pd.DataFrame:
    
    cols = [c for c in ofi_tick.columns if c.startswith("ofi")]
    if agg == "sum":
        res = ofi_tick[cols].resample(bar).sum()
    elif agg == "mean":
        res = ofi_tick[cols].resample(bar).mean()
    else:
        raise ValueError(f"Unsupported agg={agg}")

    res = res.dropna(how="all")
    return res
