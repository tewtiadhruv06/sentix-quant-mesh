package com.sentix.quant.service;

import com.sentix.quant.dto.MlPredictionDTO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

/**
 * Integration service responsible for fetching machine-learning predictions
 * from the Python FastAPI microservice running at {@code http://127.0.0.1:8000}.
 *
 * <p>Design decisions:
 * <ul>
 *   <li>Uses Spring Boot 3.2's {@link RestClient} (preferred over the legacy
 *       {@code RestTemplate}) for a modern, fluent HTTP API.</li>
 *   <li>All network calls are wrapped in a try-catch so that an unreachable
 *       Python service never crashes the Java application. A fallback DTO with
 *       {@code outperformPrediction = -1} signals a failed prediction.</li>
 *   <li>This service is purely additive — it does not touch the existing DCF
 *       valuation pipeline.</li>
 * </ul>
 */
@Service
public class MlIntegrationService {

    private static final Logger logger = LoggerFactory.getLogger(MlIntegrationService.class);

    private static final String ML_SERVICE_BASE_URL = "http://127.0.0.1:8000";

    private final RestClient restClient;

    // ----------------------------------------------------------------
    // Constructor
    // ----------------------------------------------------------------

    public MlIntegrationService() {
        this.restClient = RestClient.builder()
                .baseUrl(ML_SERVICE_BASE_URL)
                .build();
    }

    // ----------------------------------------------------------------
    // Public API
    // ----------------------------------------------------------------

    /**
     * Requests an outperformance prediction for the given ticker from the
     * Python ML microservice.
     *
     * <p>Endpoint called: {@code GET http://127.0.0.1:8000/predict/{ticker}}
     *
     * <p>If the Python service is unreachable or returns an error, this method
     * logs a {@code SEVERE}-level warning and returns a fallback DTO with:
     * <ul>
     *   <li>{@code outperformPrediction = -1} (sentinel value)</li>
     *   <li>{@code confidenceScore = 0.0}</li>
     * </ul>
     *
     * @param ticker the equity ticker symbol (e.g. "AAPL")
     * @return a populated {@link MlPredictionDTO}, or a fallback on failure
     */
    public MlPredictionDTO fetchPrediction(String ticker) {
        try {
            MlPredictionDTO prediction = restClient.get()
                    .uri("/predict/{ticker}", ticker)
                    .retrieve()
                    .body(MlPredictionDTO.class);

            logger.info("ML prediction received for [{}]: {}", ticker, prediction);
            return prediction;

        } catch (Exception ex) {
            logger.error(
                    "SEVERE — Failed to reach Python ML service at {} for ticker [{}]. " +
                    "The Java application will continue with a fallback prediction. Cause: {}",
                    ML_SERVICE_BASE_URL, ticker, ex.getMessage()
            );

            return buildFallbackPrediction(ticker);
        }
    }

    // ----------------------------------------------------------------
    // Fallback Helper
    // ----------------------------------------------------------------

    /**
     * Constructs a sentinel DTO indicating that no valid prediction could be
     * obtained from the ML microservice.
     *
     * @param ticker the ticker for which the prediction failed
     * @return fallback DTO with {@code outperformPrediction = -1} and
     *         {@code confidenceScore = 0.0}
     */
    private MlPredictionDTO buildFallbackPrediction(String ticker) {
        return new MlPredictionDTO(ticker, -1, 0.0);
    }
}
