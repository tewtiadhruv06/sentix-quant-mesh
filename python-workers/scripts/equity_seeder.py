import yfinance as yf
import requests

JAVA_API_ENDPOINT = "http://127.0.0.1:8080/api/v1/equities"


def seed_corporate_profile(ticker_symbol):
    """Fetch corporate profile data from yfinance and POST it to the Java API."""
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info

    long_name = info.get("longName")
    if not long_name:
        print(f"[SKIP] No longName found for '{ticker_symbol}'. Aborting seed.")
        return

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

    response = requests.post(JAVA_API_ENDPOINT, json=payload, headers=headers)

    if response.status_code == 201:
        print(f"[OK]       {ticker_symbol.upper()} — '{long_name}' seeded successfully.")
    elif response.status_code == 409:
        print(f"[CONFLICT] {ticker_symbol.upper()} — '{long_name}' already exists (duplicate).")
    else:
        print(
            f"[ERROR]    {ticker_symbol.upper()} — Unexpected status {response.status_code}: "
            f"{response.text}"
        )


if __name__ == "__main__":
    target_portfolio = ["TSLA", "NVDA", "AAPL", "MSFT", "AMZN"]

    print("=" * 60)
    print("  Equity Seeder — Corporate Profile Loader")
    print("=" * 60)

    for ticker in target_portfolio:
        seed_corporate_profile(ticker)

    print("=" * 60)
    print("  Seeding complete.")
    print("=" * 60)
