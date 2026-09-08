import numpy as np
import pandas as pd
import config

def compute_factor_scores(prices, as_of_date):
    prices = prices.loc[:as_of_date].copy()
    returns = prices.pct_change().dropna(how="all")
    if len(prices) < 253:
        momentum = pd.Series(np.nan, index=prices.columns)
    else:
        momentum = prices.iloc[-22] / prices.iloc[-253] - 1

    vol = returns.std() * np.sqrt(252)
    corr = returns.corr()
    if len(corr) <= 1:
        avg_corr = pd.Series(np.nan, index=prices.columns)
    else:
        avg_corr = (corr.sum() - 1) / (len(corr) - 1)

    df = pd.DataFrame({
        "momentum_12_1": momentum,
        "volatility": vol,
        "avg_correlation": avg_corr,
    })

    def zscore(s):
        std = s.std()
        return (s - s.mean()) / std if pd.notna(std) and std > 0 else pd.Series(0.0, index=s.index)

    df["z_momentum"] = zscore(df["momentum_12_1"])
    df["z_low_vol"] = -zscore(df["volatility"])
    df["z_low_corr"] = -zscore(df["avg_correlation"])

    w = config.FACTOR_WEIGHTS
    df["score"] = (
        w["momentum_12_1"] * df["z_momentum"]
        + w["low_vol"] * df["z_low_vol"]
        + w["low_corr"] * df["z_low_corr"]
    )
    return df.dropna(subset=["score"]).sort_values("score", ascending=False)

def select_top_assets(prices, as_of_date, top_n):
    return compute_factor_scores(prices, as_of_date).head(top_n).index.tolist()
