import requests
import pandas as pd
import numpy as np
import yfinance as yf

EQUITY_API = "http://127.0.0.1:8080/api/v1/equities"
FINANCIAL_API = "http://127.0.0.1:8080/api/v1/financials"


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

    print(f"[INFO] Merged {len(merged)} financial records with equity tickers.")
    return merged


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

        # Use the most recent value and the value ~3 years prior
        current_rev = float(revenue_row.iloc[-1])
        years_back = min(3, len(revenue_row) - 1)
        old_rev = float(revenue_row.iloc[-(years_back + 1)])

        if old_rev <= 0 or current_rev <= 0:
            print(f"  [WARN] Non-positive revenue for {ticker_symbol}. Using default CAGR.")
            return default_cagr

        cagr = (current_rev / old_rev) ** (1.0 / years_back) - 1.0

        # Cap and floor
        cagr = max(0.02, min(0.35, cagr))
        return cagr

    except (ZeroDivisionError, ValueError, TypeError, KeyError) as e:
        print(f"  [WARN] CAGR calculation failed for {ticker_symbol}: {e}. Using default.")
        return default_cagr
    except Exception as e:
        print(f"  [WARN] Unexpected error for {ticker_symbol}: {e}. Using default CAGR.")
        return default_cagr


def calculate_intrinsic_value(row, cagr, wacc=0.10, tgr=0.025):
    """
    DCF Intrinsic Value calculation:
      1. Base FCFF = EBIT - |TaxProvision| + DepreciationAmortization - |CapitalExpenditure|
      2. Algorithmically taper growth from CAGR (Year 1) to TGR (Year 5)
      3. Project 5 years of FCFFs, discount each to PV
      4. Terminal Value via Gordon Growth Model on Year 5 FCFF
      5. EV = sum(PV of FCFFs) + PV of TV
      6. Equity Value = EV + Cash - CurrentDebt - LongTermDebt
      7. Implied Share Price = Equity Value / SharesOutstanding

    Returns a dict with intermediate and final values.
    """
    # ── Extract financials with safe defaults ────────────────────────
    ebit = float(row.get("ebit", 0) or 0)
    tax_provision = abs(float(row.get("taxProvision", 0) or 0))
    dep_amort = float(row.get("depreciationAmortization", 0) or 0)
    capex = abs(float(row.get("capitalExpenditure", 0) or 0))
    cash = float(row.get("cashAndEquivalents", 0) or 0)
    current_debt = float(row.get("currentDebt", 0) or 0)
    long_term_debt = float(row.get("longTermDebt", 0) or 0)
    shares_outstanding = float(row.get("sharesOutstanding", 0) or 0)

    # ── Step 1: Base Unlevered Free Cash Flow ────────────────────────
    base_fcff = ebit - tax_provision + dep_amort - capex

    # ── Step 2: Algorithmic Tapering ─────────────────────────────────
    #   Year 1 Growth = cagr, Year 5 Growth = tgr
    #   Linear interpolation across 5 years
    step = (cagr - tgr) / 4.0
    growth_rates = np.array([cagr - (i * step) for i in range(5)])

    # ── Step 3: Project & discount 5 years of FCFF ───────────────────
    projected_fcffs = []
    current_fcff = base_fcff
    pv_fcffs = []

    for year in range(1, 6):
        current_fcff = current_fcff * (1.0 + growth_rates[year - 1])
        projected_fcffs.append(current_fcff)
        pv = current_fcff / ((1.0 + wacc) ** year)
        pv_fcffs.append(pv)

    sum_pv_fcffs = sum(pv_fcffs)

    # ── Step 4: Terminal Value (Gordon Growth Model) ─────────────────
    year5_fcff = projected_fcffs[-1]

    if wacc <= tgr:
        # Fallback: avoid division by zero or negative denominator
        terminal_value = year5_fcff * 15.0
    else:
        terminal_value = (year5_fcff * (1.0 + tgr)) / (wacc - tgr)

    pv_terminal = terminal_value / ((1.0 + wacc) ** 5)

    # ── Step 5: Enterprise Value ─────────────────────────────────────
    enterprise_value = sum_pv_fcffs + pv_terminal

    # ── Step 6: Equity Value ─────────────────────────────────────────
    equity_value = enterprise_value + cash - current_debt - long_term_debt

    # ── Step 7: Implied Share Price ──────────────────────────────────
    if shares_outstanding <= 0:
        implied_price = 0.0
    else:
        implied_price = equity_value / shares_outstanding

    return {
        "base_fcff": base_fcff,
        "growth_rates": growth_rates,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "implied_price": implied_price,
    }


def get_current_market_price(ticker_symbol):
    """
    Fetch the current market price via yfinance.
    Returns 0.0 on failure.
    """
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


if __name__ == "__main__":
    target_portfolio = ["TSLA", "NVDA", "AAPL", "MSFT", "AMZN"]

    print("=" * 90)
    print("  DCF Engine — Discounted Cash Flow Intrinsic Value Calculator")
    print("=" * 90)

    # ── Fetch and merge data from Java APIs ──────────────────────────
    merged_df = fetch_merged_dataframe()
    if merged_df.empty:
        print("[FATAL] No data to process. Ensure the backend is running and seeded.")
        exit(1)

    # ── Build results ────────────────────────────────────────────────
    results = []

    for ticker in target_portfolio:
        ticker_rows = merged_df[merged_df["ticker"] == ticker]
        if ticker_rows.empty:
            print(f"\n[SKIP] {ticker} — No financial record found in merged data.")
            continue

        row = ticker_rows.iloc[0]

        print(f"\n{'─' * 50}")
        print(f"  Analyzing: {ticker}")
        print(f"{'─' * 50}")

        cagr = calculate_historical_cagr(ticker)
        dcf = calculate_intrinsic_value(row, cagr)
        market_price = get_current_market_price(ticker)

        results.append({
            "Ticker": ticker,
            "Base FCFF": dcf["base_fcff"],
            "3Y CAGR (%)": cagr * 100.0,
            "Enterprise Value": dcf["enterprise_value"],
            "Market Price": market_price,
            "Implied Price": dcf["implied_price"],
        })

    # ── Print formatted results table ────────────────────────────────
    if not results:
        print("\n[WARN] No results to display.")
        exit(0)

    print("\n")
    print("=" * 90)
    print("  DCF VALUATION SUMMARY")
    print("=" * 90)

    header = (
        f"{'Ticker':<8}"
        f"{'Base FCFF':>16}"
        f"{'3Y CAGR':>12}"
        f"{'Enterprise Value':>20}"
        f"{'Market Price':>15}"
        f"{'Implied Price':>15}"
    )
    print(header)
    print("─" * 90)

    for r in results:
        ticker_str = r['Ticker']
        fcff_str = format_large_number(r['Base FCFF'])
        cagr_str = f"{r['3Y CAGR (%)']:.2f}%"
        ev_str = format_large_number(r['Enterprise Value'])
        market_price_str = f"${r['Market Price']:.2f}"
        implied_price_str = f"${r['Implied Price']:.2f}"

        line = (
            f"{ticker_str:<8}"
            f"{fcff_str:>16}"
            f"{cagr_str:>12}"
            f"{ev_str:>20}"
            f"{market_price_str:>15}"
            f"{implied_price_str:>15}"
        )
        print(line)

    print("─" * 90)
    print("  WACC = 10.0%  |  Terminal Growth Rate = 2.5%  |  Projection = 5 Years")
    print("=" * 90)
