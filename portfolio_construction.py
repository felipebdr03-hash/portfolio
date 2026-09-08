import numpy as np
import pandas as pd
from scipy.optimize import minimize
from pypfopt import EfficientFrontier, risk_models, expected_returns
import config

def _validate_capacity(n):
    if n <= 0:
        raise ValueError("Nenhum ativo disponível.")
    if config.MAX_WEIGHT_PER_ASSET * n < 1:
        raise ValueError(
            f"MAX_WEIGHT_PER_ASSET={config.MAX_WEIGHT_PER_ASSET:.1%} "
            f"é incompatível com {n} ativos."
        )

def equal_weight(prices):
    _validate_capacity(len(prices.columns))
    return pd.Series(1 / len(prices.columns), index=prices.columns)

def markowitz_max_sharpe(prices, risk_free_rate):
    mu = expected_returns.mean_historical_return(prices)
    cov = risk_models.CovarianceShrinkage(prices).ledoit_wolf()
    ef = EfficientFrontier(mu, cov, weight_bounds=(0, config.MAX_WEIGHT_PER_ASSET))
    try:
        ef.max_sharpe(risk_free_rate=risk_free_rate)
    except Exception:
        ef = EfficientFrontier(mu, cov, weight_bounds=(0, config.MAX_WEIGHT_PER_ASSET))
        ef.min_volatility()
    return pd.Series(ef.clean_weights(), dtype=float)

def _risk_parity_objective(w, cov):
    variance = w @ cov @ w
    if variance <= 0:
        return 1e10
    vol = np.sqrt(variance)
    rc = w * (cov @ w) / vol
    target = vol / len(w)
    return np.sum((rc - target) ** 2)

def risk_parity(prices):
    returns = prices.pct_change().dropna()
    cov = returns.cov().values * 252
    n = len(prices.columns)
    _validate_capacity(n)

    result = minimize(
        _risk_parity_objective,
        np.ones(n) / n,
        args=(cov,),
        method="SLSQP",
        bounds=[(0, config.MAX_WEIGHT_PER_ASSET)] * n,
        constraints={"type": "eq", "fun": lambda w: np.sum(w) - 1},
        options={"maxiter": 1000, "ftol": 1e-10},
    )
    if not result.success:
        raise RuntimeError(f"Risk Parity não convergiu: {result.message}")
    return pd.Series(result.x, index=prices.columns, dtype=float)
