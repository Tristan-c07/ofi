# OFI Research - One Pager

**ETF Microstructure: OFI Pipeline & Predictability Study**

---

## 🎯 Research Question

**能否用高频订单流不平衡（OFI）预测ETF短期收益？**  
→ 答案：统计上可以，但实践中难以交易。

---

## 📊 Data

- **标的**: 12只高流动性ETF（50ETF、300ETF、创业板ETF等）
- **时间**: 2020-2025年，约1,200交易日
- **频率**: 五档盘口快照（3秒/tick），分钟级聚合
- **规模**: 60-80M tick snapshots
- **来源**: 聚宽（JoinQuant）

---

## 🛠️ Engineering

**可复现Pipeline**:
```bash
# 一键运行
python -m src.ofi --config configs/data.yaml
```

**技术栈**:
- **Data**: Parquet存储，YAML配置驱动
- **Feature**: 5档OFI计算，分钟聚合
- **Eval**: IC/回归/分类/稳健性检验
- **Code**: 模块化设计（`src/ofi/`），完整文档

**质量保证**:
- 严格数据清洗（<2%剔除率）
- Walk-forward验证
- 按天分组CV（避免数据泄露）

---

## ✅ Key Findings

### 1. OFI有预测力（统计显著）

| 指标 | 值 | 说明 |
|------|-----|------|
| **Mean IC** | 0.185 | 中等正相关 |
| **IR** | 1.95 | 信息比率良好 |
| **Win Rate** | 58.7% | 显著高于随机 |
| **t-stat** | 3.87 | 回归系数显著 |
| **AUC** | 0.542 | 方向预测略强于随机 |

### 2. 预测力特征

✅ **时效性**：1-2分钟最强，5分钟后快速衰减  
✅ **档位**：Level 1最强（IC=0.20），多档加权可提升稳健性  
✅ **时段**：开盘和收盘IC更高（0.22 vs 0.17）  
✅ **波动**：高波动时段信号更强（0.25 vs 0.13）

### 3. 跨样本稳健性

✅ Walk-forward CV：所有fold保持显著（IC > 0.15）  
✅ 12个ETF：10个显著正IC  
⚠️ 特殊时期失效：疫情初期（2020-02）、极端波动时段

---

## ❌ Why NOT Tradable

### 成本 > 收益
- **理论收益**：5-10 bps（1分钟）
- **交易成本**：4-10 bps（双边）
- **净收益**：≈ 0 或负

### 延迟杀死信号
- 数据+计算+网络+撮合延迟：**1-4秒**
- OFI在此期间显著衰减
- 实盘vs回测gap巨大

### 市场冲击 &amp; 容量
- 频繁交易产生冲击
- 总容量<数百万（规模化后收益消失）
- T+0需要底仓（资金成本）

### 数据获取限制
- 仅5档（非完整订单簿）
- 快照（非逐笔）
- 历史vs实盘数据差异

---

## 📈 Quantitative Evidence

### IC Analysis（单变量）
```
整体统计:
  Mean IC: 0.185 ± 0.095
  IR: 1.95
  Win Rate: 58.7%
  N: 14,234 day-samples

按标的（Top 3）:
  510050: IC=0.201, IR=2.28 ✓
  510300: IC=0.178, IR=1.75 ✓
  159915: IC=0.165, IR=1.74 ✓
```

### Regression（多变量）
```
r_{t+1} = α + β·OFI_t + ε

结果:
  Beta: 0.000023 (t=3.87, p<0.001)
  R²: 3.4%
  显著比例: 62.3% (p<0.05)
```

### Classification（方向预测）
```
P(r_{t+1}>0 | OFI_t)

结果:
  AUC: 0.542（略强于0.5）
  Accuracy: 51.8%
  → 实际应用困难
```

---

## 🎓 Research Value

虽然难以交易，但研究具有学术和方法论价值：

1. **理论验证**：OFI在中国市场有效（与国际文献一致）
2. **透明度**：开放代码、数据处理、评估方法
3. **工程化**：完整的可复现pipeline
4. **诚实评估**：不夸大，明确指出局限性

---

## 📦 Artifacts

### Code（开源）
```
src/ofi/
├── paths.py       - 路径管理
├── io.py          - 数据读写
├── clean.py       - 数据清洗
├── features_ofi.py - OFI计算
├── evaluate.py    - 评估工具
├── pipeline.py    - 完整流程
└── __main__.py    - CLI入口
```

### Reports
- **final_report.md**: 完整论文式报告（9 sections）
- **one_pager.md**: 本文档
- **tables/**: 自动生成的评估结果
- **research_log.md**: Day0-Day4研究日志

### Configuration
```yaml
# configs/universe.yaml
symbols:
  - 510050.XSHG
  - 510300.XSHG
  - ...

# configs/data.yaml
paths:
  raw: data/raw/ticks
  processed: data/processed/ticks
  features: data/features/ofi_minute
```

---

## 🔮 Future Directions

### 如果要继续...

**学术延伸**:
1. 更细粒度数据（逐笔、更多档位）
2. 机器学习特征工程（LSTM、Transformer）
3. 跨市场比较（A股vs美股vs期货）

**实践改进**:
1. **不做高频**：改为T+1日内摆动（降低换手）
2. **多因子融合**：OFI作为辅助因子，不单独交易
3. **做市应用**：库存管理、报价优化（而非方向预测）
4. **精确回测**：事件驱动撮合模拟（非bar级）

---

## 📧 Contact & Reproducibility

- **项目地址**: [GitHub Repo Link]
- **更新日期**: 2026-02-02
- **版本**: 0.1.0
- **状态**: ✅ **完全可复现**

**一行命令复现所有结果**:
```bash
git clone <repo>
cd OFI
pip install -e .
python -m src.ofi
```

---

**总结**: OFI在统计上有信息量，但交易成本和延迟使其难以盈利。本研究价值在于**方法论的完整性**和**对现实约束的诚实评估**。
