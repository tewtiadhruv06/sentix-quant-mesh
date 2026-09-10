# Sentix Quant Mesh

A distributed, polyglot quantitative analysis terminal combining deterministic corporate finance modeling with statistical machine learning. 

This platform orchestrates a dynamic intrinsic valuation engine (Discounted Cash Flow & Comparable Company Analysis) with a momentum-based XGBoost alpha classifier, delivered through an institutional-grade frontend terminal.

## 1. System Architecture

The application operates on a three-node microservice mesh to isolate financial accounting logic from statistical computation:

*   **Front-Office (Angular / TypeScript):** A unified analysis terminal featuring a high-contrast, Bloomberg-inspired UI. Handles asynchronous state management across simultaneous fundamental and quantitative data payloads.
*   **Middle-Office (Spring Boot / Java):** The valuation orchestrator. Manages SEC accounting data ingestion, deterministic financial modeling, and algorithmic sector-routing. 
*   **Back-Office (FastAPI / Python):** The quantitative machine learning engine (`sentix_ml_engine`). Executes rolling technical feature extraction and probabilistic inference via a pre-trained XGBoost model.

## 2. Core Financial Engines

### Dynamic Sector Routing
The valuation engine dynamically alters its mathematical primitive based on the target equity's GICS sector categorization:
*   **Non-Financial Corporates (e.g., MSFT, TSLA):** Routes to a 10-variable Free Cash Flow to Firm (FCFF) Discounted Cash Flow model using live EBIT, CapEx, D&A, and debt tranche data.
*   **Commercial Banks (e.g., BAC, JPM):** Bypasses FCFF logic (due to differing capital structures) and routes to a Comparable Company Analysis (CCA) engine calculating Price/Book, Return on Equity (ROE), and P/E multiples.

### Statistical Alpha Generation
The `sentix_ml_engine` utilizes a binary classification XGBoost model trained on a 41,140-row historical market matrix. 
*   **Feature Engineering:** Extracts real-time time-series data to construct rolling moving averages, annualized volatility, and RSI.
*   **Inference:** Outputs a calibrated confidence score mapping the probability of statistically significant alpha generation over a 12-month horizon (Outperform vs. Underperform).

## 3. Data Ingestion Strategy

To ensure system resilience and bypass external API rate limits, the data pipeline is bifurcated:
*   **Fundamental Accounting:** Sourced via Financial Modeling Prep (FMP) modern `/stable/` endpoints. The Java middle-office pulls clean SEC 10-K/10-Q line items required for intrinsic valuation.
*   **Quantitative Pricing:** Sourced via `yfinance`. The Python back-office isolates its technical indicator generation from FMP, relying on open-source market data to ensure the ML pipeline remains operational regardless of commercial API free-tier paywalls.

## 4. Local Execution

To boot the distributed mesh locally, spin up the three nodes in separate terminal instances:

**Node 1: Spring Boot Middle-Office (Port 8080)**
\`\`\`bash
cd backend
mvn clean spring-boot:run
\`\`\`
*(Requires local MySQL instance running on Port 3306 and a valid FMP API key injected via environment variables).*

**Node 2: FastAPI Back-Office (Port 8000)**
\`\`\`bash
cd sentix_ml_engine
pip install -r requirements.txt
uvicorn ml_service:app --reload --port 8000
\`\`\`

**Node 3: Angular Terminal (Port 4200)**
\`\`\`bash
cd frontend
npm install
npm start
\`\`\`
