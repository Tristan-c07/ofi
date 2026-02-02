"""
OFI (Order Flow Imbalance) 特征计算
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List


def _col(level: int, side: str, kind: str) -> str:
    """生成列名：b1_p, a2_v 等"""
    return f"{side}{level}_{kind}"


def ensure_datetime_index(df: pd.DataFrame, time_col: str = None) -> pd.DataFrame:
    """
    确保DataFrame有datetime索引
    
    Args:
        df: 输入DataFrame
        time_col: 时间列名，如果为None则自动检测 'time' 或 'ts'
    
    Returns:
        带datetime索引的DataFrame
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
    计算每个tick的OFI（Order Flow Imbalance）
    
    基于价格和量的变化计算OFI：
    - 买方OFI (Δb): 如果bid价格上升，加买量；价格不变，加买量变化；价格下降，减前一tick买量
    - 卖方OFI (Δa): 如果ask价格下降，加卖量；价格不变，加卖量变化；价格上升，减前一tick卖量
    - OFI_i = Δb_i - Δa_i
    
    Args:
        df: 输入DataFrame，需要包含 b{i}_p, b{i}_v, a{i}_p, a{i}_v 列
        levels: 使用的深度档位，默认5档
    
    Returns:
        添加了 ofi1, ofi2, ..., ofi{levels}, ofi 列的DataFrame
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

        # Δb_i: 买方订单流变化
        db = np.where(
            bp > bp_prev, bv,
            np.where(bp == bp_prev, bv - bv_prev, -bv_prev)
        )

        # Δa_i: 卖方订单流变化
        da = np.where(
            ap < ap_prev, av,
            np.where(ap == ap_prev, av - av_prev, -av_prev)
        )

        ofi_i = db - da
        out[f"ofi{i}"] = ofi_i

    # 汇总所有档位的OFI
    ofi_cols: List[str] = [f"ofi{i}" for i in range(1, levels + 1)]
    out["ofi"] = out[ofi_cols].sum(axis=1, skipna=True)

    # 第一行填 0.0（因为没有前一tick）
    out[ofi_cols + ["ofi"]] = out[ofi_cols + ["ofi"]].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return out


def compute_ofi_minute(
    df: pd.DataFrame, 
    levels: int = 5,
    add_features: bool = True
) -> pd.DataFrame:
    """
    计算分钟级别OFI特征
    
    流程：
    1. 计算tick级别OFI
    2. 按分钟聚合
    3. 可选：添加额外特征（mid、spread、tick数量等）
    
    Args:
        df: tick级别的LOB数据
        levels: OFI计算使用的档位数
        add_features: 是否添加额外特征
    
    Returns:
        分钟级别的OFI特征DataFrame
    """
    # 确保有时间索引
    if not isinstance(df.index, pd.DatetimeIndex):
        df = ensure_datetime_index(df)
    
    # 计算tick级别OFI
    df_ofi = compute_ofi_per_tick(df, levels=levels)
    
    # 分钟聚合
    df_ofi["minute"] = df_ofi.index.floor("min")
    
    ofi_cols = [f"ofi{i}" for i in range(1, levels + 1)] + ["ofi"]
    
    # 基础聚合：OFI求和
    result = df_ofi.groupby("minute")[ofi_cols].sum()
    
    if add_features:
        # 添加额外特征
        g = df_ofi.groupby("minute")
        
        # 中间价和价差
        mid = (df_ofi["a1_p"] + df_ofi["b1_p"]) / 2.0
        spread = df_ofi["a1_p"] - df_ofi["b1_p"]
        
        result["mid_last"] = g.apply(lambda x: mid.loc[x.index].iloc[-1])
        result["spread_mean"] = g.apply(lambda x: spread.loc[x.index].mean())
        result["spread_median"] = g.apply(lambda x: spread.loc[x.index].median())
        result["n_ticks"] = g.size()
    
    return result


def aggregate_to_minute(
    ofi_tick: pd.DataFrame, 
    bar: str = "1min", 
    agg: str = "sum"
) -> pd.DataFrame:
    """
    将tick级别OFI聚合到指定时间周期
    
    Args:
        ofi_tick: 包含OFI列的tick数据
        bar: 时间周期，如 "1min", "5min"
        agg: 聚合方式，"sum" 或 "mean"
    
    Returns:
        聚合后的DataFrame
    """
    cols = [c for c in ofi_tick.columns if c.startswith("ofi")]
    
    if agg == "sum":
        res = ofi_tick[cols].resample(bar).sum()
    elif agg == "mean":
        res = ofi_tick[cols].resample(bar).mean()
    else:
        raise ValueError(f"Unsupported agg={agg}")

    res = res.dropna(how="all")
    return res
