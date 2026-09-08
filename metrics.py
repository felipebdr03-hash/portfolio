import numpy as np
import pandas as pd

def cagr(cum):
    years = (cum.index[-1] - cum.index[0]).days / 365.25
    return np.nan if years <= 0 else (1 + cum.iloc[-1]) ** (1 / years) - 1

def annualized_vol(r):
    return r.std() * np.sqrt(252)

def sharpe_ratio(r, rf):
    rf = rf.reindex(r.index).ffill()
    excess = (r - rf).dropna()
    return np.nan if len(excess) < 2 or excess.std() == 0 else excess.mean() / excess.std() * np.sqrt(252)

def sortino_ratio(r, rf):
    rf = rf.reindex(r.index).ffill()
    excess = (r - rf).dropna()
    downside = np.minimum(excess, 0)
    dd = np.sqrt(np.mean(downside ** 2))
    return np.nan if dd == 0 else excess.mean() / dd * np.sqrt(252)

def max_drawdown(cum):
    wealth = 1 + cum
    return ((wealth - wealth.cummax()) / wealth.cummax()).min()

def calmar_ratio(cum):
    mdd = max_drawdown(cum)
    return np.nan if mdd == 0 or np.isnan(mdd) else cagr(cum) / abs(mdd)

def turnover(history):
    if len(history) < 2:
        return 0.0
    vals = []
    for prev, curr in zip(history[:-1], history[1:]):
        tickers = set(prev.index) | set(curr.index)
        vals.append(sum(abs(curr.get(t, 0) - prev.get(t, 0)) for t in tickers) / 2)
    return float(np.mean(vals))

def summarize(r, history, label, rf):
    r = r.dropna()
    cum = (1 + r).cumprod() - 1
    return {
        "estratégia": label,
        "retorno_acumulado": cum.iloc[-1],
        "CAGR": cagr(cum),
        "vol_anualizada": annualized_vol(r),
        "sharpe": sharpe_ratio(r, rf),
        "sortino": sortino_ratio(r, rf),
        "max_drawdown": max_drawdown(cum),
        "calmar": calmar_ratio(cum),
        "turnover_medio": turnover(history),
    }
