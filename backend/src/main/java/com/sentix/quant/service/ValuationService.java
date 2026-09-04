package com.sentix.quant.service;

import com.sentix.quant.dto.CcaBankMetricsDTO;
import com.sentix.quant.dto.FinancialRecordDTO;
import com.sentix.quant.dto.FundamentalMetricsDTO;
import com.sentix.quant.dto.UnifiedAnalysisDTO;
import com.sentix.quant.entity.EquityEntity;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;

@Service
public class ValuationService {

    public UnifiedAnalysisDTO buildUnifiedValuation(EquityEntity equity, FinancialRecordDTO financialRecord) {
        if (equity == null || financialRecord == null) {
            return new UnifiedAnalysisDTO();
        }

        String sector = equity.getSector() == null ? "" : equity.getSector().trim();
        String industry = equity.getIndustry() == null ? "" : equity.getIndustry().trim();

        if (isBankingSector(sector, industry)) {
            CcaBankMetricsDTO ccaMetrics = calculateBankCcaMetrics(financialRecord);
            return new UnifiedAnalysisDTO(null, null, new FundamentalMetricsDTO(null, ccaMetrics));
        }

        return new UnifiedAnalysisDTO(financialRecord, null, new FundamentalMetricsDTO(financialRecord, null));
    }

    private boolean isBankingSector(String sector, String industry) {
        if (sector == null) {
            return false;
        }

        String normalizedSector = sector.toLowerCase();
        String normalizedIndustry = industry.toLowerCase();

        return "financial services".equals(normalizedSector)
                || normalizedIndustry.contains("bank");
    }

    private CcaBankMetricsDTO calculateBankCcaMetrics(FinancialRecordDTO financialRecord) {
        return new CcaBankMetricsDTO(
                new BigDecimal("1.25"),
                new BigDecimal("0.12"),
                new BigDecimal("14.50")
        );
    }
}
