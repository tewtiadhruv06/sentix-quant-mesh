import yfinance as yf
import pandas as pd
import requests

EQUITY_API = "http://127.0.0.1:8080/api/v1/equities"
FINANCIAL_API = "http://127.0.0.1:8080/api/v1/financials"


def fetch_equity_map():
    """
    GET all registered equities from the Java API and return a dict
    mapping ticker strings to their equityId integers.
    """
    response = requests.get(EQUITY_API)
    response.raise_for_status()

    equity_list = response.json()
    ticker_to_id = {}
    for equity in equity_list:
        ticker_to_id[equity["ticker"]] = equity["equityId"]

    print(f"[INFO] Loaded {len(ticker_to_id)} equities from API: "
          f"{list(ticker_to_id.keys())}")
    return ticker_to_id


def safe_get(dataframe, label, default=0.0):
    """
    Safely extract the most recent annual column value for a given row label
    from a yfinance DataFrame. Returns `default` if the label is missing or
    the value is NaN.
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


def seed_financial_record(ticker, equity_id):
    """
    Pull the most recent annual financial data from yfinance for the given
    ticker, construct a DTO-matching payload, and POST it to the Java API.
    """
    print(f"\n{'─' * 50}")
    print(f"  Processing: {ticker} (equityId={equity_id})")
    print(f"{'─' * 50}")

    stock = yf.Ticker(ticker)

    # ── Pull the three statement DataFrames ──────────────────────────
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

    # ── Extract metrics with safe fallbacks ──────────────────────────
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

    # ── Construct the payload matching the Java DTO schema ───────────
    payload = {
        "equityId": equity_id,
        "fiscalYear": 2023,
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

    # ── POST to Java API ─────────────────────────────────────────────
    headers = {"Content-Type": "application/json"}
    response = requests.post(FINANCIAL_API, json=payload, headers=headers)

    if response.status_code == 201:
        print(f"[OK]    {ticker} — Financial record seeded successfully.")
    else:
        print(f"[ERROR] {ticker} — HTTP {response.status_code}: {response.text}")


if __name__ == "__main__":
    target_portfolio = ["TSLA", "NVDA", "AAPL", "MSFT", "AMZN"]

    print("=" * 60)
    print("  Financial Seeder — Annual Statement Loader")
    print("=" * 60)

    equity_map = fetch_equity_map()

    for ticker in target_portfolio:
        equity_id = equity_map.get(ticker)
        if equity_id is None:
            print(f"\n[SKIP] {ticker} — Not found in equity registry. "
                  f"Run equity_seeder.py first.")
            continue
        seed_financial_record(ticker, equity_id)

    print("\n" + "=" * 60)
    print("  Seeding complete.")
    print("=" * 60)
