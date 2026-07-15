package com.sentix.quant.dto;

import java.time.LocalDateTime;

public class EquityDTO {

    private Long equityId;
    private String ticker;
    private String companyName;
    private String sector;
    private String exchange;
    private Boolean isActive;
    private LocalDateTime createdAt;

    // ----------------------------------------------------------------
    // Constructors
    // ----------------------------------------------------------------

    public EquityDTO() {
    }

    public EquityDTO(Long equityId,
                     String ticker,
                     String companyName,
                     String sector,
                     String exchange,
                     Boolean isActive,
                     LocalDateTime createdAt) {
        this.equityId = equityId;
        this.ticker = ticker;
        this.companyName = companyName;
        this.sector = sector;
        this.exchange = exchange;
        this.isActive = isActive;
        this.createdAt = createdAt;
    }

    // ----------------------------------------------------------------
    // Getters & Setters
    // ----------------------------------------------------------------

    public Long getEquityId() {
        return equityId;
    }

    public void setEquityId(Long equityId) {
        this.equityId = equityId;
    }

    public String getTicker() {
        return ticker;
    }

    public void setTicker(String ticker) {
        this.ticker = ticker;
    }

    public String getCompanyName() {
        return companyName;
    }

    public void setCompanyName(String companyName) {
        this.companyName = companyName;
    }

    public String getSector() {
        return sector;
    }

    public void setSector(String sector) {
        this.sector = sector;
    }

    public String getExchange() {
        return exchange;
    }

    public void setExchange(String exchange) {
        this.exchange = exchange;
    }

    public Boolean getIsActive() {
        return isActive;
    }

    public void setIsActive(Boolean isActive) {
        this.isActive = isActive;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    // ----------------------------------------------------------------
    // toString
    // ----------------------------------------------------------------

    @Override
    public String toString() {
        return "EquityDTO{" +
                "equityId=" + equityId +
                ", ticker='" + ticker + '\'' +
                ", companyName='" + companyName + '\'' +
                ", sector='" + sector + '\'' +
                ", exchange='" + exchange + '\'' +
                ", isActive=" + isActive +
                ", createdAt=" + createdAt +
                '}';
    }
}
