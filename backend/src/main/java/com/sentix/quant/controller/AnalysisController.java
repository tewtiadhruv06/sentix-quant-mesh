package com.sentix.quant.controller;

import com.sentix.quant.dto.FinancialRecordDTO;
import com.sentix.quant.dto.MlPredictionDTO;
import com.sentix.quant.dto.UnifiedAnalysisDTO;
import com.sentix.quant.dto.EquityDTO;
import com.sentix.quant.entity.EquityEntity;
import com.sentix.quant.repository.EquityRepository;
import com.sentix.quant.service.FinancialRecordService;
import com.sentix.quant.service.MlIntegrationService;
import com.sentix.quant.service.ValuationService;
import com.sentix.quant.service.EquityService;
import com.sentix.quant.service.FmpDataService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Optional;

/**
 * Aggregation controller that unifies DCF valuation data from
 * {@link FinancialRecordService} with XGBoost ML predictions from
 * {@link MlIntegrationService} into a single JSON response for the
 * Angular frontend.
 *
 * <p>Endpoint: {@code GET /api/v1/analysis/{ticker}}
 */
@RestController
@RequestMapping("/api/v1/analysis")
@CrossOrigin(origins = "http://localhost:4200")
public class AnalysisController {

    private static final Logger logger = LoggerFactory.getLogger(AnalysisController.class);

    private final EquityRepository equityRepository;
    private final FinancialRecordService financialRecordService;
    private final MlIntegrationService mlIntegrationService;
    private final ValuationService valuationService;
    private final EquityService equityService;
    private final FmpDataService fmpDataService;

    public AnalysisController(EquityRepository equityRepository,
                              FinancialRecordService financialRecordService,
                              MlIntegrationService mlIntegrationService,
                              ValuationService valuationService,
                              EquityService equityService,
                              FmpDataService fmpDataService) {
        this.equityRepository = equityRepository;
        this.financialRecordService = financialRecordService;
        this.mlIntegrationService = mlIntegrationService;
        this.valuationService = valuationService;
        this.equityService = equityService;
        this.fmpDataService = fmpDataService;
    }

    // ----------------------------------------------------------------
    // Endpoints
    // ----------------------------------------------------------------

    /**
     * GET /api/v1/analysis/{ticker}
     *
     * <p>Aggregates DCF valuation and ML prediction data for the given ticker
     * into a single {@link UnifiedAnalysisDTO}. The execution flow is:
     * <ol>
     *   <li>Resolve {@code ticker} → {@code equityId} via {@link EquityRepository}</li>
     *   <li>Fetch the most recent {@link FinancialRecordDTO} for that equity</li>
     *   <li>Fetch the {@link MlPredictionDTO} from the Python ML service</li>
     *   <li>Return both wrapped in a {@link UnifiedAnalysisDTO} with HTTP 200</li>
     * </ol>
     *
     * <p>Returns HTTP 404 if the ticker is not registered in the equities table.
     *
     * @param ticker the stock ticker symbol (e.g. "AAPL")
     * @return ResponseEntity wrapping the unified analysis payload
     */
    @GetMapping("/{ticker}")
    public ResponseEntity<?> getUnifiedAnalysis(@PathVariable String ticker) {

        // Step 1: Resolve raw input → canonical ticker symbol
        String resolvedTicker = equityService.resolveTickerSymbol(ticker);
        logger.info("Ticker resolution: [{}] → [{}]", ticker, resolvedTicker);
        Optional<EquityEntity> equityOpt = equityRepository.findByTicker(resolvedTicker);

        if (equityOpt.isEmpty()) {
            var profile = fmpDataService.fetchProfile(resolvedTicker);
            if (profile.isEmpty()) {
                logger.warn("FMP could not resolve ticker [{}]", resolvedTicker);
                return ResponseEntity.notFound().build();
            }

            EquityDTO equityDto = new EquityDTO();
            equityDto.setTicker(resolvedTicker);
            equityDto.setCompanyName(text(profile, "companyName", resolvedTicker));
            equityDto.setSector(text(profile, "sector", "Unknown"));
            equityDto.setExchange(text(profile, "exchangeShortName", "Unknown"));
            equityDto.setIsActive(true);
            EquityEntity fetchedEquity = toEntity(equityService.registerEquity(equityDto));
            fetchedEquity.setIndustry(text(profile, "industry", ""));
            equityOpt = Optional.of(fetchedEquity);
        }

        Long equityId = equityOpt.get().getEquityId();

        // Step 2: Fetch DCF valuation data (most recent record)
        List<FinancialRecordDTO> records = financialRecordService.getRecordsByEquityId(equityId);
        if (records.isEmpty()) {
            financialRecordService.saveRecord(fmpDataService.fetchLatestFinancialRecord(resolvedTicker, equityId));
            records = financialRecordService.getRecordsByEquityId(equityId);
        }
        FinancialRecordDTO dcfValuation = records.isEmpty() ? null : records.get(records.size() - 1);

        // Step 3: Fetch ML prediction from Python microservice
        MlPredictionDTO mlPrediction = mlIntegrationService.fetchPrediction(resolvedTicker);

        // Step 4: Aggregate and return
        EquityEntity equity = equityOpt.get();
        UnifiedAnalysisDTO unified = valuationService.buildUnifiedValuation(equity, dcfValuation);
        unified.setMlPrediction(mlPrediction);

        logger.info("Unified analysis assembled for [{}] (resolved from [{}]): dcf={}, ml={}",
                resolvedTicker, ticker, dcfValuation != null, mlPrediction != null);

        return ResponseEntity.ok(unified);
    }

    private String text(java.util.Map<String, Object> values, String key, String fallback) {
        Object value = values.get(key);
        return value == null || value.toString().isBlank() ? fallback : value.toString();
    }

    private EquityEntity toEntity(EquityDTO dto) {
        EquityEntity entity = new EquityEntity(dto.getTicker(), dto.getCompanyName(), dto.getSector(),
                dto.getExchange(), dto.getIsActive(), dto.getCreatedAt());
        entity.setEquityId(dto.getEquityId());
        return entity;
    }
}
