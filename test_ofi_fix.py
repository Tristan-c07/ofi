"""测试OFI计算是否正常"""
import pandas as pd
from pathlib import Path
from src.ofi import compute_ofi_per_tick, ensure_datetime_index, aggregate_to_minute

# 加载数据
df = pd.read_parquet('data/processed/ticks/510050.XSHG/2021-01-04/part.parquet')
print('Original shape:', df.shape)
print('Columns:', df.columns.tolist())

# 设置datetime索引
df_idx = ensure_datetime_index(df)
print('\nAfter ensure_datetime_index:')
print('  Index type:', type(df_idx.index))
print('  Index range:', df_idx.index[0], 'to', df_idx.index[-1])
print('  Shape:', df_idx.shape)

# 计算tick级OFI
ofi_tick = compute_ofi_per_tick(df_idx, levels=5)
print('\nOFI tick:')
print('  Shape:', ofi_tick.shape)
print('  OFI columns:', [c for c in ofi_tick.columns if c.startswith('ofi')])
print('  Sample OFI values:')
print(ofi_tick[['ofi1', 'ofi2', 'ofi3', 'ofi4', 'ofi5', 'ofi']].head())

# 聚合到分钟
ofi_min = aggregate_to_minute(ofi_tick, bar='1min', agg='sum')
print('\nOFI minute:')
print('  Shape:', ofi_min.shape)
print('  First 10 rows:')
print(ofi_min.head(10))
print('\n  Last 5 rows:')
print(ofi_min.tail(5))

# 检查时间范围
print('\nTime range:', ofi_min.index[0], 'to', ofi_min.index[-1])
