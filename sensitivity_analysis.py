import pandas as pd
import config, data, metrics
import walk_forward_backtest as wf

TOP_N_VALUES = [5, 10, 12, 15, 20]
REBALANCE_FREQ_VALUES = ["ME", "QE", "6ME", "YE"]
MAX_WEIGHT_VALUES = [0.10, 0.15, 0.20, 0.25]

def run_one(prices, cdi, label):
    rows = []
    for method in ["equal_weight", "markowitz", "risk_parity"]:
        try:
            r, h = wf.run_strategy(prices, cdi, method)
            m = metrics.summarize(r, h, method, cdi)
            m["config"] = label
            rows.append(m)
        except Exception as e:
            print(f"falha {label}/{method}: {e}")
    return rows

def main():
    approved = data.screen_universe(config.UNIVERSE)
    start = (pd.Timestamp(config.START_DATE) - pd.DateOffset(months=config.LOOKBACK_MONTHS)).strftime("%Y-%m-%d")
    prices = data.download_price_history(approved, start, config.END_DATE)
    cdi = data.download_cdi_daily(start, config.END_DATE)

    original = config.TOP_N_ASSETS, config.REBALANCE_FREQ, config.MAX_WEIGHT_PER_ASSET
    rows = []

    for n in TOP_N_VALUES:
        config.TOP_N_ASSETS = n
        config.REBALANCE_FREQ = original[1]
        config.MAX_WEIGHT_PER_ASSET = original[2]
        rows += run_one(prices, cdi, f"top_n={n}")

    for freq in REBALANCE_FREQ_VALUES:
        config.TOP_N_ASSETS = original[0]
        config.REBALANCE_FREQ = freq
        config.MAX_WEIGHT_PER_ASSET = original[2]
        rows += run_one(prices, cdi, f"rebalance={freq}")

    for w in MAX_WEIGHT_VALUES:
        config.TOP_N_ASSETS = original[0]
        config.REBALANCE_FREQ = original[1]
        config.MAX_WEIGHT_PER_ASSET = w
        rows += run_one(prices, cdi, f"max_weight={w:.0%}")

    config.TOP_N_ASSETS, config.REBALANCE_FREQ, config.MAX_WEIGHT_PER_ASSET = original
    df = pd.DataFrame(rows)
    df.to_csv("sensitivity_results.csv", index=False)
    if not df.empty:
        print(df.pivot_table(index="config", columns="estratégia", values="sharpe").round(2))

if __name__ == "__main__":
    main()
