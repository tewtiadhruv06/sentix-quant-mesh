import requests
import json
from urllib.parse import quote

YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36"
    ),
}


def resolve_ticker(company_query):
    """
    Fuzzy-search Yahoo Finance for a company name and return the top match
    as a dict with keys: ticker, name, exchange.
    Returns None if no match is found or on network failure.
    """
    encoded_query = quote(company_query)
    url = f"{YAHOO_SEARCH_URL}?q={encoded_query}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print("[!] Request timed out. Yahoo Finance may be unreachable.")
        return None
    except requests.exceptions.ConnectionError:
        print("[!] Connection error. Check your network connectivity.")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"[!] HTTP error from Yahoo Finance: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[!] Unexpected request error: {e}")
        return None

    try:
        data = response.json()
    except json.JSONDecodeError:
        print("[!] Failed to parse Yahoo Finance response as JSON.")
        return None

    quotes = data.get("quotes", [])

    if not quotes:
        return None

    top_match = quotes[0]
    symbol = top_match.get("symbol", "N/A")
    short_name = top_match.get("shortname", "Unknown")
    exchange_display = top_match.get("exchDisp", "Unknown")

    return {
        "ticker": symbol,
        "name": short_name,
        "exchange": exchange_display,
    }


def main():
    """Interactive CLI loop for fuzzy ticker resolution."""
    print("=" * 65)
    print("  Quant CLI — Fuzzy Ticker Resolution Engine")
    print("=" * 65)
    print("  Powered by Yahoo Finance Search API")
    print("  Type a company name to resolve its ticker symbol.")
    print("─" * 65)

    while True:
        user_input = input("\n[?] Enter Company Name to Analyze (or 'exit' to quit): ").strip()

        if not user_input:
            print("[!] Empty input. Please enter a valid company name.")
            continue

        if user_input.lower() == "exit":
            print("\n" + "=" * 65)
            print("  Session terminated. Goodbye.")
            print("=" * 65)
            break

        print(f"\n[~] Searching Yahoo Finance for: \"{user_input}\" ...")

        result = resolve_ticker(user_input)

        if result is None:
            print("─" * 65)
            print(f"[✗] NO MATCH FOUND for \"{user_input}\".")
            print("    Try a different spelling or a more specific company name.")
            print("─" * 65)
            continue

        ticker = result["ticker"]
        name = result["name"]
        exchange = result["exchange"]

        print("─" * 65)
        print(f"  [+] ASSET LOCKED")
        print(f"      Company  : {name}")
        print(f"      Ticker   : {ticker}")
        print(f"      Exchange : {exchange}")
        print("─" * 65)
        print(f"  [+] ASSET LOCKED: {name} | Ticker: {ticker} | Exchange: {exchange}")
        print("─" * 65)


if __name__ == "__main__":
    main()
