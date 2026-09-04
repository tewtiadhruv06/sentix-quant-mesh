package com.sentix.quant.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Data-transfer object representing a machine-learning prediction payload
 * returned by the Python FastAPI microservice at /predict/{ticker}.
 *
 * <p>JSON contract (snake_case → camelCase mapping):
 * <pre>
 * {
 *   "ticker":                "AAPL",
 *   "outperform_prediction": 1,
 *   "confidence_score":      0.958
 * }
 * </pre>
 */
public class MlPredictionDTO {

    @JsonProperty("ticker")
    private String ticker;

    @JsonProperty("outperform_prediction")
    private Integer outperformPrediction;

    @JsonProperty("confidence_score")
    private Double confidenceScore;

    // ----------------------------------------------------------------
    // Constructors
    // ----------------------------------------------------------------

    public MlPredictionDTO() {
    }

    public MlPredictionDTO(String ticker,
                           Integer outperformPrediction,
                           Double confidenceScore) {
        this.ticker = ticker;
        this.outperformPrediction = outperformPrediction;
        this.confidenceScore = confidenceScore;
    }

    // ----------------------------------------------------------------
    // Getters & Setters
    // ----------------------------------------------------------------

    public String getTicker() {
        return ticker;
    }

    public void setTicker(String ticker) {
        this.ticker = ticker;
    }

    public Integer getOutperformPrediction() {
        return outperformPrediction;
    }

    public void setOutperformPrediction(Integer outperformPrediction) {
        this.outperformPrediction = outperformPrediction;
    }

    public Double getConfidenceScore() {
        return confidenceScore;
    }

    public void setConfidenceScore(Double confidenceScore) {
        this.confidenceScore = confidenceScore;
    }

    // ----------------------------------------------------------------
    // toString
    // ----------------------------------------------------------------

    @Override
    public String toString() {
        return "MlPredictionDTO{" +
                "ticker='" + ticker + '\'' +
                ", outperformPrediction=" + outperformPrediction +
                ", confidenceScore=" + confidenceScore +
                '}';
    }
}
