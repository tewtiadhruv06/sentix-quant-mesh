package com.sentix.quant.service;

import com.sentix.quant.dto.EquityDTO;
import com.sentix.quant.entity.EquityEntity;
import com.sentix.quant.repository.EquityRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@Transactional
public class EquityService {

    private final EquityRepository equityRepository;
    private final FmpDataService fmpDataService;

    public EquityService(EquityRepository equityRepository, FmpDataService fmpDataService) {
        this.equityRepository = equityRepository;
        this.fmpDataService = fmpDataService;
    }

    // ----------------------------------------------------------------
    // Public API
    // ----------------------------------------------------------------

    /**
     * Registers a new equity in the system.
     * Enforces unique ticker constraint at the service layer before delegating
     * to the persistence layer, returning the persisted DTO with generated ID.
     *
     * @param dto incoming data-transfer object carrying equity fields
     * @return the saved EquityDTO with database-assigned equityId and createdAt
     * @throws IllegalStateException if a record with the same ticker already exists
     */
    public EquityDTO registerEquity(EquityDTO dto) {
        String normalizedTicker = normalizeTicker(dto.getTicker());
        dto.setTicker(normalizedTicker);

        equityRepository.findByTicker(normalizedTicker).ifPresent(existing -> {
            throw new IllegalStateException(
                    "Equity with ticker [" + normalizedTicker + "] already exists. " +
                    "Duplicate registrations are not permitted."
            );
        });

        EquityEntity entity = mapDtoToEntity(dto);
        entity.setCreatedAt(LocalDateTime.now());
        entity.setIsActive(dto.getIsActive() != null ? dto.getIsActive() : Boolean.TRUE);

        EquityEntity saved = equityRepository.save(entity);
        return mapEntityToDto(saved);
    }

    @Transactional(readOnly = true)
    public String resolveTickerSymbol(String rawSearch) {
        String trimmed = rawSearch == null ? "" : rawSearch.trim();
        String normalizedInput = normalizeTicker(trimmed);

        if (!normalizedInput.isBlank()) {
            Optional<EquityEntity> exactMatch = equityRepository.findByTicker(normalizedInput);
            if (exactMatch.isPresent()) {
                return exactMatch.get().getTicker().toUpperCase();
            }
        }

        String resolved = fmpDataService.searchTicker(trimmed);
        return resolved == null || resolved.isBlank() ? normalizedInput : resolved.toUpperCase();
    }

    /**
     * Retrieves all registered equities as a list of DTOs.
     *
     * @return list of EquityDTO — never null, may be empty
     */
    @Transactional(readOnly = true)
    public List<EquityDTO> getAllEquities() {
        return equityRepository.findAll()
                .stream()
                .map(this::mapEntityToDto)
                .collect(Collectors.toList());
    }

    private String normalizeTicker(String rawTicker) {
        if (rawTicker == null) {
            return "";
        }
        return rawTicker.trim().toUpperCase();
    }

    // ----------------------------------------------------------------
    // Conversion Helpers
    // ----------------------------------------------------------------

    /**
     * Maps an EquityEntity (persistence layer) to an EquityDTO (API layer).
     * No JPA-managed references leak across this boundary.
     *
     * @param entity source JPA entity
     * @return clean DTO populated from entity fields
     */
    private EquityDTO mapEntityToDto(EquityEntity entity) {
        return new EquityDTO(
                entity.getEquityId(),
                entity.getTicker(),
                entity.getCompanyName(),
                entity.getSector(),
                entity.getExchange(),
                entity.getIsActive(),
                entity.getCreatedAt()
        );
    }

    /**
     * Maps an EquityDTO (API layer) to a transient EquityEntity (persistence layer).
     * The equityId field is intentionally excluded so Hibernate treats this as a
     * new INSERT rather than an UPDATE.
     *
     * @param dto source data-transfer object
     * @return transient EquityEntity ready for persistence
     */
    private EquityEntity mapDtoToEntity(EquityDTO dto) {
        EquityEntity entity = new EquityEntity();
        entity.setTicker(dto.getTicker());
        entity.setCompanyName(dto.getCompanyName());
        entity.setSector(dto.getSector());
        entity.setExchange(dto.getExchange());
        entity.setIsActive(dto.getIsActive());
        entity.setCreatedAt(dto.getCreatedAt());
        return entity;
    }
}
