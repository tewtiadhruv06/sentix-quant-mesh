package com.sentix.quant.controller;

import com.sentix.quant.dto.FinancialRecordDTO;
import com.sentix.quant.service.FinancialRecordService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/financials")
public class FinancialRecordController {

    private final FinancialRecordService financialRecordService;

    public FinancialRecordController(FinancialRecordService financialRecordService) {
        this.financialRecordService = financialRecordService;
    }

    // ----------------------------------------------------------------
    // Endpoints
    // ----------------------------------------------------------------

    /**
     * POST /api/v1/financials
     * Receives a financial record payload and delegates to the service layer
     * for upsert processing. Returns HTTP 201 (Created) on success.
     *
     * @param dto JSON payload containing financial record fields
     * @return ResponseEntity wrapping the persisted FinancialRecordDTO
     */
    @PostMapping
    public ResponseEntity<FinancialRecordDTO> ingestFinancialRecord(
            @RequestBody FinancialRecordDTO dto) {
        FinancialRecordDTO saved = financialRecordService.saveRecord(dto);
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }

    /**
     * GET /api/v1/financials
     * Returns all financial records as a JSON array.
     * Returns HTTP 200 (OK) with an empty array when no records exist.
     *
     * @return ResponseEntity wrapping the list of FinancialRecordDTOs
     */
    @GetMapping
    public ResponseEntity<List<FinancialRecordDTO>> getAllRecords() {
        List<FinancialRecordDTO> records = financialRecordService.getAllRecords();
        return ResponseEntity.ok(records);
    }
}
