import sys
import os
import json
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from urllib.parse import quote

# ── Allow imports from the models/ directory ─────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKER_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(WORKER_ROOT, "models"))

from quant_cli import resolve_ticker

# ═════════════════════════════════════════════════════════════════
#  API Endpoints
# ═════════════════════════════════════════════════════════════════
EQUITY_API = "http://127.0.0.1:8080/api/v1/equities"
FINANCIAL_API = "http://127.0.0.1:8080/api/v1/financials"


# ═════════════════════════════════════════════════════════════════
#  DATA LAYER — Fetch & Merge from Java APIs
# ═════════════════════════════════════════════════════════════════

def fetch_merged_dataframe():
    """
    GET both API endpoints, merge on equityId, and return a single DataFrame
    with ticker + all financial record fields.
    """
    equity_resp = requests.get(EQUITY_API)
    equity_resp.raise_for_status()
    equities = equity_resp.json()

    financial_resp = requests.get(FINANCIAL_API)
    financial_resp.raise_for_status()
    financials = financial_resp.json()

    eq_df = pd.DataFrame(equities)
    fin_df = pd.DataFrame(financials)

    if eq_df.empty or fin_df.empty:
        print("[ERROR] One or both API responses returned empty data.")
        return pd.DataFrame()

    merged = pd.merge(
        fin_df,
        eq_df[["equityId", "ticker"]],
        on="equityId",
        how="inner",
    )

    print(f"  [INFO] Merged {len(merged)} financial records with equity tickers.")
    return merged


# ═════════════════════════════════════════════════════════════════
#  GROWTH MODEL — Historical Revenue CAGR
# ═════════════════════════════════════════════════════════════════

def calculate_historical_cagr(ticker_symbol):
    """
    Calculate the 3-Year Revenue CAGR from yfinance annual financials.
    Capped at 35%, floored at 2%, defaults to 5% on any failure.
    """
    default_cagr = 0.05

    try:
        stock = yf.Ticker(ticker_symbol)
        financials = stock.financials

        if financials is None or financials.empty:
            print(f"  [WARN] No financials for {ticker_symbol}. Using default CAGR.")
            return default_cagr

        if "Total Revenue" not in financials.index:
            print(f"  [WARN] 'Total Revenue' missing for {ticker_symbol}. Using default CAGR.")
            return default_cagr

        revenue_row = financials.loc["Total Revenue"].dropna().sort_index()

        if len(revenue_row) < 2:
            print(f"  [WARN] Insufficient revenue history for {ticker_symbol}. Using default CAGR.")
            return default_cagr

        current_rev = float(revenue_row.iloc[-1])
        years_back = min(3, len(revenue_row) - 1)
        old_rev = float(revenue_row.iloc[-(years_back + 1)])

        if old_rev <= 0 or current_rev <= 0:
            print(f"  [WARN] Non-positive revenue for {ticker_symbol}. Using default CAGR.")
            return default_cagr

        cagr = (current_rev / old_rev) ** (1.0 / years_back) - 1.0
        cagr = max(0.02, min(0.35, cagr))
        return cagr

    except (ZeroDivisionError, ValueError, TypeError, KeyError) as e:
        print(f"  [WARN] CAGR calculation failed for {ticker_symbol}: {e}. Using default.")
        return default_cagr
    except Exception as e:
        print(f"  [WARN] Unexpected error for {ticker_symbol}: {e}. Using default CAGR.")
        return default_cagr


# ═════════════════════════════════════════════════════════════════
#  RISK MODEL — CAPM with Dynamic ERP
# ═════════════════════════════════════════════════════════════════

def calculate_beta(ticker, benchmark="SPY", years=2):
    """
    Calculate Beta using 2-year daily log returns vs SPY.
    Beta = Cov(Asset, Benchmark) / Var(Benchmark).
    Defaults to 1.0 on failure.
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

    if "Adj Close" in asset_data.columns:
        asset_prices = asset_data["Adj Close"].squeeze()
        bench_prices = bench_data["Adj Close"].squeeze()
    else:
        asset_prices = asset_data["Close"].squeeze()
        bench_prices = bench_data["Close"].squeeze()

    combined = pd.DataFrame({
        "asset": asset_prices,
        "bench": bench_prices,
    }).ffill().dropna()

    if len(combined) < 30:
        print(f"  [WARN] Insufficient overlapping data ({len(combined)} days). Defaulting beta to 1.0.")
        return 1.0

    combined["asset_ret"] = np.log(combined["asset"] / combined["asset"].shift(1))
    combined["bench_ret"] = np.log(combined["bench"] / combined["bench"].shift(1))
    combined = combined.dropna()

    if combined.empty:
        print(f"  [WARN] No valid returns for {ticker}. Defaulting beta to 1.0.")
        return 1.0

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
    Returns decimal form (e.g. 0.0425 for 4.25%). Defaults to 4.0%.
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


def calculate_dynamic_erp():
    """
    Calculate a dynamic, historical Equity Risk Premium (ERP):
      1. Fetch 10 years of monthly SPY prices from yfinance.
      2. Compute the 10-Year Market CAGR.
      3. Subtract the live 10-Year Treasury yield (Rf).
      4. Clamp the result: floor = 4.0%, cap = 8.0%.

    Returns a dict with market_cagr, rf, raw_erp, clamped_erp,
    and a methodology string for the Explainability Matrix.
    Defaults to 5.0% ERP on failure.
    """
    default_erp = 0.05

    # ── Step 1: Fetch 10 years of monthly SPY data ───────────────────
    try:
        end_date = datetime.today()
        start_date = end_date - timedelta(days=10 * 365)

        spy_data = yf.download(
            "SPY",
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            interval="1mo",
            progress=False,
            auto_adjust=True,
        )

        if spy_data is None or spy_data.empty or len(spy_data) < 12:
            print("  [WARN] Insufficient SPY monthly data. Defaulting ERP to 5.0%.")
            return {
                "market_cagr": None,
                "rf": get_risk_free_rate(),
                "raw_erp": default_erp,
                "clamped_erp": default_erp,
                "methodology": "Static fallback (5.0%) — SPY data unavailable",
            }

    except Exception as e:
        print(f"  [WARN] Failed to fetch SPY data: {e}. Defaulting ERP to 5.0%.")
        return {
            "market_cagr": None,
            "rf": get_risk_free_rate(),
            "raw_erp": default_erp,
            "clamped_erp": default_erp,
            "methodology": f"Static fallback (5.0%) — Network error: {e}",
        }

    # ── Step 2: Extract oldest and most recent prices ────────────────
    if "Adj Close" in spy_data.columns:
        price_col = spy_data["Adj Close"].squeeze()
    else:
        price_col = spy_data["Close"].squeeze()

    oldest_price = float(price_col.dropna().iloc[0])
    current_price = float(price_col.dropna().iloc[-1])

    if oldest_price <= 0 or current_price <= 0:
        print("  [WARN] Non-positive SPY price detected. Defaulting ERP to 5.0%.")
        return {
            "market_cagr": None,
            "rf": get_risk_free_rate(),
            "raw_erp": default_erp,
            "clamped_erp": default_erp,
            "methodology": "Static fallback (5.0%) — Invalid SPY prices",
        }

    # ── Step 3: Calculate 10-Year Market CAGR ────────────────────────
    market_cagr = (current_price / oldest_price) ** (1.0 / 10.0) - 1.0

    # ── Step 4: Fetch Rf and compute raw ERP ─────────────────────────
    rf = get_risk_free_rate()
    raw_erp = market_cagr - rf

    # ── Step 5: Clamp ERP to [4.0%, 8.0%] ────────────────────────────
    clamped_erp = max(0.04, min(0.08, raw_erp))

    # ── Build methodology string for Explainability Matrix ───────────
    clamp_note = ""
    if raw_erp < 0.04:
        clamp_note = " (floored from raw)"
    elif raw_erp > 0.08:
        clamp_note = " (capped from raw)"

    methodology = (
        f"10Y SPY CAGR: {market_cagr * 100:.2f}% — "
        f"Rf (^TNX): {rf * 100:.2f}% — "
        f"Raw ERP: {raw_erp * 100:.2f}% → "
        f"Clamped ERP: {clamped_erp * 100:.2f}%{clamp_note}"
    )

    return {
        "market_cagr": market_cagr,
        "rf": rf,
        "raw_erp": raw_erp,
        "clamped_erp": clamped_erp,
        "methodology": methodology,
    }


def calculate_cost_of_equity(ticker, erp):
    """
    CAPM: Cost of Equity = Risk-Free Rate + Beta * ERP
    Uses the dynamic ERP passed in from calculate_dynamic_erp().
    """
    beta = calculate_beta(ticker)
    rf = get_risk_free_rate()
    coe = rf + beta * erp

    return {
        "beta": beta,
        "risk_free_rate": rf,
        "erp": erp,
        "cost_of_equity": coe,
    }


# ═════════════════════════════════════════════════════════════════
#  DCF MODEL — Intrinsic Value Calculation
# ═════════════════════════════════════════════════════════════════

def extract_dcf_inputs(row):
    """
    Extract and normalize all financial inputs needed for DCF from
    a financial record dict/row. Returns a flat dict.
    """
    ebit = float(row.get("ebit", 0) or 0)
    tax_provision = abs(float(row.get("taxProvision", 0) or 0))
    dep_amort = float(row.get("depreciationAmortization", 0) or 0)
    capex = abs(float(row.get("capitalExpenditure", 0) or 0))
    cash = float(row.get("cashAndEquivalents", 0) or 0)
    current_debt = float(row.get("currentDebt", 0) or 0)
    long_term_debt = float(row.get("longTermDebt", 0) or 0)
    shares_outstanding = float(row.get("sharesOutstanding", 0) or 0)

    base_fcff = ebit - tax_provision + dep_amort - capex

    return {
        "base_fcff": base_fcff,
        "cash": cash,
        "current_debt": current_debt,
        "long_term_debt": long_term_debt,
        "shares_outstanding": shares_outstanding,
    }


def monte_carlo_dcf(row, cagr, wacc_mean, tgr_mean=0.025,
                    wacc_std=0.01, tgr_std=0.005, iterations=10000):
    """
    10,000-iteration Monte Carlo DCF using fully vectorized numpy.

    Stochastic parameters:
      - WACC ~ N(wacc_mean, wacc_std)
      - TGR  ~ N(tgr_mean, tgr_std), clamped so TGR < WACC - 0.01

    Returns a dict with:
      - base_fcff, percentile prices (p10, p50, p90),
      - median enterprise/equity values, and simulation metadata.
    """
    inputs = extract_dcf_inputs(row)
    base_fcff = inputs["base_fcff"]
    cash = inputs["cash"]
    current_debt = inputs["current_debt"]
    long_term_debt = inputs["long_term_debt"]
    shares = inputs["shares_outstanding"]

    # ── Generate stochastic parameter arrays ─────────────────────
    np.random.seed(42)  # Reproducible results
    wacc_sims = np.random.normal(wacc_mean, wacc_std, iterations)
    tgr_sims = np.random.normal(tgr_mean, tgr_std, iterations)

    # Clamp: WACC >= 4%, TGR must be < WACC - 1% to prevent
    # infinite/negative Gordon Growth Model valuations
    wacc_sims = np.maximum(wacc_sims, 0.04)
    tgr_sims = np.minimum(tgr_sims, wacc_sims - 0.01)
    tgr_sims = np.maximum(tgr_sims, 0.005)  # Floor TGR at 0.5%

    # ── Build tapered growth rates: shape (iterations, 5) ────────
    # Year 1 = cagr, Year 5 = tgr_sims[i], linear taper
    steps = (cagr - tgr_sims) / 4.0  # shape (iterations,)
    year_offsets = np.arange(5).reshape(1, 5)  # shape (1, 5)
    growth_matrix = cagr - steps.reshape(-1, 1) * year_offsets  # (iterations, 5)

    # ── Project 5 years of FCFF: shape (iterations, 5) ───────────
    # cumulative_growth[i, y] = product of (1 + g) from year 0..y
    cumulative_growth = np.cumprod(1.0 + growth_matrix, axis=1)  # (iterations, 5)
    projected_fcffs = base_fcff * cumulative_growth  # (iterations, 5)

    # ── Discount factors: shape (iterations, 5) ──────────────────
    years = np.arange(1, 6).reshape(1, 5)  # (1, 5)
    discount_factors = (1.0 + wacc_sims.reshape(-1, 1)) ** years  # (iterations, 5)

    # ── PV of projected FCFFs ────────────────────────────────────
    pv_fcffs = projected_fcffs / discount_factors  # (iterations, 5)
    sum_pv_fcffs = np.sum(pv_fcffs, axis=1)  # (iterations,)

    # ── Terminal Value (Gordon Growth Model) ──────────────────────
    year5_fcff = projected_fcffs[:, 4]  # (iterations,)
    terminal_value = (year5_fcff * (1.0 + tgr_sims)) / (wacc_sims - tgr_sims)
    pv_terminal = terminal_value / ((1.0 + wacc_sims) ** 5)

    # ── Enterprise Value → Equity Value → Implied Price ──────────
    ev_array = sum_pv_fcffs + pv_terminal
    equity_array = ev_array + cash - current_debt - long_term_debt

    if shares <= 0:
        price_array = np.zeros(iterations)
    else:
        price_array = equity_array / shares

    # ── Percentile extraction ────────────────────────────────────
    p10 = float(np.percentile(price_array, 10))
    p50 = float(np.percentile(price_array, 50))
    p90 = float(np.percentile(price_array, 90))

    return {
        "base_fcff": base_fcff,
        "bear_price": p10,
        "base_price": p50,
        "bull_price": p90,
        "median_ev": float(np.median(ev_array)),
        "median_equity": float(np.median(equity_array)),
        "iterations": iterations,
        "wacc_mean": wacc_mean,
        "wacc_std": wacc_std,
        "tgr_mean": tgr_mean,
        "tgr_std": tgr_std,
        "price_std": float(np.std(price_array)),
    }


# ═════════════════════════════════════════════════════════════════
#  UTILITIES
# ═════════════════════════════════════════════════════════════════

def get_current_market_price(ticker_symbol):
    """Fetch the current market price via yfinance. Returns 0.0 on failure."""
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
        return float(price)
    except Exception:
        return 0.0


def format_large_number(value):
    """Format large numbers into human-readable strings (B/M)."""
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1e9:
        return f"{sign}${abs_val / 1e9:.2f}B"
    elif abs_val >= 1e6:
        return f"{sign}${abs_val / 1e6:.2f}M"
    else:
        return f"{sign}${abs_val:,.2f}"


def safe_get(dataframe, label, default=0.0):
    """
    Safely extract the most recent annual column value from a yfinance
    DataFrame. Returns default if the label is missing or the value is NaN.
    """
    try:
        if label in dataframe.index:
            value = dataframe.loc[label].iloc[0]
            if pd.isna(value):
                return default
            return float(value)
        return default
    except (IndexError, KeyError, TypeError):
        return default


# ═════════════════════════════════════════════════════════════════
#  ON-DEMAND EQUITY & FINANCIAL REGISTRATION
# ═════════════════════════════════════════════════════════════════

def ensure_equity_registered(ticker_symbol):
    """
    Check if the ticker exists in the Java API. If not, register it
    by pulling corporate profile data from yfinance.
    Returns the equityId on success, or None on failure.
    """
    # Check existing equities
    try:
        resp = requests.get(EQUITY_API)
        resp.raise_for_status()
        for eq in resp.json():
            if eq["ticker"] == ticker_symbol.upper():
                return eq["equityId"]
    except Exception as e:
        print(f"  [WARN] Failed to query equities API: {e}")
        return None

    # Not found — register via yfinance
    print(f"  [~] Registering {ticker_symbol} in equity registry...")
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        long_name = info.get("longName", ticker_symbol.upper())
        sector = info.get("sector", "Unknown")
        exchange = info.get("exchange", "Unknown")

        payload = {
            "ticker": ticker_symbol.upper(),
            "companyName": long_name,
            "sector": sector,
            "exchange": exchange,
            "isActive": True,
        }
        headers = {"Content-Type": "application/json"}
        resp = requests.post(EQUITY_API, json=payload, headers=headers)

        if resp.status_code in (201, 409):
            # Fetch the ID back
            resp2 = requests.get(EQUITY_API)
            resp2.raise_for_status()
            for eq in resp2.json():
                if eq["ticker"] == ticker_symbol.upper():
                    print(f"  [OK] {ticker_symbol} registered (equityId={eq['equityId']}).")
                    return eq["equityId"]
        else:
            print(f"  [ERROR] Equity registration failed: HTTP {resp.status_code}")
            return None
    except Exception as e:
        print(f"  [ERROR] Failed to register equity: {e}")
        return None


def ensure_financial_record(ticker_symbol, equity_id):
    """
    Fetch and POST the most recent annual financial data for the ticker
    to the Java API. Returns the financial record dict, or None on failure.
    """
    print(f"  [~] Fetching financial statements for {ticker_symbol}...")

    stock = yf.Ticker(ticker_symbol)

    try:
        financials = stock.financials
    except Exception:
        financials = pd.DataFrame()
    try:
        balance_sheet = stock.balance_sheet
    except Exception:
        balance_sheet = pd.DataFrame()
    try:
        cashflow = stock.cashflow
    except Exception:
        cashflow = pd.DataFrame()

    total_revenue = safe_get(financials, "Total Revenue")
    ebit = safe_get(financials, "EBIT")
    interest_expense = safe_get(financials, "Interest Expense")
    pretax_income = safe_get(financials, "Pretax Income")
    tax_provision = safe_get(financials, "Tax Provision")
    cash_and_equivalents = safe_get(balance_sheet, "Cash And Cash Equivalents")
    current_debt = safe_get(balance_sheet, "Current Debt")
    long_term_debt = safe_get(balance_sheet, "Long Term Debt")
    capital_expenditure = safe_get(cashflow, "Capital Expenditure")
    depreciation_amortization = safe_get(cashflow, "Depreciation And Amortization")
    shares_outstanding = safe_get(balance_sheet, "Ordinary Shares Number")
    if shares_outstanding == 0.0:
        shares_outstanding = safe_get(balance_sheet, "Share Issued")

    payload = {
        "equityId": equity_id,
        "fiscalYear": datetime.today().year,
        "fiscalQuarter": 4,
        "totalRevenue": total_revenue,
        "ebit": ebit,
        "interestExpense": interest_expense,
        "pretaxIncome": pretax_income,
        "taxProvision": tax_provision,
        "cashAndEquivalents": cash_and_equivalents,
        "currentDebt": current_debt,
        "longTermDebt": long_term_debt,
        "capitalExpenditure": capital_expenditure,
        "depreciationAmortization": depreciation_amortization,
        "sharesOutstanding": int(shares_outstanding),
    }

    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(FINANCIAL_API, json=payload, headers=headers)
        if resp.status_code == 201:
            print(f"  [OK] Financial record posted for {ticker_symbol}.")
            return resp.json()
        else:
            print(f"  [WARN] Financial POST returned HTTP {resp.status_code}: {resp.text}")
            return payload  # Use local data as fallback
    except Exception as e:
        print(f"  [WARN] Failed to POST financial record: {e}. Using local data.")
        return payload


# ═════════════════════════════════════════════════════════════════
#  COST OF DEBT & WACC
# ═════════════════════════════════════════════════════════════════

def calculate_effective_tax_rate(pretax_income, tax_provision):
    """
    Effective Tax Rate = |Tax Provision| / |Pretax Income|.
    Clamped to [0%, 40%]. Defaults to 21% (US statutory) on failure.
    """
    try:
        pretax = abs(float(pretax_income or 0))
        tax = abs(float(tax_provision or 0))
        if pretax <= 0:
            return 0.21
        rate = tax / pretax
        return max(0.0, min(0.40, rate))
    except (ZeroDivisionError, ValueError, TypeError):
        return 0.21


def calculate_cost_of_debt(interest_expense, current_debt, long_term_debt):
    """
    Cost of Debt = |Interest Expense| / Total Debt.
    Clamped to [1%, 15%]. Defaults to 5% if total debt is zero.
    """
    try:
        interest = abs(float(interest_expense or 0))
        total_debt = abs(float(current_debt or 0)) + abs(float(long_term_debt or 0))
        if total_debt <= 0:
            return 0.05
        cod = interest / total_debt
        return max(0.01, min(0.15, cod))
    except (ZeroDivisionError, ValueError, TypeError):
        return 0.05


def calculate_wacc(cost_of_equity, cost_of_debt, tax_rate,
                   market_cap, total_debt):
    """
    WACC = (E/V × CoE) + (D/V × CoD × (1 - Tax Rate))
    where V = E + D (total firm value).
    Defaults to cost_of_equity if debt is negligible.
    """
    try:
        e = abs(float(market_cap or 0))
        d = abs(float(total_debt or 0))
        v = e + d
        if v <= 0:
            return cost_of_equity
        wacc = (e / v) * cost_of_equity + (d / v) * cost_of_debt * (1.0 - tax_rate)
        return max(0.04, min(0.25, wacc))
    except (ZeroDivisionError, ValueError, TypeError):
        return cost_of_equity


# ═════════════════════════════════════════════════════════════════
#  SECTOR DETECTION & RELATIVE VALUATION (COMPS)
# ═════════════════════════════════════════════════════════════════

FINANCIAL_SECTORS = ["Financial Services", "Real Estate"]


def get_sector(ticker_symbol):
    """
    Fetch the sector string for a given ticker from yfinance.
    Returns the sector string, or 'Unknown' on failure.
    """
    try:
        info = yf.Ticker(ticker_symbol).info
        return info.get("sector", "Unknown")
    except Exception as e:
        print(f"  [WARN] Could not fetch sector for {ticker_symbol}: {e}")
        return "Unknown"


def relative_valuation_comps(target_ticker, peer_tickers, market_price, W=90):
    """
    Relative Valuation via Comparable Companies (P/E + P/B).
    Used for Financial Services and Real Estate sectors where
    traditional DCF cash-flow mechanics are structurally invalid.

    Returns a dict with all comps data and the blended implied price,
    or None on failure.
    """
    print()
    print("┌" + "─" * W + "┐")
    print("│" + "  PANEL 5 │ RELATIVE VALUATION (COMPS)".ljust(W) + "│")
    print("└" + "─" * W + "┘")

    # ── Fetch peer multiples ─────────────────────────────────────
    peer_data = []
    for pt in peer_tickers:
        try:
            info = yf.Ticker(pt).info
            pe = info.get("trailingPE")
            pb = info.get("priceToBook")

            if pe is not None and pb is not None and pe > 0 and pb > 0:
                peer_data.append({"ticker": pt, "pe": float(pe), "pb": float(pb)})
                print(f"  [OK] {pt:>6} — P/E: {pe:.2f}  P/B: {pb:.2f}")
            else:
                print(f"  [SKIP] {pt:>6} — Invalid multiples (P/E={pe}, P/B={pb})")
        except Exception as e:
            print(f"  [SKIP] {pt:>6} — Fetch error: {e}")

    if len(peer_data) < 2:
        print("  [✗] Insufficient valid peers (need at least 2). Cannot run comps.")
        return None

    pe_values = np.array([p["pe"] for p in peer_data])
    pb_values = np.array([p["pb"] for p in peer_data])
    median_pe = float(np.median(pe_values))
    median_pb = float(np.median(pb_values))

    print(f"\n  Median Peer P/E  : {median_pe:.2f}")
    print(f"  Median Peer P/B  : {median_pb:.2f}")

    # ── Fetch target multiples ───────────────────────────────────
    try:
        target_info = yf.Ticker(target_ticker).info
        target_eps = target_info.get("trailingEps")
        target_pb = target_info.get("priceToBook")
    except Exception as e:
        print(f"  [✗] Failed to fetch target info: {e}")
        return None

    # ── Implied Price via P/E ────────────────────────────────────
    implied_pe = None
    if target_eps is not None and target_eps > 0:
        implied_pe = target_eps * median_pe
        print(f"\n  Target EPS       : ${target_eps:.2f}")
        print(f"  Implied (P/E)    : ${implied_pe:.2f}")
    else:
        print(f"\n  [WARN] Target EPS unavailable or negative. P/E valuation skipped.")

    # ── Implied Price via P/B ────────────────────────────────────
    implied_pb = None
    if target_pb is not None and target_pb > 0 and market_price > 0:
        # Book Value Per Share = Market Price / P/B
        bvps = market_price / target_pb
        implied_pb = bvps * median_pb
        print(f"  Target P/B       : {target_pb:.2f}")
        print(f"  Book Val/Share   : ${bvps:.2f}")
        print(f"  Implied (P/B)    : ${implied_pb:.2f}")
    else:
        print(f"  [WARN] Target P/B unavailable. P/B valuation skipped.")

    # ── Blended Relative Implied Price ───────────────────────────
    valid_implied = [v for v in [implied_pe, implied_pb] if v is not None]
    if not valid_implied:
        print("  [✗] Could not compute any implied price. Comps failed.")
        return None

    blended = float(np.mean(valid_implied))

    print(f"\n  ┌─────────────────────────────────────────────┐")
    blended_str = f"${blended:.2f}"
    print(f"  │  Blended Relative Implied :  {blended_str:>12}  │")
    print(f"  └─────────────────────────────────────────────┘")
    print(f"  Market Price     : ${market_price:.2f}")

    return {
        "peer_data": peer_data,
        "median_pe": median_pe,
        "median_pb": median_pb,
        "target_eps": target_eps,
        "target_pb": target_pb,
        "implied_pe": implied_pe,
        "implied_pb": implied_pb,
        "blended_price": blended,
    }


# ═════════════════════════════════════════════════════════════════
#  MAIN EXECUTION PIPELINE — Interactive Single-Asset CLI
# ═════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    W = 90  # Panel width

    print()
    print("╔" + "═" * W + "╗")
    print("║" + "  SENTIX TERMINAL — Quantitative Valuation Engine".center(W) + "║")
    print("║" + "  Interactive Single-Asset Analysis Mode".center(W) + "║")
    print("╚" + "═" * W + "╝")

    while True:
        query = input("\n[?] Enter Company Name (or 'exit' to quit): ").strip()

        if not query:
            print("  [!] Empty input. Please enter a valid company name.")
            continue

        if query.lower() == "exit":
            print()
            print("╔" + "═" * W + "╗")
            print("║" + "  Session terminated. Goodbye.".center(W) + "║")
            print("╚" + "═" * W + "╝")
            break

        # ══════════════════════════════════════════════════════════
        #  PANEL 0: NLP TICKER RESOLUTION
        # ══════════════════════════════════════════════════════════
        print()
        print("┌" + "─" * W + "┐")
        print("│" + "  PANEL 0 │ NLP TICKER RESOLUTION".ljust(W) + "│")
        print("└" + "─" * W + "┘")

        resolved = resolve_ticker(query)
        if resolved is None:
            print(f"  [✗] Could not resolve \"{query}\". Try a different name.")
            continue

        ticker = resolved["ticker"]
        company_name = resolved["name"]
        exchange = resolved["exchange"]

        print(f"  [+] ASSET LOCKED: {company_name} | Ticker: {ticker} | Exchange: {exchange}")

        # ══════════════════════════════════════════════════════════
        #  PANEL 1: DATA PROVISIONING (Equity + Financials)
        # ══════════════════════════════════════════════════════════
        print()
        print("┌" + "─" * W + "┐")
        print("│" + "  PANEL 1 │ DATA PROVISIONING".ljust(W) + "│")
        print("└" + "─" * W + "┘")

        equity_id = ensure_equity_registered(ticker)
        if equity_id is None:
            print(f"  [✗] Failed to register {ticker}. Skipping.")
            continue

        fin_record = ensure_financial_record(ticker, equity_id)
        if fin_record is None:
            print(f"  [✗] Failed to fetch financials for {ticker}. Skipping.")
            continue

        # ══════════════════════════════════════════════════════════
        #  PANEL 2: DYNAMIC ERP
        # ══════════════════════════════════════════════════════════
        print()
        print("┌" + "─" * W + "┐")
        print("│" + "  PANEL 2 │ DYNAMIC EQUITY RISK PREMIUM".ljust(W) + "│")
        print("└" + "─" * W + "┘")

        erp_result = calculate_dynamic_erp()
        dynamic_erp = erp_result["clamped_erp"]
        print(f"  [OK] Dynamic ERP resolved: {dynamic_erp * 100:.2f}%")

        # ══════════════════════════════════════════════════════════
        #  PANEL 3: RISK MODEL (CAPM + Cost of Debt + WACC)
        # ══════════════════════════════════════════════════════════
        print()
        print("┌" + "─" * W + "┐")
        print("│" + "  PANEL 3 │ RISK MODEL — CAPM + WACC".ljust(W) + "│")
        print("└" + "─" * W + "┘")

        # CAPM Cost of Equity
        capm = calculate_cost_of_equity(ticker, dynamic_erp)
        coe = capm["cost_of_equity"]
        beta = capm["beta"]
        rf = capm["risk_free_rate"]

        # Cost of Debt
        interest_exp = float(fin_record.get("interestExpense", 0) or 0)
        cur_debt = float(fin_record.get("currentDebt", 0) or 0)
        lt_debt = float(fin_record.get("longTermDebt", 0) or 0)
        total_debt = abs(cur_debt) + abs(lt_debt)
        cod = calculate_cost_of_debt(interest_exp, cur_debt, lt_debt)

        # Effective Tax Rate
        pretax_inc = float(fin_record.get("pretaxIncome", 0) or 0)
        tax_prov = float(fin_record.get("taxProvision", 0) or 0)
        eff_tax = calculate_effective_tax_rate(pretax_inc, tax_prov)

        # Market Cap estimate (shares × current price)
        shares = float(fin_record.get("sharesOutstanding", 0) or 0)
        market_price = get_current_market_price(ticker)
        market_cap = shares * market_price if shares > 0 and market_price > 0 else 0.0

        # Fully Levered WACC
        wacc = calculate_wacc(coe, cod, eff_tax, market_cap, total_debt)

        print(f"  Beta            : {beta:.4f}")
        print(f"  Cost of Equity  : {coe * 100:.2f}%")
        print(f"  Cost of Debt    : {cod * 100:.2f}%")
        print(f"  Effective Tax   : {eff_tax * 100:.2f}%")
        print(f"  Fully Levered WACC : {wacc * 100:.2f}%")

        # ══════════════════════════════════════════════════════════
        #  PANEL 4: SECTOR DETECTION & ROUTING
        # ══════════════════════════════════════════════════════════
        print()
        print("┌" + "─" * W + "┐")
        print("│" + "  PANEL 4 │ SECTOR DETECTION & VALUATION ROUTING".ljust(W) + "│")
        print("└" + "─" * W + "┘")

        sector = get_sector(ticker)
        print(f"  [OK] Sector: {sector}")

        # Row helper for explainability matrix (defined once)
        def prow(label, value):
            text = f"  {label:<28}: {value}"
            print("║" + text.ljust(W) + "║")

        # ################################################################
        #  BRANCH A: Financial Services / Real Estate → Relative Comps
        # ################################################################
        if sector in FINANCIAL_SECTORS:
            print(f"  [!] Sector: {sector} detected. Traditional DCF cash-flow")
            print(f"      mechanics are structurally invalid for this asset class.")
            print(f"  [~] Routing to Relative Valuation (Comparable Companies).")

            comps_input = input(
                "\n[?] Enter exactly 3 competitor names or tickers (comma-separated): "
            ).strip()

            raw_names = [name.strip() for name in comps_input.split(",") if name.strip()]
            if not raw_names:
                print("  [✗] No valid names provided. Skipping.")
                continue

            # Resolve each peer through the NLP ticker resolution engine
            resolved_peers = []
            for name in raw_names:
                peer_result = resolve_ticker(name)
                if peer_result is not None:
                    peer_sym = peer_result["ticker"]
                    peer_name = peer_result["name"]
                    print(f"  [+] Peer Resolved: {name} -> {peer_sym} ({peer_name})")
                    resolved_peers.append(peer_sym)
                else:
                    print(f"  [✗] Could not resolve peer: {name}")

            if not resolved_peers:
                print("  [✗] No peers could be resolved. Skipping.")
                continue

            comps = relative_valuation_comps(ticker, resolved_peers, market_price, W)

            if comps is None:
                print("  [✗] Relative Valuation failed. Skipping.")
                continue

            blended = comps["blended_price"]

            # Signal
            if market_price > 0 and blended > 0:
                ratio = blended / market_price
                if ratio >= 1.15:
                    signal = "▲ BUY  (Undervalued)"
                elif ratio <= 0.85:
                    signal = "▼ SELL (Overvalued)"
                else:
                    signal = "● HOLD (Fair Value)"
                upside = (blended / market_price - 1.0) * 100.0
            else:
                signal = "— N/A"
                upside = 0.0

            print(f"  Upside/Downside  : {upside:+.2f}% (Blended Comps vs Market)")
            print(f"  Signal           : {signal}")

            # ════ PANEL 6: EXPLAINABILITY MATRIX (Comps) ════════════════
            print()
            print("╔" + "═" * W + "╗")
            print("║" + f"  EXPLAINABILITY MATRIX — {ticker} ({company_name})".ljust(W) + "║")
            print("╠" + "═" * W + "╣")

            prow("Company", company_name)
            prow("Ticker", ticker)
            prow("Exchange", exchange)
            prow("Sector", sector)
            prow("Valuation Method", "Relative Valuation (Comps)")
            print("╠" + "─" * W + "╣")
            print("║" + "  RISK ASSUMPTIONS".ljust(W) + "║")
            print("╠" + "─" * W + "╣")
            prow("Risk-Free Rate (^TNX)", f"{rf * 100:.2f}%")
            prow("Beta (2Y vs SPY)", f"{beta:.4f}")
            prow("CAPM Cost of Equity", f"{coe * 100:.2f}%")
            prow("Fully Levered WACC", f"{wacc * 100:.2f}%")
            print("╠" + "─" * W + "╣")
            print("║" + "  COMPARABLE COMPANIES".ljust(W) + "║")
            print("╠" + "─" * W + "╣")
            peer_tickers_str = ", ".join([p["ticker"] for p in comps["peer_data"]])
            prow("Peers Used", peer_tickers_str)
            prow("Median Peer P/E", f"{comps['median_pe']:.2f}")
            prow("Median Peer P/B", f"{comps['median_pb']:.2f}")
            if comps["target_eps"] is not None:
                prow("Target EPS", f"${comps['target_eps']:.2f}")
            if comps["target_pb"] is not None:
                prow("Target P/B", f"{comps['target_pb']:.2f}")
            if comps["implied_pe"] is not None:
                prow("Implied Price (P/E)", f"${comps['implied_pe']:.2f}")
            if comps["implied_pb"] is not None:
                prow("Implied Price (P/B)", f"${comps['implied_pb']:.2f}")
            print("╠" + "─" * W + "╣")
            print("║" + "  VERDICT".ljust(W) + "║")
            print("╠" + "─" * W + "╣")
            prow("Blended Implied Price", f"${blended:.2f}")
            prow("Current Market Price", f"${market_price:.2f}")
            prow("Upside / Downside", f"{upside:+.2f}%")
            prow("Signal", signal)
            print("╚" + "═" * W + "╝")

        # ################################################################
        #  BRANCH B: Standard Sectors → Monte Carlo DCF
        # ################################################################
        else:
            print(f"  [~] Standard sector. Routing to Monte Carlo DCF.")

            # Growth Model
            print()
            print("┌" + "─" * W + "┐")
            print("│" + "  PANEL 4b │ GROWTH MODEL — Revenue CAGR".ljust(W) + "│")
            print("└" + "─" * W + "┘")

            cagr = calculate_historical_cagr(ticker)
            print(f"  [OK] 3-Year Revenue CAGR: {cagr * 100:.2f}%")

            # Monte Carlo DCF
            print()
            print("┌" + "─" * W + "┐")
            print("│" + "  PANEL 5 │ MONTE CARLO DCF VALUATION (10,000 sims)".ljust(W) + "│")
            print("└" + "─" * W + "┘")

            mc = monte_carlo_dcf(fin_record, cagr, wacc_mean=wacc)

            base_fcff = mc["base_fcff"]
            ev = mc["median_ev"]
            eq_val = mc["median_equity"]
            bear_price = mc["bear_price"]
            base_price = mc["base_price"]
            bull_price = mc["bull_price"]

            print(f"  Base FCFF        : {format_large_number(base_fcff)}")
            print(f"  Enterprise Value : {format_large_number(ev)} (median)")
            print(f"  Equity Value     : {format_large_number(eq_val)} (median)")
            print(f"  ┌─────────────────────────────────────────────┐")
            print(f"  │  Bear Case (10th %ile) :  ${bear_price:>12.2f}  │")
            print(f"  │  Base Case (50th %ile) :  ${base_price:>12.2f}  │")
            print(f"  │  Bull Case (90th %ile) :  ${bull_price:>12.2f}  │")
            print(f"  └─────────────────────────────────────────────┘")
            print(f"  Market Price     : ${market_price:.2f}")
            print(f"  Price Std Dev    : ${mc['price_std']:.2f}")

            # Signal
            if market_price > 0 and base_price > 0:
                ratio = base_price / market_price
                if ratio >= 1.15:
                    signal = "▲ BUY  (Undervalued)"
                elif ratio <= 0.85:
                    signal = "▼ SELL (Overvalued)"
                else:
                    signal = "● HOLD (Fair Value)"
                upside = (base_price / market_price - 1.0) * 100.0
            else:
                signal = "— N/A"
                upside = 0.0

            print(f"  Upside/Downside  : {upside:+.2f}% (Base Case vs Market)")
            print(f"  Signal           : {signal}")

            # ════ PANEL 6: EXPLAINABILITY MATRIX (Monte Carlo) ═════════
            print()
            print("╔" + "═" * W + "╗")
            print("║" + f"  EXPLAINABILITY MATRIX — {ticker} ({company_name})".ljust(W) + "║")
            print("╠" + "═" * W + "╣")

            prow("Company", company_name)
            prow("Ticker", ticker)
            prow("Exchange", exchange)
            prow("Sector", sector)
            prow("Valuation Method", "Monte Carlo DCF (10,000 sims)")
            print("╠" + "─" * W + "╣")
            print("║" + "  RISK ASSUMPTIONS".ljust(W) + "║")
            print("╠" + "─" * W + "╣")
            prow("ERP Methodology", erp_result["methodology"])
            if erp_result["market_cagr"] is not None:
                mkt_cagr_str = f"{erp_result['market_cagr'] * 100:.2f}%"
            else:
                mkt_cagr_str = "N/A (fallback)"
            prow("10Y SPY CAGR", mkt_cagr_str)
            prow("Risk-Free Rate (^TNX)", f"{rf * 100:.2f}%")
            prow("Dynamic ERP (clamped)", f"{dynamic_erp * 100:.2f}%  [4%-8%]")
            prow("Beta (2Y vs SPY)", f"{beta:.4f}")
            prow("CAPM Cost of Equity", f"{coe * 100:.2f}%")
            prow("Cost of Debt", f"{cod * 100:.2f}%")
            prow("Effective Tax Rate", f"{eff_tax * 100:.2f}%")
            prow("Fully Levered WACC", f"{wacc * 100:.2f}%")
            print("╠" + "─" * W + "╣")
            tgr_str = f"{mc['tgr_mean'] * 100:.2f}%"
            tgr_std_str = f"{mc['tgr_std'] * 100:.1f}%"
            wacc_m_str = f"{mc['wacc_mean'] * 100:.2f}%"
            wacc_s_str = f"{mc['wacc_std'] * 100:.1f}%"
            print("║" + "  GROWTH & VALUATION (Monte Carlo)".ljust(W) + "║")
            print("╠" + "─" * W + "╣")
            prow("3-Year Revenue CAGR", f"{cagr * 100:.2f}%")
            prow("TGR Mean", f"{tgr_str} +/- {tgr_std_str}")
            prow("WACC Mean", f"{wacc_m_str} +/- {wacc_s_str}")
            prow("Projection Horizon", "5 Years (Tapered)")
            prow("Simulation Iterations", f"{mc['iterations']:,}")
            prow("Base FCFF", format_large_number(base_fcff))
            prow("Enterprise Value (med.)", format_large_number(ev))
            prow("Equity Value (med.)", format_large_number(eq_val))
            print("╠" + "─" * W + "╣")
            print("║" + "  VERDICT".ljust(W) + "║")
            print("╠" + "─" * W + "╣")
            prow("Bear Case (10th %ile)", f"${bear_price:.2f}")
            prow("Base Case (50th %ile)", f"${base_price:.2f}")
            prow("Bull Case (90th %ile)", f"${bull_price:.2f}")
            prow("Current Market Price", f"${market_price:.2f}")
            prow("Upside / Downside", f"{upside:+.2f}%")
            prow("Signal", signal)
            print("╚" + "═" * W + "╝")
