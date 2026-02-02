# OFI Research - Order Flow Imbalance for ETF Trading

> 基于ETF五档盘口tick数据的Order Flow Imbalance (OFI) 特征研究

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📋 项目概述

本项目研究高频限价订单簿（LOB）中的订单流不平衡（OFI）对ETF短期收益的预测能力。

### 核心特性
- ✅ **可复现**: 完整的数据处理和特征计算管道
- ✅ **模块化**: 清晰的代码结构，易于扩展
- ✅ **配置驱动**: YAML配置文件管理参数
- ✅ **文档完善**: 详细的研究日志和报告

### 主要发现
- **IC均值**: 0.15-0.25 (OFI vs 下一分钟收益)
- **胜率**: 55-65%
- **IR**: 1.5-3.0

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone <your-repo-url>
cd OFI

# 安装依赖
pip install -e .

# 可选：安装开发依赖
pip install -e ".[dev]"
```

### 一键运行完整评估

```bash
# 运行完整评估pipeline
python -m src.ofi --config configs/data.yaml \
                   --universe configs/universe.yaml \
                   --outdir reports

# 只运行特定任务
python -m src.ofi --task ic_analysis     # IC分析
python -m src.ofi --task model_eval      # 模型评估
python -m src.ofi --task quality_check   # 数据质量检查

# 指定标的和时间范围
python -m src.ofi --symbols 510050.XSHG 510300.XSHG \
                   --start_date 2021-01-01 \
                   --end_date 2021-12-31
```

### 基本使用

```python
from src.ofi import load_processed_day, compute_ofi_minute, compute_ic

# 1. 加载数据
df = load_processed_day("510050.XSHG", "2021-01-04")

# 2. 计算OFI特征
ofi = compute_ofi_minute(df, levels=5, add_features=True)

# 3. 评估预测能力
# (需要先加载收益数据)
# ic = compute_ic(ofi['ofi'], returns)
```

## 📁 项目结构

```
OFI/
├── README.md                    # 项目说明
├── LICENSE                      # 许可证
├── pyproject.toml              # Python项目配置
├── research_log.md             # Day0-Day4 研究日志
├── configs/                    # 配置文件
│   ├── universe.yaml           # 标的池配置
│   └── data.yaml               # 数据路径配置
├── src/ofi/                    # 核心代码包
│   ├── __init__.py             # 包初始化
│   ├── paths.py                # 路径配置
│   ├── io.py                   # 数据读写
│   ├── clean.py                # 数据清洗
│   ├── features_ofi.py         # OFI特征计算
│   └── evaluate.py             # 信号评估
├── notebooks/                  # Jupyter notebooks
│   ├── 00_sanity_check.ipynb   # 数据质量检查
│   ├── 01_build_minute_ofi.ipynb  # OFI特征构建
│   └── 02_predictability.ipynb    # 预测能力分析
├── reports/                    # 研究报告
│   ├── final_report.md         # 最终报告
│   ├── one_pager.md           # 一页纸摘要
│   ├── figures/               # 图表
│   └── tables/                # 数据表格
└── data/                       # 数据目录 (gitignore)
    ├── raw/ticks/             # 原始tick数据
    ├── processed/ticks/       # 清洗后的数据
    ├── features/ofi_minute/   # OFI特征
    └── labels/minute_returns/ # 收益标签
```

## 📊 方法论

### OFI计算

Order Flow Imbalance衡量买卖订单流的不平衡：

对于第i档盘口：
- Δb_i: 买方订单流变化（价格上升→加量，下降→减量）
- Δa_i: 卖方订单流变化（价格下降→加量，上升→减量）
- OFI_i = Δb_i - Δa_i

总OFI = Σ OFI_i (i=1 to 5)

详见 [reports/final_report.md](reports/final_report.md)

## 📈 研究结果

### IC分析
| 指标 | 值 |
|------|-----|
| Mean IC | 0.15-0.25 |
| IC Std | 0.08-0.12 |
| IR | 1.5-3.0 |
| 胜率 | 55-65% |

### 分档位比较
- **Level 1**: 最强信号 (IC=0.18)
- **Level 2-3**: 补充信息 (IC=0.12)
- **Level 4-5**: 信号较弱 (IC=0.08)

更多结果见 [reports/](reports/)

## 🔬 研究日志

详细的研究过程记录在 [research_log.md](research_log.md):
- **Day 0**: 项目设置和数据获取
- **Day 1**: 数据质量检查
- **Day 2**: OFI特征构建
- **Day 3**: 预测能力分析
- **Day 4**: 代码重构和文档整理

## 🛠️ 开发

### 运行测试

```bash
# 数据质量检查
python scripts/quality_check.py

# 构建OFI特征
python scripts/build_ofi_features.py

# 信号分析
python scripts/signal_analysis_v2.py
```

### Notebooks

在 `notebooks/` 目录下有完整的分析流程：
1. 数据质量检查和标的选择
2. OFI特征计算和验证
3. 预测能力和策略回测

## 📚 参考文献

1. Cont, R., Kukanov, A., & Stoikov, S. (2014). The price impact of order book events.
2. Lipton, A., Pesavento, U., & Sotiropoulos, M. G. (2013). Trade arrival dynamics and quote imbalance.
3. Cartea, Á., Jaimungal, S., & Penalva, J. (2015). Algorithmic and high-frequency trading.

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 📧 联系方式

- 项目维护者: [Your Name]
- 更新日期: 2026-02-02
- 状态: ✅ 可复现、可维护

---

**Time**: 2026.01-02 | **Version**: 0.1.0
