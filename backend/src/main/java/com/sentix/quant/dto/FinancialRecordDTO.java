package com.sentix.quant.dto;

import java.math.BigDecimal;

public class FinancialRecordDTO {

    private Long recordId;
    private Long equityId;
    private Integer fiscalYear;
    private Integer fiscalQuarter;
    private BigDecimal totalRevenue;
    private BigDecimal ebit;
    private BigDecimal interestExpense;
    private BigDecimal pretaxIncome;
    private BigDecimal taxProvision;
    private BigDecimal cashAndEquivalents;
    private BigDecimal currentDebt;
    private BigDecimal longTermDebt;
    private BigDecimal capitalExpenditure;
    private BigDecimal depreciationAmortization;
    private Long sharesOutstanding;

    // ----------------------------------------------------------------
    // Constructors
    // ----------------------------------------------------------------

    public FinancialRecordDTO() {
    }

    // ----------------------------------------------------------------
    // Getters & Setters
    // ----------------------------------------------------------------

    public Long getRecordId() {
        return recordId;
    }

    public void setRecordId(Long recordId) {
        this.recordId = recordId;
    }

    public Long getEquityId() {
        return equityId;
    }

    public void setEquityId(Long equityId) {
        this.equityId = equityId;
    }

    public Integer getFiscalYear() {
        return fiscalYear;
    }

    public void setFiscalYear(Integer fiscalYear) {
        this.fiscalYear = fiscalYear;
    }

    public Integer getFiscalQuarter() {
        return fiscalQuarter;
    }

    public void setFiscalQuarter(Integer fiscalQuarter) {
        this.fiscalQuarter = fiscalQuarter;
    }

    public BigDecimal getTotalRevenue() {
        return totalRevenue;
    }

    public void setTotalRevenue(BigDecimal totalRevenue) {
        this.totalRevenue = totalRevenue;
    }

    public BigDecimal getEbit() {
        return ebit;
    }

    public void setEbit(BigDecimal ebit) {
        this.ebit = ebit;
    }

    public BigDecimal getInterestExpense() {
        return interestExpense;
    }

    public void setInterestExpense(BigDecimal interestExpense) {
        this.interestExpense = interestExpense;
    }

    public BigDecimal getPretaxIncome() {
        return pretaxIncome;
    }

    public void setPretaxIncome(BigDecimal pretaxIncome) {
        this.pretaxIncome = pretaxIncome;
    }

    public BigDecimal getTaxProvision() {
        return taxProvision;
    }

    public void setTaxProvision(BigDecimal taxProvision) {
        this.taxProvision = taxProvision;
    }

    public BigDecimal getCashAndEquivalents() {
        return cashAndEquivalents;
    }

    public void setCashAndEquivalents(BigDecimal cashAndEquivalents) {
        this.cashAndEquivalents = cashAndEquivalents;
    }

    public BigDecimal getCurrentDebt() {
        return currentDebt;
    }

    public void setCurrentDebt(BigDecimal currentDebt) {
        this.currentDebt = currentDebt;
    }

    public BigDecimal getLongTermDebt() {
        return longTermDebt;
    }

    public void setLongTermDebt(BigDecimal longTermDebt) {
        this.longTermDebt = longTermDebt;
    }

    public BigDecimal getCapitalExpenditure() {
        return capitalExpenditure;
    }

    public void setCapitalExpenditure(BigDecimal capitalExpenditure) {
        this.capitalExpenditure = capitalExpenditure;
    }

    public BigDecimal getDepreciationAmortization() {
        return depreciationAmortization;
    }

    public void setDepreciationAmortization(BigDecimal depreciationAmortization) {
        this.depreciationAmortization = depreciationAmortization;
    }

    public Long getSharesOutstanding() {
        return sharesOutstanding;
    }

    public void setSharesOutstanding(Long sharesOutstanding) {
        this.sharesOutstanding = sharesOutstanding;
    }
}
