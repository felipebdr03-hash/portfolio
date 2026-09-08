import time
import requests
import pandas as pd
import yfinance as yf
import config

def fetch_fundamentals(ticker):
    info = yf.Ticker(ticker).info
    return {
        "ticker": ticker,
        "market_cap": info.get("marketCap"),
        "roe": info.get("returnOnEquity"),
        "debt_to_equity": info.get("debtToEquity"),
        "profit_margin": info.get("profitMargins"),
        "sector": info.get("sector"),
    }

def screen_universe(universe):
    approved = []
    for ticker in universe:
        try:
            f = fetch_fundamentals(ticker)
            ok = (
                f["market_cap"] is not None and f["market_cap"] >= config.MIN_MARKET_CAP
                and f["roe"] is not None and f["roe"] >= config.MIN_ROE
                and (f["debt_to_equity"] is None or f["debt_to_equity"] <= config.MAX_DEBT_TO_EQUITY)
                and f["profit_margin"] is not None and f["profit_margin"] >= config.MIN_PROFIT_MARGIN
            )
            if ok:
                approved.append(ticker)
        except Exception as e:
            print(f"aviso: falha em {ticker}: {e}")
        time.sleep(0.3)
    return approved

def download_price_history(tickers, start, end=None):
    data = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)["Close"]
    if isinstance(data, pd.Series):
        data = data.to_frame()
    data.index = pd.to_datetime(data.index)
    return data.sort_index().dropna(how="all")

def download_cdi_daily(start, end=None):
    start_dt = pd.Timestamp(start)
    end_dt = pd.Timestamp(end) if end else pd.Timestamp.today()
    url = (
        "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
        f"?formato=json&dataInicial={start_dt:%d/%m/%Y}&dataFinal={end_dt:%d/%m/%Y}"
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    df = pd.DataFrame(resp.json())
    if df.empty:
        raise RuntimeError("BCB não retornou CDI.")
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["valor"] = df["valor"].astype(float) / 100
    return df.set_index("data")["valor"].sort_index()

def annualized_cdi_until(cdi_daily, as_of_date, lookback_months):
    start = as_of_date - pd.DateOffset(months=lookback_months)
    window = cdi_daily.loc[start:as_of_date].dropna()
    if len(window) < 20:
        return 0.0
    accumulated = (1 + window).prod()
    years = (window.index[-1] - window.index[0]).days / 365.25
    return accumulated ** (1 / years) - 1 if years > 0 else 0.0
