import pandas as pd
import yfinance as yf


FEATURE_COLUMNS = [
    'moving_average_50', 'moving_average_200', 'daily_volatility',
    'rsi', 'volume_momentum'
]


def _download_history(ticker: str) -> pd.DataFrame:
    history = yf.download(
        ticker, period='5y', auto_adjust=False, progress=False,
        threads=False
    )
    if history.empty:
        return pd.DataFrame()

    # yfinance can return a MultiIndex even for a single ticker.
    if isinstance(history.columns, pd.MultiIndex):
        history.columns = history.columns.get_level_values(0)
    required_columns = {'Close', 'Volume'}
    if not required_columns.issubset(history.columns):
        raise ValueError(f"Missing price columns for {ticker}")
    return history

def fetch_financial_features(ticker: str) -> pd.DataFrame:
    """Download five years of price history and calculate the X matrix."""
    print(f"[*] Fetching historical price data for {ticker}...")
    history = _download_history(ticker)
    if history.empty:
        return pd.DataFrame()

    close = history['Close']
    volume = history['Volume']
    daily_return = close.pct_change()
    delta = close.diff()
    gains = delta.clip(lower=0).rolling(14).mean()
    losses = -delta.clip(upper=0).rolling(14).mean()
    relative_strength = gains / losses.replace(0, pd.NA)

    features = pd.DataFrame(index=history.index)
    features['date'] = pd.to_datetime(features.index).tz_localize(None)
    features['symbol'] = ticker.upper()
    features['moving_average_50'] = close.rolling(50).mean()
    features['moving_average_200'] = close.rolling(200).mean()
    features['daily_volatility'] = daily_return.rolling(20).std()
    features['rsi'] = 100 - (100 / (1 + relative_strength))
    features['volume_momentum'] = volume / volume.rolling(20).mean() - 1
    return features.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)

def fetch_price_data(ticker: str) -> pd.DataFrame:
    """Fetches historical closing prices to calculate forward returns."""
    print(f"[*] Fetching price data for {ticker}...")
    history = _download_history(ticker)
    if history.empty:
        return pd.DataFrame()
    prices = history[['Close']].rename(columns={'Close': 'close'}).reset_index()
    prices = prices.rename(columns={prices.columns[0]: 'date'})
    prices['date'] = pd.to_datetime(prices['date']).dt.tz_localize(None)
    return prices[['date', 'close']]

def build_target_matrix(features: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """Executes the time-shift merge to calculate the binary target variable (y)."""
    print("[*] Enforcing time-shift and calculating target variables...")
    
    # Sort both dataframes by date (Required for asynchronous merging)
    features = features.sort_values('date')
    prices = prices.sort_values('date')
    features['date'] = pd.to_datetime(features['date']).astype('datetime64[ns]')
    prices['date'] = pd.to_datetime(prices['date']).astype('datetime64[ns]')
    
    features['buy_date'] = features['date'] + pd.Timedelta(days=60)
    features['sell_date'] = features['buy_date'] + pd.Timedelta(days=365)
    
    # 2. Extract the Buy Price using As-Of Merging (finds the closest trading day)
    df = pd.merge_asof(features, prices, left_on='buy_date', right_on='date', 
                       direction='forward', suffixes=('', '_buy'))
    df = df.rename(columns={'close': 'buy_price'})
    
    # 3. Extract the Sell Price
    df = pd.merge_asof(df, prices, left_on='sell_date', right_on='date', 
                       direction='forward', suffixes=('', '_sell'))
    df = df.rename(columns={'close': 'sell_price'})
    
    # 4. Calculate the Target Label (y)
    # 1 if the stock beat the 10% market average, 0 if it failed
    df['1yr_return'] = (df['sell_price'] - df['buy_price']) / df['buy_price']
    df['target'] = (df['1yr_return'] > 0.10).astype(int)
    
    # Clean matrix and remove nulls (e.g., current year data where 1 year hasn't passed yet)
    df = df.dropna(subset=['buy_price', 'sell_price'])
    
    return df

if __name__ == "__main__":
    df_features = fetch_financial_features("AAPL")
    df_prices = fetch_price_data("AAPL")
    
    if not df_features.empty and not df_prices.empty:
        final_dataset = build_target_matrix(df_features, df_prices)
        print("\n[+] Final Training Matrix Constructed:")
        print(final_dataset[['date', 'buy_date', 'sell_date', '1yr_return', 'target']].head(5))
    else:
        print("[-] Pipeline failed. Check the ticker and network access.")