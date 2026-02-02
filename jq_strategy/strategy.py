from jqdata import *
import numpy as np
from datetime import timedelta
from collections import deque

def calc_ofi(prev, curr, level):
    ap, av = f'a{level}_p', f'a{level}_v'
    bp, bv = f'b{level}_p', f'b{level}_v'
    ofi = 0.0

    # bid side
    if curr[bp] > prev[bp]:
        ofi += curr[bv]
    elif curr[bp] == prev[bp]:
        ofi += (curr[bv] - prev[bv])
    else:
        ofi -= prev[bv]

    # ask side（注意方向：ask 下移 => 卖压增强 => 负）
    if curr[ap] < prev[ap]:
        ofi -= curr[av]
    elif curr[ap] == prev[ap]:
        ofi -= (curr[av] - prev[av])
    else:
        ofi += prev[av]

    return ofi


def get_ofi(security, end_dt, window_seconds=60, levels=5, weight=None):
    """
    返回：(ofi, rel_spread, last_current)
    - ofi: 最近 window_seconds 内 tick 累加的 L1~L5 OFI（按 weight 加权）
    - rel_spread: 最后一条快照的相对点差 (a1-b1)/mid
    - last_current: 最后一条快照的 current（最新价）
    get_ticks 的字段包含 current 以及买五卖五。:contentReference[oaicite:0]{index=0}
    """
    if weight is None:
        weight = np.ones(levels, dtype=float)
    else:
        weight = np.asarray(weight, dtype=float)
        if len(weight) != levels:
            raise ValueError(f"len(weight)={len(weight)} != levels={levels}")

    start_dt = end_dt - timedelta(seconds=window_seconds)

    fields = ['time', 'current']
    for i in range(1, levels + 1):
        fields += [f'a{i}_p', f'a{i}_v', f'b{i}_p', f'b{i}_v']

    df = get_ticks(security, start_dt=start_dt, end_dt=end_dt, fields=fields, df=True)
    if df is None or len(df) < 2:
        return np.nan, np.nan, np.nan

    df = df.sort_values('time')

    last = df.iloc[-1]
    a1, b1 = float(last['a1_p']), float(last['b1_p'])
    mid = (a1 + b1) / 2.0 if (a1 > 0 and b1 > 0) else np.nan
    rel_spread = (a1 - b1) / mid if (mid and mid > 0 and a1 > b1) else np.nan
    last_current = float(last['current'])

    prev_row = df.iloc[0]
    prev = {c: float(prev_row[c]) for c in fields if c != 'time'}

    res = 0.0
    lvl_ofi = np.zeros(levels, dtype=float)

    for k in range(1, len(df)):
        row = df.iloc[k]
        curr = {c: float(row[c]) for c in fields if c != 'time'}

        # 基本异常过滤：L1 价差必须为正
        if curr['a1_p'] <= 0 or curr['b1_p'] <= 0 or curr['a1_p'] <= curr['b1_p']:
            prev = curr
            continue

        for level in range(1, levels + 1):
            lvl_ofi[level - 1] = calc_ofi(prev, curr, level)

        res += float((lvl_ofi * weight).sum())
        prev = curr  # ✅ 必须更新

    return res, rel_spread, last_current


def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    
    log.info("[Initialize] Strategy starting...")

    g.universe = [
        '159915.XSHE',
        '159919.XSHE',
        '510300.XSHG',
        '510500.XSHG',
        '518880.XSHG',
        '511380.XSHG',
        # 你现在还在对账 510050，可以临时加进来做 debug：
        # '510050.XSHG',
    ]
    log.info(f"[Initialize] Universe: {g.universe}")

    g.balance_interval = 3     # 3分钟再平衡
    g.k_long = 2
    g.levels = 5
    g.k_spread = 0.5

    # ✅ weight 是参数：默认等权（你的本地口径）
    g.weight = np.ones(g.levels, dtype=float)
    # 如果要试 1/i：
    # g.weight = 1.0 / np.arange(1, g.levels + 1)

    # 每分钟先算 1-min OFI（严格分钟对齐），再把最近3个分钟OFI求和作为信号
    g.minute_window_seconds = 60

    # 状态
    g.bar_count = 0
    g.prev_target = {s: 0.0 for s in g.universe}
    g.turnover = 0.0
    g.trades = 0
    g.cost_est = 0.0

    # 最近3个 1-min OFI / spread 缓存
    g.ofi_1m_hist = {s: deque(maxlen=g.balance_interval) for s in g.universe}
    g.spr_1m_hist = {s: deque(maxlen=g.balance_interval) for s in g.universe}
    
    # 日志计数器：避免日志过多
    g.log_counter = 0

    # ETF 通常不收印花税
    set_order_cost(OrderCost(close_tax=0.0,
                             open_commission=0.0003,
                             close_commission=0.0003,
                             min_commission=5), type='stock')

    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    # 用 market_open 代替 handle_data：分钟回测下 every_bar 每分钟触发。:contentReference[oaicite:1]{index=1}
    run_daily(market_open, time='every_bar', reference_security='000300.XSHG')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')


def before_market_open(context):
    log.info(f"[Before Open] {context.current_dt.date()} - Resetting daily state")
    g.bar_count = 0
    g.ofi_1m_hist = {s: deque(maxlen=g.balance_interval) for s in g.universe}
    g.spr_1m_hist = {s: deque(maxlen=g.balance_interval) for s in g.universe}
    g.log_counter = 0


def market_open(context):
    dt = context.current_dt
    g.bar_count += 1
    g.log_counter += 1
    
    # 每30分钟输出一次进度日志
    if g.log_counter % 30 == 1:
        log.info(f"[Bar {g.bar_count}] {dt} - Processing...")

    # 1) 每分钟更新 1-min OFI（用于对账 & 形成 3-min 信号）
    ofi_results = {}
    for s in g.universe:
        ofi_1m, rel_spread, last_px = get_ofi(
            s, dt,
            window_seconds=g.minute_window_seconds,
            levels=g.levels,
            weight=g.weight
        )
        g.ofi_1m_hist[s].append(ofi_1m)
        g.spr_1m_hist[s].append(rel_spread)
        ofi_results[s] = ofi_1m

    # 可选：对账用（如果你把 510050 加进 universe）
    # if '510050.XSHG' in g.universe:
    #     ofi_dbg = g.ofi_1m_hist['510050.XSHG'][-1]
    
    # 到了再平衡节点
    log.info(f"[Rebalance] Bar {g.bar_count} at {dt} - Starting rebalance")
    #     record(ofi510050_1m=0.0 if np.isnan(ofi_dbg) else ofi_dbg)

    # 2) 没到 3 分钟节点就不交易
    if g.bar_count % g.balance_interval != 0:
        record(pv=context.portfolio.total_value,
               turnover=g.turnover, trades=g.trades, cost_est=g.cost_est)
        return

    # 3) 形成 3-min OFI 信号（严格分钟对齐：最近3个1-min求和）
    ofi_map = {}
    spread_map = {}

    for s inlog.debug(f"[Rebalance] {s} skip: hist_len={len(hist)}, has_nan={any(np.isnan(x) for x in hist) if hist else 'empty'}")
            continue
        ofi_map[s] = float(np.sum(hist))

        spr_hist = [x for x in g.spr_1m_hist[s] if not np.isnan(x)]
        spread_map[s] = float(np.mean(spr_hist)) if len(spr_hist) else np.nan

    if len(ofi_map) < g.k_long:
        log.warning(f"[Rebalance] Not enough signals: got {len(ofi_map)}, need {g.k_long}")
        return
    
    log.info(f"[Rebalance] OFI signals: {', '.join([f'{s}:{v:.0f}' for s, v in sorted(ofi_map.items(), key=lambda x: x[1], reverse=True)])}")_map[s] = float(np.mean(spr_hist)) if len(spr_hist) else np.nan

    if len(ofi_map) < g.k_long:
        return
    log.info(f"[Rebalance] Selected longs: {longs}")

    # 4) 截面排序 long top2（long-only）
    ranked = sorted(ofi_map.items(), key=lambda kv: kv[1], reverse=True)
    longs = [x[0] for x in ranked[:g.k_long]]

    target = {s: 0.0 for s in g.universe}
    w_long = 0.98 / g.k_long
    for s in longs:
        target[s] = w_long

    # 5) 估算一次 rebalance 的点差成本：sum(0.5*|Δw|*k_spread*rel_spread)
    est = 0.0
    for s in g.universe:
        dw = abs(float(target[s]) - float(g.prev_target.get(s, 0.0)))
        traded = 0.5 * dw
        rs = spread_map.get(s, np.nan)
        if not np.isnan(rs):
            est += traded * g.k_spread * rs
    g.cost_est += est

    # 6) 下单 + 统计
    for s in g.universe:
        new_w = float(target[s])
        old_w = float(g.prev_target.get(s, 0.0))
        if abs(new_w - old_w) > 1e-8:
            g.turnover += abs(new_w - old_w)
            g.trades += 1
            capital = cash * new_w
            order_target_value(s, new_w)
            g.prev_target[s] = new_w

    record(pv=context.portfolio.total_value,
           turnover=g.turnover, trades=g.trades, cost_est=g.cost_est)


def positions = [f"{p.security}:{p.value/context.portfolio.total_value:.2%}" for p in context.portfolio.positions.values() if p.total_amount > 0]
    log.info(f"[Day End] {context.current_dt.date()} - PV={context.portfolio.total_value:.2f}, Bars={g.bar_count}, Turnover={g.turnover:.4f}, Trades={g.trades}, Cost={g.cost_est:.6f}")
    if positions:
        log.info(f"[Day End] Positions: {', '.join(positions)
    log.info(f"Day end: pv={context.portfolio.total_value:.2f}, turnover={g.turnover:.4f}, trades={g.trades}, cost_est={g.cost_est:.6f}")
