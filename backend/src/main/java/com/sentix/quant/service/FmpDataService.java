package com.sentix.quant.service;

import com.sentix.quant.dto.FinancialRecordDTO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestClient;

import java.math.BigDecimal;
import java.util.Map;
import java.time.LocalDate;

@Service
public class FmpDataService {

    private static final Logger logger = LoggerFactory.getLogger(FmpDataService.class);

    private static final String BASE_URL = "https://financialmodelingprep.com";
    private final RestClient restClient;
    private final String apiKey;

    public FmpDataService() {
        this(RestClient.builder().baseUrl(BASE_URL).build(),
                System.getProperty("fmp.api.key", "demo"));
    }

    FmpDataService(RestClient restClient, String apiKey) {
        this.restClient = restClient;
        this.apiKey = apiKey;
    }

    public String searchTicker(String query) {
        Map[] results = getArray("/api/v3/search", query, 1);
        if (results.length == 0) {
            logger.debug("FMP ticker search returned no results for query [{}]", query);
            return null;
        }
        Object symbol = results[0].get("symbol");
        return symbol == null ? null : symbol.toString().trim().toUpperCase();
    }

    public Map<String, Object> fetchProfile(String ticker) {
        Map[] results = getArray("/api/v3/profile/" + ticker, null, 1);
        return results.length == 0 ? Map.of() : results[0];
    }

    public Map<String, Object> fetchLatestIncomeStatement(String ticker) {
        return fetchLatest("/api/v3/income-statement/" + ticker);
    }

    public Map<String, Object> fetchLatestBalanceSheet(String ticker) {
        return fetchLatest("/api/v3/balance-sheet-statement/" + ticker);
    }

    public Map<String, Object> fetchLatestCashFlow(String ticker) {
        return fetchLatest("/api/v3/cash-flow-statement/" + ticker);
    }

    public FinancialRecordDTO fetchLatestFinancialRecord(String ticker, Long equityId) {
        Map<String, Object> income = fetchLatestIncomeStatement(ticker);
        Map<String, Object> balance = fetchLatestBalanceSheet(ticker);
        Map<String, Object> cashFlow = fetchLatestCashFlow(ticker);
        FinancialRecordDTO record = new FinancialRecordDTO();
        record.setEquityId(equityId);
        record.setFiscalYear(year(income, balance, cashFlow));
        record.setFiscalQuarter(0);
        record.setTotalRevenue(decimal(income, "revenue").orElse(null));
        record.setEbit(decimal(income, "ebit").orElse(decimal(income, "operatingIncome").orElse(null)));
        record.setInterestExpense(decimal(income, "interestExpense").orElse(null));
        record.setPretaxIncome(decimal(income, "incomeBeforeTax").orElse(null));
        record.setTaxProvision(decimal(income, "incomeTaxExpense").orElse(null));
        record.setCashAndEquivalents(decimal(balance, "cashAndCashEquivalents").orElse(null));
        record.setCurrentDebt(decimal(balance, "shortTermDebt").orElse(null));
        record.setLongTermDebt(decimal(balance, "longTermDebt").orElse(null));
        record.setCapitalExpenditure(decimal(cashFlow, "capitalExpenditure").orElse(null));
        record.setDepreciationAmortization(decimal(cashFlow, "depreciationAndAmortization").orElse(null));
        record.setSharesOutstanding(longValue(balance, "commonStockSharesOutstanding"));
        return record;
    }

    private Map<String, Object> fetchLatest(String path) {
        Map[] results = getArray(path, "period", 1);
        return results.length == 0 ? Map.of() : results[0];
    }

    private Map[] getArray(String path, String query, int limit) {
        try {
            Map[] results = restClient.get()
                    .uri(uriBuilder -> {
                        uriBuilder.path(path).queryParam("limit", limit).queryParam("apikey", apiKey);
                        if (query != null && !query.isBlank()) {
                            uriBuilder.queryParam("query", query.trim());
                        }
                        return uriBuilder.build();
                    })
                    .retrieve()
                    .body(Map[].class);
            return results == null ? new Map[0] : results;
        } catch (HttpClientErrorException ex) {
            int status = ex.getStatusCode().value();
            if (status == 401) {
                logger.error("FMP API 401 UNAUTHORIZED — API key is invalid or expired. Path: [{}]", path);
            } else if (status == 429) {
                logger.error("FMP API 429 TOO MANY REQUESTS — Rate limit exceeded. Path: [{}]", path);
            } else {
                logger.warn("FMP API HTTP {} error on path [{}]: {}", status, path, ex.getMessage());
            }
            return new Map[0];
        } catch (HttpServerErrorException ex) {
            logger.error("FMP API server error HTTP {} on path [{}]: {}",
                    ex.getStatusCode().value(), path, ex.getMessage());
            return new Map[0];
        } catch (Exception ex) {
            logger.warn("FMP API call failed for path [{}]: {}", path, ex.getMessage());
            return new Map[0];
        }
    }

    public static java.util.Optional<BigDecimal> decimal(Map<String, Object> values, String key) {
        Object value = values.get(key);
        if (value == null) {
            return java.util.Optional.empty();
        }
        try {
            return java.util.Optional.of(new BigDecimal(value.toString()));
        } catch (NumberFormatException ex) {
            return java.util.Optional.empty();
        }
    }

    public static Long longValue(Map<String, Object> values, String key) {
        return decimal(values, key).map(BigDecimal::longValue).orElse(null);
    }

    private Integer year(Map<String, Object>... statements) {
        for (Map<String, Object> statement : statements) {
            Object date = statement.get("date");
            if (date != null) {
                try {
                    return LocalDate.parse(date.toString()).getYear();
                } catch (RuntimeException ignored) {
                    // Continue to the next statement or use the current year.
                }
            }
        }
        return LocalDate.now().getYear();
    }
}
