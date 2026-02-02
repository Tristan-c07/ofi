# 性能问题诊断

## 可能的性能瓶颈

### 1. **get_ticks 调用频繁** ⚠️ 最可能的原因
```python
# 当前：每分钟对 6 只标的调用 get_ticks
# 每天 240 分钟 × 6 只 = 1440 次 API 调用
```

**影响**：
- 聚宽 `get_ticks` 是耗时操作，每次需要从数据库查询
- 获取 5 档盘口数据（22 个字段）增加数据传输时间
- 回测时大量 I/O 导致卡顿

**解决方案**：
1. 减少调用频率：只在再平衡节点（每3分钟）获取数据
2. 使用缓存：在内存中缓存最近的 tick 数据
3. 减少字段：如果只用 L1，只获取 L1 数据

### 2. **数据量过大**
```python
# 每次获取 60 秒的 tick 数据
# 对于活跃 ETF，可能有数百条 tick
```

### 3. **循环计算 OFI**
```python
# 每个 tick 都要计算 5 档 OFI
# 单日 6 只标的 × 240 分钟 × 平均 50 tick/分钟 = 72,000 次循环
```

## 日志说明

添加的日志会输出：

### 初始化
```
[Initialize] Strategy starting...
[Initialize] Universe: ['159915.XSHE', ...]
```

### 每天开盘前
```
[Before Open] 2024-01-01 - Resetting daily state
```

### 运行中（每30分钟一次）
```
[Bar 30] 2024-01-01 09:59:00 - Processing...
```

### 再平衡时（每3分钟）
```
[Rebalance] Bar 3 at 2024-01-01 09:32:00 - Starting rebalance
[Rebalance] OFI signals: 510300.XSHG:12345, 159919.XSHE:9876, ...
[Rebalance] Selected longs: ['510300.XSHG', '159919.XSHE']
[Rebalance] Orders: 510300.XSHG: 0.00%→49.00%; 159919.XSHE: 0.00%→49.00%
[Rebalance] Stats: turnover=0.9800, trades=2, cost_est=0.000123
```

### 收盘
```
[Day End] 2024-01-01 - PV=1000000.00, Bars=240, Turnover=1.9600, Trades=4, Cost=0.000246
[Day End] Positions: 510300.XSHG:49.00%, 159919.XSHE:49.00%
```

## 优化建议

### 方案1：减少调用频率（推荐）
```python
# 只在再平衡节点获取数据
if g.bar_count % g.balance_interval == 0:
    for s in g.universe:
        ofi_3m, rel_spread, last_px = get_ofi(
            s, dt,
            window_seconds=180,  # 直接获取 3 分钟
            levels=g.levels,
            weight=g.weight
        )
```

### 方案2：使用分钟线代替 tick（最快）
```python
# 使用 get_price 获取分钟 OHLCV
# 虽然丢失盘口信息，但计算快 100 倍
```

### 方案3：只用 L1 数据
```python
g.levels = 1  # 只用 L1
# 减少数据量和计算量
```

## 监控指标

通过日志查看：
1. **是否卡在数据获取**：如果只看到 `[Bar X] Processing...` 但没有后续日志
2. **数据是否缺失**：查看 `[Rebalance] {s} skip` 的警告
3. **信号是否生成**：查看 `OFI signals` 的值是否合理
4. **是否实际下单**：查看 `Orders` 日志

## 测试建议

1. **先测试短期**：只回测 1-2 天，看是否正常
2. **逐步增加标的**：先测 2-3 只，再加到 6 只
3. **对比性能**：记录每天回测耗时，定位瓶颈
