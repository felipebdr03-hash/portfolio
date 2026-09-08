import pandas as pd
import matplotlib.pyplot as plt
import config, data, factor_score
import portfolio_construction as pc
import metrics

def get_rebalance_dates(index):
    start = pd.Timestamp(config.START_DATE)
    end = pd.Timestamp(config.END_DATE) if config.END_DATE else index.max()
    dates = pd.date_range(start=start, end=end, freq=config.REBALANCE_FREQ)
    return sorted(set(d for d in (index[index >= x][0] if len(index[index >= x]) else None for x in dates) if d is not None and d <= end))

def run_strategy(prices_full, cdi_daily, method):
    dates = get_rebalance_dates(prices_full.index)
    periods, history = [], []
    prev = pd.Series(dtype=float)
    configured_end = pd.Timestamp(config.END_DATE) if config.END_DATE else prices_full.index.max()

    for i, reb_date in enumerate(dates):
        start = reb_date - pd.DateOffset(months=config.LOOKBACK_MONTHS)
        window = prices_full.loc[start:reb_date]
        min_days = config.MIN_HISTORY_MONTHS * 21
        valid = [c for c in window.columns if window[c].dropna().shape[0] >= min_days]
        window = window[valid].dropna(axis=1, how="any")
        if window.shape[1] < 3:
            continue

        selected = factor_score.select_top_assets(window, reb_date, config.TOP_N_ASSETS)
        if len(selected) < 3:
            continue
        selected_prices = window[selected]
        rf_rate = data.annualized_cdi_until(cdi_daily, reb_date, config.LOOKBACK_MONTHS)

        if method == "markowitz":
            weights = pc.markowitz_max_sharpe(selected_prices, rf_rate)
        elif method == "risk_parity":
            weights = pc.risk_parity(selected_prices)
        elif method == "equal_weight":
            weights = pc.equal_weight(selected_prices)
        else:
            raise ValueError(f"Método desconhecido: {method}")

        weights = weights[weights > 1e-10]
        history.append(weights)

        end = dates[i + 1] if i + 1 < len(dates) else configured_end
        end = min(end, configured_end)
        future = prices_full.loc[reb_date:end, weights.index].dropna(how="any")
        if len(future) < 2:
            continue

        daily = future.pct_change().dropna().dot(weights.reindex(future.columns).fillna(0))
        turnover_amount = 1.0 if prev.empty else sum(
            abs(weights.get(t, 0) - prev.get(t, 0))
            for t in set(prev.index) | set(weights.index)
        ) / 2
        cost = turnover_amount * config.TRANSACTION_COST_BPS / 10000

        if len(daily):
            daily.iloc[0] = (1 + daily.iloc[0]) * (1 - cost) - 1

        periods.append(daily)
        prev = weights

    if not periods:
        raise RuntimeError(f"Nenhum período válido para {method}.")
    result = pd.concat(periods)
    return result[~result.index.duplicated(keep="first")].sort_index(), history

def align_returns(strategies, benchmarks):
    series = list(strategies.values()) + list(benchmarks.values())
    start = max(s.index.min() for s in series)
    end = min(s.index.max() for s in series)
    return (
        {k: v.loc[start:end] for k, v in strategies.items()},
        {k: v.loc[start:end] for k, v in benchmarks.items()},
    )

def run_benchmarks(start, end):
    out = {}
    for name, ticker in config.BENCHMARK_TICKERS.items():
        try:
            p = data.download_price_history([ticker], start, end)
            if not p.empty:
                out[name] = p.iloc[:, 0].pct_change().dropna()
        except Exception as e:
            print(f"aviso: benchmark {name}: {e}")
    try:
        out["CDI"] = data.download_cdi_daily(start, end)
    except Exception as e:
        print(f"aviso: CDI: {e}")
    return out

def main():
    approved = data.screen_universe(config.UNIVERSE)
    if len(approved) < 5:
        raise RuntimeError("Poucos ativos aprovados.")

    data_start = (
        pd.Timestamp(config.START_DATE) - pd.DateOffset(months=config.LOOKBACK_MONTHS)
    ).strftime("%Y-%m-%d")

    prices = data.download_price_history(approved, data_start, config.END_DATE)
    cdi = data.download_cdi_daily(data_start, config.END_DATE)

    strategies, histories = {}, {}
    for method in ["equal_weight", "markowitz", "risk_parity"]:
        print(f"Rodando {method}...")
        strategies[method], histories[method] = run_strategy(prices, cdi, method)

    benchmarks = run_benchmarks(config.START_DATE, config.END_DATE)
    strategies, benchmarks = align_returns(strategies, benchmarks)

    start = max(s.index.min() for s in list(strategies.values()) + list(benchmarks.values()))
    end = min(s.index.max() for s in list(strategies.values()) + list(benchmarks.values()))
    rf = cdi.loc[start:end]

    rows = []
    for name, r in strategies.items():
        rows.append(metrics.summarize(r, histories[name], name, rf))
    for name, r in benchmarks.items():
        rows.append(metrics.summarize(r, [], name, rf))

    summary = pd.DataFrame(rows).set_index("estratégia")
    print(summary.to_string(float_format=lambda x: f"{x:.2%}"))
    summary.to_csv("walk_forward_summary.csv")

    fig, ax = plt.subplots(figsize=(11, 6))
    for name, r in {**strategies, **benchmarks}.items():
        ((1 + r).cumprod() - 1).plot(ax=ax, label=name)
    ax.set_title("Walk-Forward Backtest")
    ax.set_ylabel("Retorno acumulado")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.savefig("walk_forward_backtest.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    main()
