import time
import os
import pandas as pd
from data_ingestion import fetch_financial_features, fetch_price_data, build_target_matrix

TARGET_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "META", "AMZN", "JPM", "NVDA", "TSLA",
    "AVGO", "GOOG", "LLY", "V", "UNH", "MA", "XOM", "JNJ", "WMT",
    "PG", "COST", "HD", "ORCL", "MRK", "ABBV", "CVX", "BAC", "KO",
    "PEP", "ADBE", "CRM", "NFLX", "TMO", "MCD", "AMD", "ACN", "CSCO",
    "LIN", "ABT", "INTU", "DHR", "CMCSA", "TXN", "QCOM", "AMGN", "IBM",
    "PM", "HON", "UNP", "LOW", "CAT", "GE", "GS", "SPGI", "BLK", "DE"
]
OUTPUT_FILE = "master_training_matrix.csv"

def aggregate_data(tickers: list):
    print(f"[*] Initializing aggregation for {len(tickers)} assets...")
    
    # Trackers for the terminal output
    successful = 0
    failed = 0
    
    for ticker in tickers:
        print(f"\n[*] Processing [{ticker}]...")
        try:
            # 1. Fetch raw data
            df_features = fetch_financial_features(ticker)
            df_prices = fetch_price_data(ticker)
            
            # 2. Check if data is valid
            if df_features.empty or df_prices.empty:
                print(f"[-] Insufficient data for {ticker}. Skipping.")
                failed += 1
                continue
                
            # 3. Align the matrices (The Time-Shift)
            df_final = build_target_matrix(df_features, df_prices)
            if df_final.empty:
                print(f"[-] No complete forward-return rows for {ticker}. Skipping.")
                failed += 1
                continue
            
            # 4. Iterative Checkpointing: Save to CSV immediately
            # Do not mix the current schema with an older training matrix.
            has_current_schema = False
            if os.path.isfile(OUTPUT_FILE):
                existing_columns = pd.read_csv(OUTPUT_FILE, nrows=0).columns.tolist()
                has_current_schema = existing_columns == df_final.columns.tolist()
            if not has_current_schema:
                df_final.to_csv(OUTPUT_FILE, index=False)
            else:
                df_final.to_csv(OUTPUT_FILE, mode='a', header=False, index=False)
                
            print(f"[+] {ticker} successfully appended to database.")
            successful += 1
            
        except Exception as e:
            print(f"[-] Fatal error on {ticker}: {str(e)}. Bypassing.")
            failed += 1
            
        # 5. Throttle to prevent API ban
        time.sleep(0.5)
        
    print(f"\n[+] Aggregation Complete. Success: {successful} | Failed: {failed}")
    print(f"[+] Data securely written to {OUTPUT_FILE}")

if __name__ == "__main__":
    aggregate_data(TARGET_TICKERS)