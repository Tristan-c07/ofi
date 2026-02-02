"""
OFI信号评估模块
包含完整的统计分析、预测建模和稳健性检验
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy import stats
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


def compute_ic(
    features: pd.DataFrame, 
    labels: pd.DataFrame,
    method: str = "spearman"
) -> pd.Series:
    """
    计算信息系数（IC）
    
    Args:
        features: 特征DataFrame，索引为时间
        labels: 标签DataFrame，索引为时间
        method: 相关系数方法，"pearson" 或 "spearman"
    
    Returns:
        每个时间点的IC值Series
    """
    # 对齐数据
    common_idx = features.index.intersection(labels.index)
    
    if len(common_idx) == 0:
        return pd.Series(dtype=float)
    
    feat = features.loc[common_idx]
    lab = labels.loc[common_idx]
    
    # 逐时间点计算相关系数
    ic_list = []
    
    for idx in common_idx:
        f = feat.loc[idx] if isinstance(feat.loc[idx], pd.Series) else feat.loc[[idx]].values.flatten()
        l = lab.loc[idx] if isinstance(lab.loc[idx], pd.Series) else lab.loc[[idx]].values.flatten()
        
        # 移除NaN
        mask = ~(np.isnan(f) | np.isnan(l))
        if mask.sum() < 2:
            ic_list.append(np.nan)
            continue
        
        f_clean = f[mask]
        l_clean = l[mask]
        
        if method == "spearman":
            ic, _ = stats.spearmanr(f_clean, l_clean)
        elif method == "pearson":
            ic, _ = stats.pearsonr(f_clean, l_clean)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        ic_list.append(ic)
    
    return pd.Series(ic_list, index=common_idx)


def compute_rank_ic(
    signal: pd.Series,
    returns: pd.Series
) -> float:
    """
    计算单期Rank IC
    
    Args:
        signal: 信号值
        returns: 收益率
    
    Returns:
        Spearman相关系数
    """
    # 对齐并移除NaN
    df = pd.DataFrame({"signal": signal, "returns": returns}).dropna()
    
    if len(df) < 2:
        return np.nan
    
    ic, _ = stats.spearmanr(df["signal"], df["returns"])
    return ic


def ic_summary(ic_series: pd.Series) -> Dict[str, float]:
    """
    IC统计摘要
    
    Args:
        ic_series: IC时间序列
    
    Returns:
        统计指标字典
    """
    ic_clean = ic_series.dropna()
    
    if len(ic_clean) == 0:
        return {
            "mean": np.nan,
            "std": np.nan,
            "ir": np.nan,
            "win_rate": np.nan,
            "count": 0,
        }
    
    mean_ic = ic_clean.mean()
    std_ic = ic_clean.std()
    ir = mean_ic / std_ic if std_ic > 0 else np.nan
    win_rate = (ic_clean > 0).mean()
    
    return {
        "mean": mean_ic,
        "std": std_ic,
        "ir": ir,
        "win_rate": win_rate,
        "count": len(ic_clean),
    }


def compute_quantile_returns(
    signal: pd.Series,
    returns: pd.Series,
    n_quantiles: int = 5
) -> pd.DataFrame:
    """
    分位数收益分析
    
    Args:
        signal: 信号值
        returns: 收益率
        n_quantiles: 分位数数量
    
    Returns:
        每个分位数的统计DataFrame
    """
    df = pd.DataFrame({"signal": signal, "returns": returns}).dropna()
    
    if len(df) == 0:
        return pd.DataFrame()
    
    # 分位数标签
    df["quantile"] = pd.qcut(df["signal"], n_quantiles, labels=False, duplicates="drop")
    
    # 按分位数聚合
    result = df.groupby("quantile").agg({
        "returns": ["mean", "std", "count"],
        "signal": ["mean", "min", "max"]
    })
    
    result.columns = ["_".join(col).strip() for col in result.columns]
    result = result.reset_index()
    result["quantile"] = result["quantile"] + 1  # 从1开始
    
    return result


def compute_long_short_returns(
    signal: pd.Series,
    returns: pd.Series,
    top_pct: float = 0.2,
    bottom_pct: float = 0.2
) -> Dict[str, float]:
    """
    多空组合收益分析
    
    Args:
        signal: 信号值
        returns: 收益率
        top_pct: 做多的头部百分比
        bottom_pct: 做空的尾部百分比
    
    Returns:
        多空统计字典
    """
    df = pd.DataFrame({"signal": signal, "returns": returns}).dropna()
    
    if len(df) == 0:
        return {
            "long_return": np.nan,
            "short_return": np.nan,
            "long_short_return": np.nan,
        }
    
    # 排序
    df = df.sort_values("signal", ascending=False)
    
    n = len(df)
    n_long = int(n * top_pct)
    n_short = int(n * bottom_pct)
    
    if n_long == 0 or n_short == 0:
        return {
            "long_return": np.nan,
            "short_return": np.nan,
            "long_short_return": np.nan,
        }
    
    long_ret = df.head(n_long)["returns"].mean()
    short_ret = df.tail(n_short)["returns"].mean()
    long_short_ret = long_ret - short_ret
    
    return {
        "long_return": long_ret,
        "short_return": short_ret,
        "long_short_return": long_short_ret,
        "n_long": n_long,
        "n_short": n_short,
    }


def backtest_simple(
    signals: pd.DataFrame,
    returns: pd.DataFrame,
    method: str = "equal_weight"
) -> pd.Series:
    """
    简单回测
    
    Args:
        signals: 信号DataFrame（时间 x 资产）
        returns: 收益DataFrame（时间 x 资产）
        method: 权重方法，"equal_weight" 或 "signal_weight"
    
    Returns:
        组合收益时间序列
    """
    # 对齐
    common_idx = signals.index.intersection(returns.index)
    common_cols = signals.columns.intersection(returns.columns)
    
    sig = signals.loc[common_idx, common_cols]
    ret = returns.loc[common_idx, common_cols]
    
    if method == "equal_weight":
        # 等权
        weights = (sig > 0).astype(float)
        weights = weights.div(weights.sum(axis=1), axis=0).fillna(0)
    elif method == "signal_weight":
        # 信号加权
        weights = sig.div(sig.abs().sum(axis=1), axis=0).fillna(0)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    portfolio_returns = (weights * ret).sum(axis=1)
    
    return portfolio_returns


def regression_analysis(
    signal: pd.Series,
    returns: pd.Series,
    controls: Optional[pd.DataFrame] = None
) -> Dict[str, float]:
    """
    线性回归分析: r_{t+1} ~ OFI_t + controls
    
    Args:
        signal: OFI信号
        returns: 未来收益
        controls: 控制变量（可选）
    
    Returns:
        回归结果字典
    """
    from scipy import stats as sp_stats
    
    # 对齐数据
    df = pd.DataFrame({"signal": signal, "returns": returns})
    
    if controls is not None:
        df = pd.concat([df, controls], axis=1).dropna()
    else:
        df = df.dropna()
    
    if len(df) < 10:
        return {
            "beta": np.nan,
            "t_stat": np.nan,
            "p_value": np.nan,
            "r_squared": np.nan,
            "n_obs": len(df)
        }
    
    # 准备X和y
    X = df[["signal"]].values
    if controls is not None:
        control_cols = [c for c in df.columns if c not in ["signal", "returns"]]
        if control_cols:
            X = df[["signal"] + control_cols].values
    
    y = df["returns"].values
    
    # 添加常数项
    X = np.column_stack([np.ones(len(X)), X])
    
    # OLS
    try:
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        y_pred = X @ beta
        residuals = y - y_pred
        
        # 统计量
        n = len(y)
        k = X.shape[1]
        mse = np.sum(residuals**2) / (n - k)
        var_beta = mse * np.linalg.inv(X.T @ X)
        se_beta = np.sqrt(np.diag(var_beta))
        
        # signal的系数（第1个，因为第0个是常数项）
        signal_beta = beta[1]
        signal_se = se_beta[1]
        t_stat = signal_beta / signal_se if signal_se > 0 else 0
        p_value = 2 * (1 - sp_stats.t.cdf(abs(t_stat), n - k))
        
        # R²
        ss_tot = np.sum((y - y.mean())**2)
        ss_res = np.sum(residuals**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            "beta": signal_beta,
            "t_stat": t_stat,
            "p_value": p_value,
            "r_squared": r_squared,
            "n_obs": n
        }
    except Exception as e:
        return {
            "beta": np.nan,
            "t_stat": np.nan,
            "p_value": np.nan,
            "r_squared": np.nan,
            "n_obs": len(df),
            "error": str(e)
        }


def classification_analysis(
    signal: pd.Series,
    returns: pd.Series
) -> Dict[str, float]:
    """
    分类分析: 预测 sign(r_{t+1})
    
    Args:
        signal: OFI信号
        returns: 未来收益
    
    Returns:
        分类指标字典（AUC, Accuracy等）
    """
    # 对齐数据
    df = pd.DataFrame({"signal": signal, "returns": returns}).dropna()
    
    if len(df) < 10:
        return {
            "auc": np.nan,
            "accuracy": np.nan,
            "n_obs": len(df)
        }
    
    # 创建标签：未来收益的符号
    y_true = (df["returns"] > 0).astype(int).values
    
    # 使用信号作为预测概率（标准化到[0,1]）
    signal_vals = df["signal"].values
    if signal_vals.std() > 0:
        y_score = (signal_vals - signal_vals.min()) / (signal_vals.max() - signal_vals.min())
    else:
        y_score = np.ones_like(signal_vals) * 0.5
    
    # 预测类别（阈值0.5）
    y_pred = (y_score > 0.5).astype(int)
    
    try:
        # 手动计算AUC（不依赖sklearn）
        # 简化版：使用Spearman相关性作为AUC的代理
        from scipy.stats import spearmanr
        auc_proxy, _ = spearmanr(signal_vals, y_true)
        auc = (auc_proxy + 1) / 2  # 转换到[0,1]
        
        # Accuracy
        accuracy = (y_true == y_pred).mean()
        
        # 混淆矩阵（手动计算）
        tp = ((y_true == 1) & (y_pred == 1)).sum()
        fp = ((y_true == 0) & (y_pred == 1)).sum()
        fn = ((y_true == 1) & (y_pred == 0)).sum()
        tn = ((y_true == 0) & (y_pred == 0)).sum()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        return {
            "auc": auc,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "n_obs": len(df),
            "n_positive": int(y_true.sum()),
            "n_negative": int(len(y_true) - y_true.sum())
        }
    except Exception as e:
        return {
            "auc": np.nan,
            "accuracy": np.nan,
            "n_obs": len(df),
            "error": str(e)
        }


def rolling_ic_analysis(
    signal: pd.Series,
    returns: pd.Series,
    window: int = 20,
    method: str = "spearman"
) -> pd.Series:
    """
    滚动IC分析
    
    Args:
        signal: 信号序列
        returns: 收益序列
        window: 滚动窗口大小
        method: 相关系数方法
    
    Returns:
        滚动IC序列
    """
    df = pd.DataFrame({"signal": signal, "returns": returns}).dropna()
    
    if len(df) < window:
        return pd.Series(dtype=float)
    
    def calc_ic(s, r):
        if method == "spearman":
            ic, _ = stats.spearmanr(s, r)
        else:
            ic, _ = stats.pearsonr(s, r)
        return ic
    
    rolling_ic = df.rolling(window).apply(
        lambda x: calc_ic(x["signal"], x["returns"]) if len(x) == window else np.nan,
        raw=False
    )
    
    return rolling_ic["signal"]


def subsample_analysis(
    signal: pd.Series,
    returns: pd.Series,
    subsample_by: str = "hour"
) -> pd.DataFrame:
    """
    子样本分析（按时间段/波动率分组）
    
    Args:
        signal: 信号序列
        returns: 收益序列
        subsample_by: 分组方式 ("hour", "volatility", "day_of_week")
    
    Returns:
        各子样本的IC统计
    """
    df = pd.DataFrame({"signal": signal, "returns": returns}).dropna()
    
    if subsample_by == "hour":
        if isinstance(df.index, pd.DatetimeIndex):
            df["group"] = df.index.hour
        else:
            return pd.DataFrame()
    elif subsample_by == "volatility":
        # 按波动率分组（使用收益率的滚动标准差）
        vol = df["returns"].rolling(20).std()
        df["group"] = pd.qcut(vol, q=3, labels=["low", "mid", "high"], duplicates="drop")
    elif subsample_by == "day_of_week":
        if isinstance(df.index, pd.DatetimeIndex):
            df["group"] = df.index.dayofweek
        else:
            return pd.DataFrame()
    else:
        raise ValueError(f"Unknown subsample_by: {subsample_by}")
    
    results = []
    for group_val, group_df in df.groupby("group"):
        if len(group_df) < 10:
            continue
        
        ic, _ = stats.spearmanr(group_df["signal"], group_df["returns"])
        
        results.append({
            "group": group_val,
            "ic_mean": ic,
            "n_obs": len(group_df)
        })
    
    return pd.DataFrame(results)


def walk_forward_cv(
    signal: pd.Series,
    returns: pd.Series,
    n_splits: int = 5
) -> pd.DataFrame:
    """
    Walk-forward交叉验证
    
    Args:
        signal: 信号序列
        returns: 收益序列
        n_splits: 分割数量
    
    Returns:
        各fold的评估结果
    """
    df = pd.DataFrame({"signal": signal, "returns": returns}).dropna()
    
    n = len(df)
    fold_size = n // n_splits
    
    results = []
    
    for i in range(n_splits):
        # 训练集：前i+1个fold
        train_end = (i + 1) * fold_size
        if i == 0:
            continue  # 第一个fold没有训练集
        
        train = df.iloc[:train_end]
        
        # 测试集：第i+1个fold
        test_start = i * fold_size
        test_end = (i + 1) * fold_size
        test = df.iloc[test_start:test_end]
        
        if len(test) < 10:
            continue
        
        # 计算测试集IC
        ic, p_val = stats.spearmanr(test["signal"], test["returns"])
        
        results.append({
            "fold": i,
            "train_size": len(train),
            "test_size": len(test),
            "ic": ic,
            "p_value": p_val
        })
    
    return pd.DataFrame(results)

