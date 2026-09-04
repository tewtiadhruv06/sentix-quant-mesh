/**
 * TypeScript interfaces strictly modelling the JSON contract
 * returned by GET /api/v1/analysis/{ticker}.
 */

export interface DcfValuation {
  recordId: number;
  equityId: number;
  fiscalYear: number;
  fiscalQuarter: number;
  totalRevenue: number;
  ebit: number;
  interestExpense: number;
  pretaxIncome: number;
  taxProvision: number;
  cashAndEquivalents: number;
  currentDebt: number;
  longTermDebt: number;
  capitalExpenditure: number;
  depreciationAmortization: number;
  sharesOutstanding: number;
}

export interface CcaBankMetrics {
  priceToBook: number;
  roe: number;
  priceToEarnings: number;
}

export interface FundamentalMetrics {
  dcfValuation: DcfValuation | null;
  ccaMetrics: CcaBankMetrics | null;
}

export interface MlPrediction {
  ticker: string;
  outperform_prediction: number;   // 1 = Outperform, 0 = Underperform, -1 = Engine Offline
  confidence_score: number;        // 0.0 – 1.0
}

export interface UnifiedAnalysis {
  dcfValuation: DcfValuation | null;
  mlPrediction: MlPrediction | null;
  fundamental: FundamentalMetrics | null;
}
