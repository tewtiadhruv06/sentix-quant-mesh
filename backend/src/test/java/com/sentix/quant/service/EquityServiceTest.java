package com.sentix.quant.service;

import com.sentix.quant.dto.EquityDTO;
import com.sentix.quant.entity.EquityEntity;
import com.sentix.quant.repository.EquityRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import java.time.LocalDateTime;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

class EquityServiceTest {

    private EquityRepository equityRepository;
    private FmpDataService fmpDataService;
    private EquityService equityService;

    @BeforeEach
    void setUp() {
        equityRepository = Mockito.mock(EquityRepository.class);
        fmpDataService = Mockito.mock(FmpDataService.class);
        equityService = new EquityService(equityRepository, fmpDataService);
    }

    @Test
    void resolveTickerSymbol_shouldStandardizeExactTickerMatch() {
        EquityEntity entity = new EquityEntity();
        entity.setTicker("TSLA");
        entity.setCompanyName("Tesla Inc.");
        entity.setSector("Automotive");
        entity.setExchange("NASDAQ");
        entity.setIsActive(true);
        entity.setCreatedAt(LocalDateTime.now());

        when(equityRepository.findByTicker("TESLA")).thenReturn(Optional.empty());
        when(fmpDataService.searchTicker("tesla")).thenReturn("TSLA");

        String resolved = equityService.resolveTickerSymbol("tesla");

        assertEquals("TSLA", resolved);
    }

    @Test
    void resolveTickerSymbol_shouldFallbackToFmpSearchWhenNameIsProvided() {
        when(equityRepository.findByTicker("MICROSOFT")).thenReturn(Optional.empty());
        when(fmpDataService.searchTicker("microsoft")).thenReturn("MSFT");

        String resolved = equityService.resolveTickerSymbol("microsoft");

        assertEquals("MSFT", resolved);
    }

    @Test
    void registerEquity_shouldNormalizeTickerToUppercase() {
        EquityDTO dto = new EquityDTO();
        dto.setTicker("aapl");
        dto.setCompanyName("Apple Inc.");
        dto.setSector("Technology");
        dto.setExchange("NASDAQ");
        dto.setIsActive(true);
        dto.setCreatedAt(LocalDateTime.now());

        when(equityRepository.findByTicker(anyString())).thenReturn(Optional.empty());
        when(equityRepository.save(Mockito.any(EquityEntity.class)))
                .thenAnswer(invocation -> {
                    EquityEntity entity = invocation.getArgument(0);
                    entity.setEquityId(99L);
                    return entity;
                });

        EquityDTO saved = equityService.registerEquity(dto);

        assertEquals("AAPL", saved.getTicker());
    }
}
