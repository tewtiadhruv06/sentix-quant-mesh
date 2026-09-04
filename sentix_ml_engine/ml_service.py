from fastapi import FastAPI
import xgboost as xgb
import pandas as pd
from data_ingestion import FEATURE_COLUMNS, fetch_financial_features

# Initialize the API framework
app = FastAPI(title="Sentix ML Engine")

# Load the pre-trained brain into RAM exactly once on startup
model = xgb.XGBClassifier()
model.load_model("alpha_classifier.json")

@app.get("/predict/{ticker}")
def predict_alpha(ticker: str):
    ticker = ticker.upper()
    print(f"[*] Incoming request from Spring Boot: Analyzing {ticker}")
    try:
        df = fetch_financial_features(ticker)
        if df.empty:
            raise ValueError("Ticker data not found")
        latest_data = df[FEATURE_COLUMNS].iloc[[-1]]
        prediction = model.predict(latest_data)[0]
        probability = model.predict_proba(latest_data)[0][1]
        return {
            "ticker": ticker,
            "outperform_prediction": int(prediction),
            "confidence_score": float(probability)
        }
    except Exception as error:
        print(f"[-] Prediction unavailable for {ticker}: {error}")
        return {
            "ticker": ticker,
            "outperform_prediction": -1,
            "confidence_score": 0.0
        }