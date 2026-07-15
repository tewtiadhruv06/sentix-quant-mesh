package com.sentix.quant.repository;

import com.sentix.quant.entity.EquityEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface EquityRepository extends JpaRepository<EquityEntity, Long> {

    /**
     * Derived query method: SELECT * FROM equities WHERE ticker = ?1
     * Returns an Optional to enforce explicit null-handling at the service layer.
     *
     * @param ticker the stock ticker symbol (e.g. "AAPL", "RELIANCE")
     * @return an Optional wrapping the matched EquityEntity, or empty if none found
     */
    Optional<EquityEntity> findByTicker(String ticker);
}
