package com.sentix.quant.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.math.BigDecimal;

@Entity
@Table(name = "financial_records")
public class FinancialRecordEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "record_id")
    private Long recordId;

    @Column(name = "equity_id")
    private Long equityId;

    @Column(name = "fiscal_year")
    private Integer fiscalYear;

    @Column(name = "fiscal_quarter")
    private Integer fiscalQuarter;

    @Column(name = "total_revenue")
    private BigDecimal totalRevenue;

    @Column(name = "ebit")
    private BigDecimal ebit;

    @Column(name = "interest_expense")
    private BigDecimal interestExpense;

    @Column(name = "pretax_income")
    private BigDecimal pretaxIncome;

    @Column(name = "tax_provision")
    private BigDecimal taxProvision;

    @Column(name = "cash_and_equivalents")
    private BigDecimal cashAndEquivalents;

    @Column(name = "current_debt")
    private BigDecimal currentDebt;

    @Column(name = "long_term_debt")
    private BigDecimal longTermDebt;

    @Column(name = "capital_expenditure")
    private BigDecimal capitalExpenditure;

    @Column(name = "depreciation_amortization")
    private BigDecimal depreciationAmortization;

    @Column(name = "shares_outstanding")
    private Long sharesOutstanding;

    // ----------------------------------------------------------------
    // Constructors
    // ----------------------------------------------------------------

    public FinancialRecordEntity() {
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

    // ----------------------------------------------------------------
    // toString
    // ----------------------------------------------------------------

    @Override
    public String toString() {
        return "FinancialRecordEntity{" +
                "recordId=" + recordId +
                ", equityId=" + equityId +
                ", fiscalYear=" + fiscalYear +
                ", fiscalQuarter=" + fiscalQuarter +
                ", totalRevenue=" + totalRevenue +
                ", ebit=" + ebit +
                ", interestExpense=" + interestExpense +
                ", pretaxIncome=" + pretaxIncome +
                ", taxProvision=" + taxProvision +
                ", cashAndEquivalents=" + cashAndEquivalents +
                ", currentDebt=" + currentDebt +
                ", longTermDebt=" + longTermDebt +
                ", capitalExpenditure=" + capitalExpenditure +
                ", depreciationAmortization=" + depreciationAmortization +
                ", sharesOutstanding=" + sharesOutstanding +
                '}';
    }
}
