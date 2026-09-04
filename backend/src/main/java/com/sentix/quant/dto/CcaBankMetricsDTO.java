package com.sentix.quant.dto;

import java.math.BigDecimal;

public class CcaBankMetricsDTO {

    private BigDecimal priceToBook;
    private BigDecimal roe;
    private BigDecimal priceToEarnings;

    public CcaBankMetricsDTO() {
    }

    public CcaBankMetricsDTO(BigDecimal priceToBook, BigDecimal roe, BigDecimal priceToEarnings) {
        this.priceToBook = priceToBook;
        this.roe = roe;
        this.priceToEarnings = priceToEarnings;
    }

    public BigDecimal getPriceToBook() {
        return priceToBook;
    }

    public void setPriceToBook(BigDecimal priceToBook) {
        this.priceToBook = priceToBook;
    }

    public BigDecimal getRoe() {
        return roe;
    }

    public void setRoe(BigDecimal roe) {
        this.roe = roe;
    }

    public BigDecimal getPriceToEarnings() {
        return priceToEarnings;
    }

    public void setPriceToEarnings(BigDecimal priceToEarnings) {
        this.priceToEarnings = priceToEarnings;
    }
}
