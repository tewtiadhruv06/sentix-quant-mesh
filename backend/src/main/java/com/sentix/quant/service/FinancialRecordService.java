package com.sentix.quant.service;

import com.sentix.quant.dto.FinancialRecordDTO;
import com.sentix.quant.entity.FinancialRecordEntity;
import com.sentix.quant.repository.FinancialRecordRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
public class FinancialRecordService {

    private final FinancialRecordRepository financialRecordRepository;

    public FinancialRecordService(FinancialRecordRepository financialRecordRepository) {
        this.financialRecordRepository = financialRecordRepository;
    }

    // ----------------------------------------------------------------
    // Public API
    // ----------------------------------------------------------------

    /**
     * Saves or updates a financial record using an upsert strategy.
     * If a record already exists for the given equity/year/quarter combination,
     * all numerical fields are updated in place. Otherwise a new record is
     * inserted.
     *
     * @param dto incoming data-transfer object carrying financial record fields
     * @return the persisted FinancialRecordDTO with database-assigned recordId
     */
    @Transactional
    public FinancialRecordDTO saveRecord(FinancialRecordDTO dto) {
        Optional<FinancialRecordEntity> existing =
                financialRecordRepository.findByEquityIdAndFiscalYearAndFiscalQuarter(
                        dto.getEquityId(), dto.getFiscalYear(), dto.getFiscalQuarter());

        FinancialRecordEntity entity;

        if (existing.isPresent()) {
            entity = existing.get();
            updateNumericalFields(entity, dto);
        } else {
            entity = mapDtoToEntity(dto);
        }

        FinancialRecordEntity saved = financialRecordRepository.save(entity);
        return mapEntityToDto(saved);
    }

    /**
     * Retrieves all financial records as a list of DTOs.
     *
     * @return list of FinancialRecordDTO — never null, may be empty
     */
    @Transactional(readOnly = true)
    public List<FinancialRecordDTO> getAllRecords() {
        return financialRecordRepository.findAll()
                .stream()
                .map(this::mapEntityToDto)
                .collect(Collectors.toList());
    }

    // ----------------------------------------------------------------
    // Conversion Helpers
    // ----------------------------------------------------------------

    /**
     * Updates all numerical fields on an existing entity from the incoming DTO.
     * The composite business key fields (equityId, fiscalYear, fiscalQuarter)
     * are intentionally left unchanged.
     *
     * @param entity the managed JPA entity to update
     * @param dto    source of the new numerical values
     */
    private void updateNumericalFields(FinancialRecordEntity entity, FinancialRecordDTO dto) {
        entity.setTotalRevenue(dto.getTotalRevenue());
        entity.setEbit(dto.getEbit());
        entity.setInterestExpense(dto.getInterestExpense());
        entity.setPretaxIncome(dto.getPretaxIncome());
        entity.setTaxProvision(dto.getTaxProvision());
        entity.setCashAndEquivalents(dto.getCashAndEquivalents());
        entity.setCurrentDebt(dto.getCurrentDebt());
        entity.setLongTermDebt(dto.getLongTermDebt());
        entity.setCapitalExpenditure(dto.getCapitalExpenditure());
        entity.setDepreciationAmortization(dto.getDepreciationAmortization());
        entity.setSharesOutstanding(dto.getSharesOutstanding());
    }

    /**
     * Maps a FinancialRecordEntity (persistence layer) to a FinancialRecordDTO
     * (API layer). No JPA-managed references leak across this boundary.
     *
     * @param entity source JPA entity
     * @return clean DTO populated from entity fields
     */
    private FinancialRecordDTO mapEntityToDto(FinancialRecordEntity entity) {
        FinancialRecordDTO dto = new FinancialRecordDTO();
        dto.setRecordId(entity.getRecordId());
        dto.setEquityId(entity.getEquityId());
        dto.setFiscalYear(entity.getFiscalYear());
        dto.setFiscalQuarter(entity.getFiscalQuarter());
        dto.setTotalRevenue(entity.getTotalRevenue());
        dto.setEbit(entity.getEbit());
        dto.setInterestExpense(entity.getInterestExpense());
        dto.setPretaxIncome(entity.getPretaxIncome());
        dto.setTaxProvision(entity.getTaxProvision());
        dto.setCashAndEquivalents(entity.getCashAndEquivalents());
        dto.setCurrentDebt(entity.getCurrentDebt());
        dto.setLongTermDebt(entity.getLongTermDebt());
        dto.setCapitalExpenditure(entity.getCapitalExpenditure());
        dto.setDepreciationAmortization(entity.getDepreciationAmortization());
        dto.setSharesOutstanding(entity.getSharesOutstanding());
        return dto;
    }

    /**
     * Maps a FinancialRecordDTO (API layer) to a transient FinancialRecordEntity
     * (persistence layer). The recordId field is intentionally excluded so
     * Hibernate treats this as a new INSERT rather than an UPDATE.
     *
     * @param dto source data-transfer object
     * @return transient FinancialRecordEntity ready for persistence
     */
    private FinancialRecordEntity mapDtoToEntity(FinancialRecordDTO dto) {
        FinancialRecordEntity entity = new FinancialRecordEntity();
        entity.setEquityId(dto.getEquityId());
        entity.setFiscalYear(dto.getFiscalYear());
        entity.setFiscalQuarter(dto.getFiscalQuarter());
        entity.setTotalRevenue(dto.getTotalRevenue());
        entity.setEbit(dto.getEbit());
        entity.setInterestExpense(dto.getInterestExpense());
        entity.setPretaxIncome(dto.getPretaxIncome());
        entity.setTaxProvision(dto.getTaxProvision());
        entity.setCashAndEquivalents(dto.getCashAndEquivalents());
        entity.setCurrentDebt(dto.getCurrentDebt());
        entity.setLongTermDebt(dto.getLongTermDebt());
        entity.setCapitalExpenditure(dto.getCapitalExpenditure());
        entity.setDepreciationAmortization(dto.getDepreciationAmortization());
        entity.setSharesOutstanding(dto.getSharesOutstanding());
        return entity;
    }
}
