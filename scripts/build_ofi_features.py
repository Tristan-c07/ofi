"""
重新生成 OFI 分钟特征数据
使用修复后的 ofi.py 函数批量处理所有标的的所有交易日
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from tqdm import tqdm

from src.pipeline_io import load_config, load_universe, iter_daily_files
from src.ofi import compute_ofi_per_tick, ensure_datetime_index, aggregate_to_minute


def load_daily(path: Path, source: str) -> pd.DataFrame:
    """加载单日tick数据"""
    if source == "processed":
        return pd.read_parquet(path)
    if source == "raw":
        try:
            return pd.read_csv(path, compression="gzip")
        except pd.errors.ParserError:
            return pd.read_csv(
                path, 
                compression="gzip",
                on_bad_lines='skip',
                engine='python'
            )
    raise ValueError(f"unknown source={source}")


def out_path(base: Path, symbol: str, date: str) -> Path:
    """生成输出文件路径"""
    d = base / symbol
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{date}.parquet"


def process_one_day(df: pd.DataFrame, levels: int, bar: str, agg: str) -> pd.DataFrame:
    """处理单日数据，返回分钟级OFI"""
    # 确保有datetime索引
    df_idx = ensure_datetime_index(df)
    
    # 计算tick级OFI
    ofi_tick = compute_ofi_per_tick(df_idx, levels=levels)
    
    # 聚合到分钟
    ofi_min = aggregate_to_minute(ofi_tick, bar=bar, agg=agg)
    
    return ofi_min


def main():
    # 加载配置
    cfg = load_config("configs/data.yaml")
    universe = load_universe(cfg.data.universe_file)
    
    print(f"Universe: {universe}, total={len(universe)}")
    print(f"OFI Config: levels={cfg.ofi.levels}, bar={cfg.ofi.bar}, agg={cfg.ofi.agg}")
    print(f"Output dir: {cfg.ofi.output_dir}")
    print(f"Overwrite: {cfg.ofi.overwrite}")
    print()
    
    total_done = 0
    total_skip = 0
    total_fail = 0
    
    # 收集所有需要处理的文件
    all_tasks = []
    for sym in universe:
        for sym, date, path, src in iter_daily_files(
            cfg.data.processed_dir, cfg.data.raw_dir, sym, 
            cfg.data.start, cfg.data.end
        ):
            op = out_path(cfg.ofi.output_dir, sym, date)
            
            # 如果不覆盖且文件已存在，跳过
            if not cfg.ofi.overwrite and op.exists():
                total_skip += 1
                continue
            
            all_tasks.append((sym, date, path, src, op))
    
    print(f"Total tasks: {len(all_tasks)} (skipped: {total_skip})")
    
    # 处理所有任务
    for sym, date, path, src, op in tqdm(all_tasks, desc="Processing"):
        try:
            # 加载数据
            df = load_daily(path, src)
            
            # 检查必需列
            required_cols = ['a1_p', 'a1_v', 'b1_p', 'b1_v']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                raise ValueError(f"Missing columns: {missing}")
            
            # 处理并生成OFI
            ofi_min = process_one_day(
                df, 
                levels=cfg.ofi.levels, 
                bar=cfg.ofi.bar, 
                agg=cfg.ofi.agg
            )
            
            # 保存
            ofi_min.to_parquet(op)
            total_done += 1
            
        except Exception as e:
            total_fail += 1
            print(f"\n[FAIL] {sym} {date} src={src}: {type(e).__name__}: {str(e)[:100]}")
    
    print(f"\n{'='*60}")
    print(f"Finished!")
    print(f"  Done: {total_done}")
    print(f"  Skip: {total_skip}")
    print(f"  Fail: {total_fail}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
