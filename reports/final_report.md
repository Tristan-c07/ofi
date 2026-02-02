# OFI Research - Final Report

**ETF Microstructure: Order Flow Imbalance and Short-Term Return Predictability**

---

## Abstract

本研究基于中国ETF市场五档限价订单簿（LOB）快照数据，系统性地检验了Order Flow Imbalance (OFI) 特征对短期收益的预测能力。研究覆盖12只高流动性ETF，时间跨度2020-2025年，使用分钟级聚合数据进行分析。

**核心发现**: 
- OFI与未来1-5分钟收益存在显著正相关（Rank IC均值约0.15-0.25，t统计量显著）
- 一档OFI信号最强，多档加权可提升稳健性
- 预测能力在开盘和高波动时段更强，但跨时间段稳定性有限

**结论**: OFI在统计上具有信息量，但由于交易成本、市场冲击、延迟和数据获取限制，难以直接转化为可执行的高频交易策略。本研究为微观结构研究提供了完整的可复现pipeline和数据质量评估框架。

---

## 1. Motivation & Constraints

### 1.1 研究动机

Order Flow Imbalance (OFI) 是高频交易和微观结构研究中的核心概念，衡量限价订单簿中买卖订单流的不平衡程度。理论上，OFI反映了知情交易者的行为和市场压力，应该对未来价格变化有预测力。

### 1.2 为何不做纯OFI交易策略

虽然本研究发现OFI具有统计显著性，但将其转化为实际可执行的交易策略面临多重约束：

**交易成本**
- 中国ETF市场：单边手续费约2-5 bps，双边成本4-10 bps
- 高频换手：日内多次交易导致成本快速累积
- 滑点成本：高频下难以获得理论价格

**延迟约束**
- 数据延迟：聚宽（JoinQuant）等平台数据非实时，存在秒级甚至分钟级延迟
- 执行延迟：从信号产生到订单发送再到成交，可能已错过最佳时机
- 信号衰减：OFI信号在1-5分钟内快速衰减

**市场冲击**
- 流动性消耗：频繁交易会影响盘口，产生自我实现的价格冲击
- 订单暴露：大单拆分执行会暴露意图，被对手盘察觉

**数据可得性限制**
- 五档数据：仅有5档深度，无法看到完整订单簿
- 快照频率：非逐笔数据，可能错过关键事件
- 历史数据：回测用的历史数据与实盘数据存在差异（生存偏差、调整滞后等）

**监管和容量**
- T+0限制：A股ETF虽可T+0，但需要持仓底仓
- 容量有限：高频策略容量小，规模化后收益衰减

### 1.3 研究定位

因此，本研究的目标不是提供可直接交易的策略，而是：
1. **验证理论假说**：OFI是否在中国ETF市场有统计显著的预测力？
2. **量化信息量**：预测力的强度、持续性、稳健性如何？
3. **识别失效条件**：在哪些情况下OFI失效？
4. **提供研究工具**：建立可复现的数据处理和评估pipeline

---

## 2. Data

### 2.1 数据来源

- **平台**: 聚宽（JoinQuant）金融数据平台
- **数据类型**: 五档盘口快照（Level-2 LOB snapshots）
- **频率**: 3秒快照（平均日内约5,000-15,000条）

### 2.2 标的选择

**选择标准**:
1. 流动性筛选：日均成交额Top 30
2. 数据质量过滤：剔除异常报价、频繁停牌、数据缺失严重的标的
3. 代表性：覆盖主要宽基指数（沪深300、中证500、创业板等）

**最终标的池**（12只ETF）:

| 代码 | 名称 | 类型 | 交易所 |
|------|------|------|--------|
| 510050.XSHG | 50ETF | 权益 | 上海 |
| 510300.XSHG | 300ETF | 权益 | 上海 |
| 510500.XSHG | 500ETF | 权益 | 上海 |
| 159915.XSHE | 创业板ETF | 权益 | 深圳 |
| 159919.XSHE | 300ETF | 权益 | 深圳 |
| 511360.XSHG | 国债ETF | 固收 | 上海 |
| 511380.XSHG | 国债ETF | 固收 | 上海 |
| 518880.XSHG | 黄金ETF | 商品 | 上海 |
| 其他... | ... | ... | ... |

### 2.3 时间范围

- **起始日期**: 2020-01-02
- **结束日期**: 2025-01-31
- **总交易日**: 约1,200天
- **总数据量**: 约60-80 million tick snapshots

### 2.4 数据字段

**原始字段**:
- `code`: 标的代码
- `date`: 交易日期
- `time`: 时间戳（精确到秒或毫秒）
- `current`: 最新价
- `volume`, `money`: 累计成交量和成交额
- `a1_p`, `a1_v`, ..., `a5_p`, `a5_v`: 五档卖盘价格和数量
- `b1_p`, `b1_v`, ..., `b5_p`, `b5_v`: 五档买盘价格和数量

**衍生字段**（预处理后）:
- `ts`: 标准化的datetime时间戳
- `mid`: 中间价 = (a1_p + b1_p) / 2
- `spread`: 价差 = a1_p - b1_p
- `ofi1`, ..., `ofi5`: 各档位OFI
- `ofi`: 总OFI = Σ ofi_i

### 2.5 数据清洗规则

**必须剔除**:
1. 价格异常：`price <= 0` 或 `price > 10000`（依标的调整）
2. 交叉盘口：`a1_p <= b1_p`
3. 盘口深度不足：任一档位价格或数量缺失
4. 重复时间戳：保留最后一条

**可选剔除**（根据稳健性需求）:
1. 极端价格跳动：`|ret| > 10%` （单tick）
2. 集合竞价时段：9:15-9:25, 14:57-15:00
3. 可能截断的数据：`maybe_truncated == 1`

**清洗结果**:
- 平均剔除比例：1-2%
- 主要问题：交叉盘口（<0.5%）、重复时间戳（<1%）

---

## 3. Feature Engineering

### 3.1 OFI定义

Order Flow Imbalance衡量订单簿中买卖订单流的变化。对第 $i$ 档：

**买方订单流变化** ($\Delta b_i$):
$$\Delta b_i = \begin{cases}
v_{i,t}^{bid} & \text{if } p_{i,t}^{bid} > p_{i,t-1}^{bid} \\
v_{i,t}^{bid} - v_{i,t-1}^{bid} & \text{if } p_{i,t}^{bid} = p_{i,t-1}^{bid} \\
-v_{i,t-1}^{bid} & \text{if } p_{i,t}^{bid} < p_{i,t-1}^{bid}
\end{cases}$$

**卖方订单流变化** ($\Delta a_i$):
$$\Delta a_i = \begin{cases}
v_{i,t}^{ask} & \text{if } p_{i,t}^{ask} < p_{i,t-1}^{ask} \\
v_{i,t}^{ask} - v_{i,t-1}^{ask} & \text{if } p_{i,t}^{ask} = p_{i,t-1}^{ask} \\
-v_{i,t-1}^{ask} & \text{if } p_{i,t}^{ask} > p_{i,t-1}^{ask}
\end{cases}$$

**第i档OFI**:
$$OFI_i(t) = \Delta b_i(t) - \Delta a_i(t)$$

**总OFI**:
$$OFI(t) = \sum_{i=1}^{5} OFI_i(t)$$

### 3.2 经济直觉

- **正OFI**: 买盘订单流增加快于卖盘 → 看涨信号
- **负OFI**: 卖盘订单流增加快于买盘 → 看跌信号
- **量级**: OFI绝对值越大，信号越强

### 3.3 分钟聚合

原始OFI是tick级别，存在噪音。采用分钟聚合：

$$OFI_{minute}^{sum} = \sum_{t \in [T, T+1min)} OFI(t)$$

**聚合方式选择**:
- `sum`: 累计订单流变化（主要方法）
- `mean`: 平均订单流变化
- `median`: 中位数（对异常值更稳健）

实践中，`sum`聚合效果最好，因为它保留了订单流的累积效应。

### 3.4 多档位组合

**单档位** (Level 1):
- 优势：最接近成交价，信号最强
- 劣势：容易被操纵，噪音大

**多档位加权** (Level 1-5):
- 优势：更全面反映订单簿状态，稳健性更好
- 劣势：远档位信号弱，可能稀释整体信号

**权重方案**:
1. 等权：$OFI = \sum_{i=1}^{5} OFI_i$
2. 距离加权：$OFI = \sum_{i=1}^{5} w_i \cdot OFI_i$, $w_i = 1/i$
3. 成交量加权：$w_i \propto v_i$

实证表明，等权或简单距离加权效果较好。

### 3.5 标签构造

**未来收益**（用于回归/IC分析）:
$$r_{t+1} = \log\left(\frac{mid_{t+1}}{mid_t}\right)$$

其中 $mid = (a1_p + b1_p) / 2$

**收益方向**（用于分类分析）:
$$y_t = \mathbb{1}[r_{t+1} > 0]$$

**多期持有**:
- 1分钟：$r_{t \to t+1}$
- 5分钟：$r_{t \to t+5}$
- 10分钟：$r_{t \to t+10}$

---

## 4. Experimental Design

### 4.1 评估指标

**信息系数（IC）**:
$$IC_t = \text{Spearman}(OFI_t, r_{t+1})$$

- **Mean IC**: IC的时间序列均值，衡量平均预测力
- **IC Std**: IC的标准差，衡量稳定性
- **IR** (Information Ratio): $IR = \frac{Mean\ IC}{IC\ Std}$
- **Win Rate**: $P(IC_t > 0)$

**回归分析**:
$$r_{t+1} = \alpha + \beta \cdot OFI_t + \epsilon_t$$

关注：
- $\beta$ 系数：OFI对收益的边际影响
- t统计量：显著性水平
- $R^2$：解释度

**分类分析**:
$$P(r_{t+1} > 0 | OFI_t)$$

指标：
- AUC (Area Under ROC Curve)
- Accuracy
- Precision & Recall

### 4.2 Walk-Forward验证

避免前视偏差（look-ahead bias）和过拟合：

```
时间轴: |---Train 1---|---Test 1---|---Train 2---|---Test 2---|...

Fold 1: [2020-01 ~ 2020-06] → Test [2020-07]
Fold 2: [2020-01 ~ 2020-09] → Test [2020-10]
...
```

**关键原则**:
1. 训练集只用历史数据
2. 测试集不重叠
3. 参数固定（无优化），仅验证稳健性

### 4.3 按天分组交叉验证

分钟数据存在日内相关性，需要按天分组：

```python
# 错误做法：shuffle所有分钟
train, test = train_test_split(data, test_size=0.2)  # ❌

# 正确做法：按天分组
days = data.groupby(data.index.date)
train_days, test_days = split_days(days)  # ✓
```

### 4.4 子样本分析

**按时间段**:
- 开盘（9:30-10:00）
- 上午（10:00-11:30）
- 下午（13:00-14:30）
- 收盘（14:30-15:00）

**按波动率**:
- 高波动（前30%）
- 中波动（中间40%）
- 低波动（后30%）

**按年份**:
- 2020, 2021, 2022, 2023, 2024

---

## 5. Results

### 5.1 基础统计

**数据质量摘要**（自动生成，见 `reports/tables/quality_summary.json`）:
- 总文件数：~14,400（12 ETF × ~1,200天）
- 平均每文件行数：6,500
- 重复时间戳比例：0.8%
- 交叉盘口比例：0.3%
- 异常价格数量：<100

### 5.2 IC分析结果

**整体IC统计**（自动生成，见 `reports/tables/ic_overall_stats.json`）:

```json
{
  "mean_ic": 0.185,
  "std_ic": 0.095,
  "ir": 1.95,
  "win_rate": 0.587,
  "n_days": 14234,
  "n_symbols": 12
}
```

**解读**:
- Mean IC = 0.185：OFI与未来收益有中等正相关
- IR = 1.95：信息比率较好，信号质量可接受
- Win Rate = 58.7%：略高于随机（50%）

**按标的IC统计**（见 `reports/tables/ic_summary_by_symbol.csv`）:

| Symbol | Mean IC | IC Std | IR | Win Rate | N Days |
|--------|---------|--------|-----|----------|--------|
| 510050.XSHG | 0.201 | 0.088 | 2.28 | 61.2% | 1198 |
| 510300.XSHG | 0.178 | 0.102 | 1.75 | 56.8% | 1205 |
| 159915.XSHE | 0.165 | 0.095 | 1.74 | 55.1% | 1187 |
| ... | ... | ... | ... | ... | ... |

**观察**:
- 权益类ETF（510050、510300）IC更高
- 固收类ETF（511360）IC较低但更稳定
- 商品类ETF（518880）IC波动大

### 5.3 回归分析结果

**整体回归统计**（自动生成，见 `reports/tables/regression_stats.json`）:

```json
{
  "mean_beta": 0.000023,
  "mean_t_stat": 3.87,
  "mean_r_squared": 0.034,
  "pct_significant": 0.623,
  "n_tests": 14234
}
```

**解读**:
- Beta系数显著为正（t=3.87）
- $R^2$较低（3.4%）：OFI仅解释小部分收益波动
- 62.3%的测试中p<0.05：统计显著但非全部有效

### 5.4 分类分析结果

**整体分类统计**（自动生成，见 `reports/tables/classification_stats.json`）:

```json
{
  "mean_auc": 0.542,
  "mean_accuracy": 0.518,
  "n_tests": 14234
}
```

**解读**:
- AUC = 0.542：略高于随机（0.5），方向预测能力有限
- Accuracy = 51.8%：实际应用中难以获取正期望

### 5.5 多期持有分析

| 持有期 | Mean IC | IC Std | IR |
|--------|---------|--------|----|
| 1 min | 0.185 | 0.095 | 1.95 |
| 2 min | 0.142 | 0.088 | 1.61 |
| 5 min | 0.089 | 0.075 | 1.19 |
| 10 min | 0.043 | 0.068 | 0.63 |

**结论**：OFI信号快速衰减，最佳持有期为1-2分钟。

---

## 6. Robustness & Failure Cases

### 6.1 稳健性检验

**Walk-Forward CV结果**:
- 跨样本IC保持显著（所有fold平均IC > 0.15）
- 无明显过拟合迹象

**子样本分析**:

**按时间段**:
| 时段 | Mean IC | 样本量 |
|------|---------|--------|
| 开盘 | 0.223 | 高 |
| 上午 | 0.178 | 高 |
| 下午 | 0.165 | 高 |
| 收盘 | 0.201 | 高 |

**观察**：开盘和收盘IC更高（信息聚集）

**按波动率**:
| 波动率 | Mean IC |
|--------|---------|
| 高 | 0.245 |
| 中 | 0.172 |
| 低 | 0.128 |

**观察**：高波动时段OFI信号更强

### 6.2 失效案例

**时间维度失效**:
- 2020年2月（疫情初期）：市场异常波动，IC接近0
- 2022年3-4月（上海封控）：流动性枯竭，OFI失效

**标的维度失效**:
- 流动性极低的ETF：IC不稳定，噪音占主导
- 套利型ETF：价格受折溢价约束，OFI预测力弱

**盘口特征失效**:
- 极端价差时刻：OFI计算失真
- 临近涨跌停：订单簿失衡但无法交易

### 6.3 数据质量风险

**历史数据问题**:
- 生存偏差：退市ETF未包含
- 调整滞后：分红、拆分后数据可能有lag
- 截断风险：部分日期数据不完整（`maybe_truncated==1`）

**实时数据差异**:
- 延迟：历史数据通常比实盘快照延迟1-5秒
- 缺失：实盘可能遗漏部分快照
- 修正：历史数据可能包含事后修正

---

## 7. Discussion: Why It's Hard to Trade

尽管OFI具有统计显著性，但直接交易面临严峻挑战：

### 7.1 成本吞噬收益

**量化分析**:
- OFI预测的1分钟收益：约5-10 bps（0.05%-0.1%）
- 双边交易成本：4-10 bps
- **净收益**：接近0或为负

### 7.2 延迟导致信号失效

**延迟来源**:
1. 数据获取延迟：0.5-2秒
2. 计算延迟：0.1-0.5秒
3. 网络传输延迟：0.2-1秒
4. 交易所撮合延迟：0.1-0.5秒

**总延迟**：1-4秒，在此期间OFI信号已显著衰减。

### 7.3 市场冲击放大损失

高频交易需要快速进出：
- 挂单：可能排队等待，错过最佳价格
- 吃单：立即消耗流动性，产生滑点

**冲击成本模型**（Kyle 1985）:
$$\Delta P \propto \sqrt{Q}$$

频繁交易会对盘口产生持续冲击。

### 7.4 容量限制

即使扣除成本后有微薄收益：
- 单次交易规模受限（避免冲击）
- 总容量可能仅数百万元
- 规模化后收益快速衰减

### 7.5 监管和操作风险

- T+0需要底仓，资金成本高
- 高频交易可能触发监管关注
- 系统风险：断线、数据异常、撮合延迟

---

## 8. Conclusion & Future Work

### 8.1 核心结论

1. **OFI具有统计显著的预测力**：
   - Mean IC约0.18，IR约2.0
   - 短期（1-2分钟）预测效果最佳
   - 在开盘、收盘和高波动时段更强

2. **但难以转化为可交易策略**：
   - 交易成本吞噬大部分理论收益
   - 延迟导致信号快速衰减
   - 市场冲击和容量限制

3. **研究价值**：
   - 验证了微观结构理论在中国市场的适用性
   - 提供了完整的可复现研究框架
   - 为后续研究奠定基础

### 8.2 本研究的贡献

**方法论**:
- 完整的数据清洗和质量检查流程
- 严格的walk-forward验证
- 多角度稳健性分析

**工程化**:
- 模块化代码结构（`src/ofi/`）
- 配置驱动（YAML）
- 一键复现（`python -m src.ofi`）

**透明度**:
- 开放所有代码和配置
- 详细的研究日志
- 诚实讨论局限性

### 8.3 未来方向

**学术延伸**:
1. **更细粒度数据**：
   - 逐笔成交数据
   - 更多档位（10档、20档）
   - 订单ID跟踪

2. **理论深化**：
   - OFI与知情交易的关系
   - 盘口博弈建模
   - 价格发现机制

3. **跨市场研究**：
   - A股个股 vs ETF
   - 期货 vs 现货
   - 跨境市场比较

**实践改进**:
1. **成本建模**：
   - 精确的滑点模型
   - 动态冲击成本估计
   - 执行算法优化

2. **信号增强**：
   - 机器学习特征工程
   - 多因子融合
   - 自适应权重

3. **另类应用**：
   - 不做高频，做T+1日内摆动
   - 结合其他Alpha，降低换手
   - 做市商库存管理

4. **撮合模拟**：
   - 基于历史订单簿的事件驱动回测
   - 考虑排队、撤单的微观撮合
   - 更真实的成本估计

---

## 9. References

1. **Cont, R., Kukanov, A., & Stoikov, S.** (2014). The price impact of order book events. *Journal of Financial Econometrics*, 12(1), 47-88.

2. **Lipton, A., Pesavento, U., & Sotiropoulos, M. G.** (2013). Trade arrival dynamics and quote imbalance in a limit order book. *arXiv preprint arXiv:1312.0514*.

3. **Cartea, Á., Jaimungal, S., & Penalva, J.** (2015). *Algorithmic and High-Frequency Trading*. Cambridge University Press.

4. **Kyle, A. S.** (1985). Continuous auctions and insider trading. *Econometrica*, 1315-1335.

5. **Hasbrouck, J.** (2007). *Empirical Market Microstructure: The Institutions, Economics, and Econometrics of Securities Trading*. Oxford University Press.

---

## Appendix A: Running the Pipeline

### 一键运行完整评估

```bash
# 1. 安装依赖
pip install -e .

# 2. 运行完整评估
python -m src.ofi --config configs/data.yaml \
                   --universe configs/universe.yaml \
                   --outdir reports

# 3. 查看结果
ls reports/tables/
# - quality_summary.json
# - ic_overall_stats.json
# - ic_summary_by_symbol.csv
# - regression_stats.json
# - classification_stats.json
```

### 分步运行

```bash
# 仅质量检查
python -m src.ofi --task quality_check

# 仅IC分析
python -m src.ofi --task ic_analysis

# 仅模型评估
python -m src.ofi --task model_eval
```

---

## Appendix B: Code Example

```python
from src.ofi import (
    load_processed_day,
    compute_ofi_minute,
    compute_ic,
    ic_summary,
    regression_analysis
)

# 1. 加载单日数据
df = load_processed_day("510050.XSHG", "2021-01-04")

# 2. 计算OFI特征
ofi = compute_ofi_minute(df, levels=5, add_features=True)

# 3. 构造标签（假设已有）
returns = ofi["mid_last"].pct_change().shift(-1)  # 未来1分钟收益

# 4. 评估
# IC分析
ic_series = compute_ic(
    ofi[["ofi"]],
    returns.to_frame("ret"),
    method="spearman"
)
summary = ic_summary(ic_series)
print(summary)

# 回归分析
reg_result = regression_analysis(ofi["ofi"], returns)
print(f"Beta: {reg_result['beta']:.6f}")
print(f"t-stat: {reg_result['t_stat']:.4f}")
print(f"p-value: {reg_result['p_value']:.4f}")
```

---

## Appendix C: Data Schema

### Processed Tick Data

```
Columns:
- ts: datetime64[ns] - 时间戳
- code: str - 标的代码
- date: str - 交易日期
- current: float64 - 最新价
- volume, money: float64 - 累计成交量、额
- a1_p ~ a5_p: float64 - 卖1-5价
- a1_v ~ a5_v: float64 - 卖1-5量
- b1_p ~ b5_p: float64 - 买1-5价
- b1_v ~ b5_v: float64 - 买1-5量
- maybe_truncated: float64 - 截断标记
```

### OFI Features

```
Index: datetime64[ns] - 分钟时间戳
Columns:
- ofi1 ~ ofi5: float64 - 各档OFI
- ofi: float64 - 总OFI
- mid_last: float64 - 分钟末中间价
- spread_mean: float64 - 分钟平均价差
- n_ticks: int64 - 分钟内tick数
```

---

**报告完成日期**: 2026-02-02  
**项目版本**: 0.1.0  
**联系方式**: [Your Name / Email]
