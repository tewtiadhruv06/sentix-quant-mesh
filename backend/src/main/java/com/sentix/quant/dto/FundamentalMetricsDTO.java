package com.sentix.quant.dto;

public class FundamentalMetricsDTO {

    private FinancialRecordDTO dcfValuation;
    private CcaBankMetricsDTO ccaMetrics;

    public FundamentalMetricsDTO() {
    }

    public FundamentalMetricsDTO(FinancialRecordDTO dcfValuation, CcaBankMetricsDTO ccaMetrics) {
        this.dcfValuation = dcfValuation;
        this.ccaMetrics = ccaMetrics;
    }

    public FinancialRecordDTO getDcfValuation() {
        return dcfValuation;
    }

    public void setDcfValuation(FinancialRecordDTO dcfValuation) {
        this.dcfValuation = dcfValuation;
    }

    public CcaBankMetricsDTO getCcaMetrics() {
        return ccaMetrics;
    }

    public void setCcaMetrics(CcaBankMetricsDTO ccaMetrics) {
        this.ccaMetrics = ccaMetrics;
    }
}
