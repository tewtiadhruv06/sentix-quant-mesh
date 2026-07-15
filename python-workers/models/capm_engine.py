import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def calculate_beta(ticker, benchmark="SPY", years=2):
    """
    Calculate the Beta of an asset relative to a benchmark using daily
    logarithmic returns over the specified lookback period.

    Beta = Cov(Asset, Benchmark) / Var(Benchmark)

    Returns the computed beta, or 1.0 as a safe default on failure.
    """
    end_date = datetime.today()
    start_date = end_date - timedelta(days=years * 365)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    try:
        asset_data = yf.download(
            ticker, start=start_str, end=end_str, progress=False, auto_adjust=True
        )
        bench_data = yf.download(
            benchmark, start=start_str, end=end_str, progress=False, auto_adjust=True
        )
    except Exception as e:
        print(f"  [WARN] Failed to download price data for {ticker}/{benchmark}: {e}")
        return 1.0

    if asset_data.empty or bench_data.empty:
        print(f"  [WARN] Empty price history for {ticker} or {benchmark}. Defaulting beta to 1.0.")
        return 1.0

    # ── Extract Adj Close / Close and align on common dates ──────────
    if "Adj Close" in asset_data.columns:
        asset_prices = asset_data["Adj Close"].squeeze()
        bench_prices = bench_data["Adj Close"].squeeze()
    else:
        asset_prices = asset_data["Close"].squeeze()
        bench_prices = bench_data["Close"].squeeze()

    # Merge into a single DataFrame, forward-fill mismatched holidays
    combined = pd.DataFrame({
        "asset": asset_prices,
        "bench": bench_prices,
    }).ffill().dropna()

    if len(combined) < 30:
        print(f"  [WARN] Insufficient overlapping data ({len(combined)} days). Defaulting beta to 1.0.")
        return 1.0

    # ── Daily logarithmic returns ────────────────────────────────────
    combined["asset_ret"] = np.log(combined["asset"] / combined["asset"].shift(1))
    combined["bench_ret"] = np.log(combined["bench"] / combined["bench"].shift(1))
    combined = combined.dropna()

    if combined.empty:
        print(f"  [WARN] No valid returns for {ticker}. Defaulting beta to 1.0.")
        return 1.0

    # ── Covariance / Variance ────────────────────────────────────────
    cov_matrix = np.cov(combined["asset_ret"], combined["bench_ret"])
    covariance = cov_matrix[0, 1]
    variance = cov_matrix[1, 1]

    if variance == 0 or np.isnan(variance):
        print(f"  [WARN] Zero or NaN benchmark variance. Defaulting beta to 1.0.")
        return 1.0

    beta = covariance / variance
    return float(beta)


def get_risk_free_rate():
    """
    Fetch the live 10-Year US Treasury Yield from Yahoo Finance (^TNX).
    Yahoo returns the yield as a percentage (e.g. 4.25), so we divide
    by 100 to return a decimal (0.0425).

    Defaults to 4.0% (0.04) on failure.
    """
    default_rate = 0.04

    try:
        tnx = yf.Ticker("^TNX")
        info = tnx.info
        yield_pct = info.get("regularMarketPrice") or info.get("previousClose")

        if yield_pct is None or yield_pct <= 0:
            print("  [WARN] Could not extract 10-Yr yield. Defaulting to 4.0%.")
            return default_rate

        return float(yield_pct) / 100.0

    except Exception as e:
        print(f"  [WARN] Failed to fetch risk-free rate: {e}. Defaulting to 4.0%.")
        return default_rate


def calculate_cost_of_equity(ticker):
    """
    CAPM: Cost of Equity = Risk-Free Rate + Beta * Equity Risk Premium

    Returns a dictionary with beta, risk_free_rate, erp, and cost_of_equity.
    """
    erp = 0.055  # Equity Risk Premium = 5.5%

    beta = calculate_beta(ticker)
    rf = get_risk_free_rate()
    coe = rf + beta * erp

    return {
        "beta": beta,
        "risk_free_rate": rf,
        "erp": erp,
        "cost_of_equity": coe,
    }


if __name__ == "__main__":
    test_tickers = ["AAPL", "TSLA"]

    print("=" * 65)
    print("  CAPM Engine — Cost of Equity Calculator")
    print("=" * 65)
    print("  Model   : Capital Asset Pricing Model (CAPM)")
    print("  Benchmark: S&P 500 (SPY)")
    print("  Lookback : 2 Years Daily Returns")
    print("  ERP      : 5.5%")
    print("=" * 65)

    results = []

    for ticker in test_tickers:
        print(f"\n{'─' * 50}")
        print(f"  Processing: {ticker}")
        print(f"{'─' * 50}")

        capm = calculate_cost_of_equity(ticker)
        results.append({"ticker": ticker, **capm})

    # ── Formatted results table ──────────────────────────────────────
    print("\n")
    print("=" * 65)
    print("  CAPM RESULTS SUMMARY")
    print("=" * 65)

    header = (
        f"{'Ticker':<10}"
        f"{'Beta':>10}"
        f"{'10-Yr Yield':>15}"
        f"{'ERP':>10}"
        f"{'Cost of Equity':>18}"
    )
    print(header)
    print("─" * 65)

    for r in results:
        beta_str = f"{r['beta']:.4f}"
        rf_str = f"{r['risk_free_rate'] * 100:.2f}%"
        erp_str = f"{r['erp'] * 100:.1f}%"
        coe_str = f"{r['cost_of_equity'] * 100:.2f}%"

        line = (
            f"{r['ticker']:<10}"
            f"{beta_str:>10}"
            f"{rf_str:>15}"
            f"{erp_str:>10}"
            f"{coe_str:>18}"
        )
        print(line)

    print("─" * 65)
    print("  Formula: CoE = Rf + β × ERP")
    print("=" * 65)
