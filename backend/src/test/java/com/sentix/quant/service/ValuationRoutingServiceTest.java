package com.sentix.quant.service;

import com.sentix.quant.dto.FinancialRecordDTO;
import com.sentix.quant.dto.UnifiedAnalysisDTO;
import com.sentix.quant.entity.EquityEntity;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.*;

class ValuationRoutingServiceTest {

    @Test
    void routeForBankingSector_shouldReturnCcaMetrics() {
        EquityEntity equity = new EquityEntity();
        equity.setTicker("JPM");
        equity.setSector("Financial Services");
        equity.setCompanyName("JPMorgan Chase");
        equity.setIndustry("Banks - Diversified");

        FinancialRecordDTO financialRecord = new FinancialRecordDTO();
        financialRecord.setTotalRevenue(new BigDecimal("1500000000"));
        financialRecord.setEbit(new BigDecimal("500000000"));
        financialRecord.setPretaxIncome(new BigDecimal("450000000"));
        financialRecord.setTaxProvision(new BigDecimal("100000000"));
        financialRecord.setCashAndEquivalents(new BigDecimal("200000000"));
        financialRecord.setCurrentDebt(new BigDecimal("800000000"));
        financialRecord.setLongTermDebt(new BigDecimal("900000000"));
        financialRecord.setCapitalExpenditure(new BigDecimal("25000000"));
        financialRecord.setDepreciationAmortization(new BigDecimal("35000000"));
        financialRecord.setSharesOutstanding(2000000L);

        ValuationService valuationService = new ValuationService();
        UnifiedAnalysisDTO result = valuationService.buildUnifiedValuation(equity, financialRecord);

        assertNotNull(result.getFundamental());
        assertNotNull(result.getFundamental().getCcaMetrics());
        assertEquals(new BigDecimal("1.25"), result.getFundamental().getCcaMetrics().getPriceToBook());
        assertEquals(new BigDecimal("0.12"), result.getFundamental().getCcaMetrics().getRoe());
        assertEquals(new BigDecimal("14.50"), result.getFundamental().getCcaMetrics().getPriceToEarnings());
    }
}
