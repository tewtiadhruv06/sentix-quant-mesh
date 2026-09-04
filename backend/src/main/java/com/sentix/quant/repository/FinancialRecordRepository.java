package com.sentix.quant.repository;

import com.sentix.quant.entity.FinancialRecordEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface FinancialRecordRepository extends JpaRepository<FinancialRecordEntity, Long> {

    /**
     * Derived query to look up a financial record by its composite business key:
     * equity ID + fiscal year + fiscal quarter.
     *
     * @param equityId     the owning equity's database ID
     * @param fiscalYear   the fiscal year (e.g. 2025)
     * @param fiscalQuarter the fiscal quarter (1–4)
     * @return an Optional containing the matching record, or empty if none exists
     */
    Optional<FinancialRecordEntity> findByEquityIdAndFiscalYearAndFiscalQuarter(
            Long equityId, Integer fiscalYear, Integer fiscalQuarter);

    /**
     * Derived query to retrieve all financial records belonging to a given equity.
     *
     * @param equityId the owning equity's database ID
     * @return list of matching FinancialRecordEntity — never null, may be empty
     */
    List<FinancialRecordEntity> findByEquityId(Long equityId);
}
