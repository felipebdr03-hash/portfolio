import pandas as pd
import config, data, metrics
import walk_forward_backtest as wf

PERIODS = [
    ("2014-01-01", "2018-12-31", "2014-2018"),
    ("2019-01-01", "2021-12-31", "2019-2021"),
    ("2022-01-01", "2024-12-31", "2022-2024"),
    ("2025-01-01", None, "2025-atual"),
]

def main():
    original = config.START_DATE, config.END_DATE
    earliest = min(pd.Timestamp(p[0]) for p in PERIODS)
    data_start = (earliest - pd.DateOffset(months=config.LOOKBACK_MONTHS)).strftime("%Y-%m-%d")

    approved = data.screen_universe(config.UNIVERSE)
    prices = data.download_price_history(approved, data_start, None)
    cdi_full = data.download_cdi_daily(data_start, None)

    rows = []
    for start, end, label in PERIODS:
        config.START_DATE, config.END_DATE = start, end
        cdi = cdi_full.loc[pd.Timestamp(start):(pd.Timestamp(end) if end else cdi_full.index.max())]

        for method in ["equal_weight", "markowitz", "risk_parity"]:
            try:
                r, h = wf.run_strategy(prices, cdi, method)
                common_start = max(r.index.min(), cdi.index.min())
                common_end = min(r.index.max(), cdi.index.max())
                r = r.loc[common_start:common_end]
                rf = cdi.loc[common_start:common_end]
                m = metrics.summarize(r, h, method, rf)
                m["periodo"] = label
                rows.append(m)
                print(f"{label} | {method} | Sharpe={m['sharpe']:.2f} | CAGR={m['CAGR']:.1%}")
            except Exception as e:
                print(f"falha {label}/{method}: {e}")

    config.START_DATE, config.END_DATE = original
    df = pd.DataFrame(rows)
    df.to_csv("multi_period_results.csv", index=False)
    if not df.empty:
        print(df.pivot_table(index="periodo", columns="estratégia", values="sharpe").round(2))

if __name__ == "__main__":
    main()
