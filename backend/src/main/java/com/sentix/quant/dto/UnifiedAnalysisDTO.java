package com.sentix.quant.dto;

/**
 * Aggregator DTO that combines the DCF valuation data with the
 * XGBoost ML prediction into a single response payload for the
 * Angular frontend.
 *
 * <p>Returned by {@code GET /api/v1/analysis/{ticker}}.
 */
public class UnifiedAnalysisDTO {

    private FinancialRecordDTO dcfValuation;
    private MlPredictionDTO mlPrediction;
    private FundamentalMetricsDTO fundamental;

    // ----------------------------------------------------------------
    // Constructors
    // ----------------------------------------------------------------

    public UnifiedAnalysisDTO() {
    }

    public UnifiedAnalysisDTO(FinancialRecordDTO dcfValuation,
                              MlPredictionDTO mlPrediction) {
        this(dcfValuation, mlPrediction, new FundamentalMetricsDTO(dcfValuation, null));
    }

    public UnifiedAnalysisDTO(FinancialRecordDTO dcfValuation,
                              MlPredictionDTO mlPrediction,
                              FundamentalMetricsDTO fundamental) {
        this.dcfValuation = dcfValuation;
        this.mlPrediction = mlPrediction;
        this.fundamental = fundamental;
    }

    // ----------------------------------------------------------------
    // Getters & Setters
    // ----------------------------------------------------------------

    public FinancialRecordDTO getDcfValuation() {
        return dcfValuation;
    }

    public void setDcfValuation(FinancialRecordDTO dcfValuation) {
        this.dcfValuation = dcfValuation;
    }

    public MlPredictionDTO getMlPrediction() {
        return mlPrediction;
    }

    public void setMlPrediction(MlPredictionDTO mlPrediction) {
        this.mlPrediction = mlPrediction;
    }

    public FundamentalMetricsDTO getFundamental() {
        return fundamental;
    }

    public void setFundamental(FundamentalMetricsDTO fundamental) {
        this.fundamental = fundamental;
    }

    // ----------------------------------------------------------------
    // toString
    // ----------------------------------------------------------------

    @Override
    public String toString() {
        return "UnifiedAnalysisDTO{" +
                "dcfValuation=" + dcfValuation +
                ", mlPrediction=" + mlPrediction +
                ", fundamental=" + fundamental +
                '}';
    }
}
