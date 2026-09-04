from requests import models
import pandas as pd
import xgboost as xgb
from data_ingestion import FEATURE_COLUMNS
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# 1. Ingest the Master Data
DATA_FILE = "master_training_matrix.csv"

def train_alpha_classifier():
    print(f"[*] Booting XGBoost Engine. Loading {DATA_FILE}...")
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        print(f"[-] Critical Error: {DATA_FILE} not found. Run build_dataset.py first.")
        return

    # 2. Define the exact columns for Features (X) and Target (y)
    feature_cols = FEATURE_COLUMNS
    
    # Drop any rows with NaN values that snuck through the pipeline
    df = df.dropna(subset=feature_cols + ['target'])
    
    X = df[feature_cols]
    y = df['target']
    
    print(f"[*] Matrix Loaded: {len(df)} historical financial quarters secured.")
    print("[*] Splitting data into 80% Training Set and 20% Test Set...")
    
    # 3. Split the data (Random state locked for reproducibility)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 4. Initialize and Train the Machine Learning Model
    print("[*] Training XGBoost Classifier...")
    model = xgb.XGBClassifier(
        n_estimators=100, 
        learning_rate=0.1, 
        max_depth=3, 
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    # 5. Execute Predictions and Evaluate Accuracy
    print("[*] Training complete. Executing blind predictions on Test Set...")
    predictions = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, predictions)
    print("\n" + "="*40)
    print("   MODEL EVALUATION REPORT")
    print("="*40)
    print(f"[+] Baseline Accuracy: {accuracy * 100:.2f}%")
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, predictions, zero_division=0))
    
    # Output the feature importance (which ratios mattered most)
    importance = model.feature_importances_
    print("\n[+] Feature Importance (What drove the predictions):")
    for i, col in enumerate(feature_cols):
        print(f"    - {col}: {importance[i] * 100:.2f}%")

    print("\n[*] Serializing decision trees to disk...")
    model.save_model("alpha_classifier.json")
    print("[+] Model successfully saved as alpha_classifier.json")

if __name__ == "__main__":
    train_alpha_classifier()


