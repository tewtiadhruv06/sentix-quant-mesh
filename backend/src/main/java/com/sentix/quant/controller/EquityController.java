package com.sentix.quant.controller;

import com.sentix.quant.dto.EquityDTO;
import com.sentix.quant.service.EquityService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/equities")
public class EquityController {

    private final EquityService equityService;

    public EquityController(EquityService equityService) {
        this.equityService = equityService;
    }

    // ----------------------------------------------------------------
    // Endpoints
    // ----------------------------------------------------------------

    /**
     * POST /api/v1/equities
     * Registers a new equity instrument. Returns HTTP 201 (Created) on success.
     * Returns HTTP 409 (Conflict) when the ticker already exists.
     *
     * @param dto JSON payload containing equity registration fields
     * @return ResponseEntity wrapping the persisted EquityDTO or an error message
     */
    @PostMapping
    public ResponseEntity<?> registerEquity(@RequestBody EquityDTO dto) {
        try {
            EquityDTO saved = equityService.registerEquity(dto);
            return ResponseEntity.status(HttpStatus.CREATED).body(saved);
        } catch (IllegalStateException ex) {
            return ResponseEntity
                    .status(HttpStatus.CONFLICT)
                    .body(ex.getMessage());
        }
    }

    /**
     * GET /api/v1/equities
     * Returns all registered equity instruments as a JSON array.
     * Returns HTTP 200 (OK) with an empty array when no records exist.
     *
     * @return ResponseEntity wrapping the list of EquityDTOs
     */
    @GetMapping
    public ResponseEntity<List<EquityDTO>> getAllEquities() {
        List<EquityDTO> equities = equityService.getAllEquities();
        return ResponseEntity.ok(equities);
    }
}
