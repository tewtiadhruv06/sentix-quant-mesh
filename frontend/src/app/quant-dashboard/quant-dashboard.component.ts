import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule, KeyValuePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { UnifiedAnalysis } from '../models/analysis.model';

/**
 * Describes a single displayable metric row in the valuation panel.
 */
interface MetricEntry {
  label: string;
  value: string;
  highlight: boolean;   // true → render in accent colour
}

@Component({
  selector: 'sentix-quant-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, KeyValuePipe],
  templateUrl: './quant-dashboard.component.html',
  styleUrl: './quant-dashboard.component.css'
})
export class QuantDashboardComponent {

  // ── Binding State ──────────────────────────────────────────
  tickerInput: string = '';
  analysisData: UnifiedAnalysis | null = null;
  isLoading: boolean = false;
  errorMessage: string = '';

  /** Structured metric rows, built after each successful fetch */
  valuationMetrics: MetricEntry[] = [];

  /** Dynamically resolved panel badge text */
  valuationBadge: string = '';

  /** True when the response contains CCA (bank) metrics rather than DCF */
  isCcaModel: boolean = false;

  // ── API Configuration ──────────────────────────────────────
  private readonly API_BASE = 'http://localhost:8080/api/v1/analysis';

  constructor(private http: HttpClient) {}

  // ── Public Methods ─────────────────────────────────────────

  /**
   * Executes the unified analysis by calling the Spring Boot
   * aggregation endpoint for the entered query (ticker or company name).
   */
  executeAnalysis(): void {
    const query = this.tickerInput.trim();

    if (!query) {
      this.errorMessage = 'QUERY REQUIRED — Enter a valid ticker symbol or company name.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.analysisData = null;
    this.valuationMetrics = [];

    this.http.get<UnifiedAnalysis>(`${this.API_BASE}/${encodeURIComponent(query)}`).subscribe({
      next: (data) => {
        this.analysisData = data;
        this.buildMetrics(data);
        this.isLoading = false;
      },
      error: (err) => {
        this.isLoading = false;
        if (err.status === 404) {
          this.errorMessage = `SYMBOL NOT FOUND — "${query}" is not registered in the equity database.`;
        } else if (err.status === 0) {
          this.errorMessage = 'CONNECTION REFUSED — Backend service at localhost:8080 is unreachable.';
        } else {
          this.errorMessage = `SERVER ERROR [${err.status}] — ${err.message || 'Unknown failure.'}`;
        }
      }
    });
  }

  // ── Template Helpers ───────────────────────────────────────

  /**
   * Formats large numbers with commas and dollar sign.
   * e.g. 416161000000 → $416,161,000,000
   */
  formatCurrency(value: number | null | undefined): string {
    if (value === null || value === undefined) return 'N/A';
    const abs = Math.abs(value);
    const formatted = abs.toLocaleString('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    });
    return value < 0 ? `-$${formatted}` : `$${formatted}`;
  }

  /**
   * Formats a decimal as a percentage string.
   * e.g. 0.958 → 95.80%
   */
  formatPercent(value: number | null | undefined): string {
    if (value === null || value === undefined) return 'N/A';
    return (value * 100).toFixed(2) + '%';
  }

  /**
   * Formats large share counts with commas.
   */
  formatShares(value: number | null | undefined): string {
    if (value === null || value === undefined) return 'N/A';
    return value.toLocaleString('en-US');
  }

  /**
   * Returns the human-readable prediction verdict.
   */
  getPredictionLabel(code: number | null | undefined): string {
    if (code === null || code === undefined) return 'NO DATA';
    switch (code) {
      case 1:  return 'OUTPERFORM';
      case 0:  return 'NEUTRAL/UNDERPERFORM';
      case -1: return 'ENGINE OFFLINE';
      default: return 'UNKNOWN';
    }
  }

  /**
   * Returns the CSS class for conditional color styling.
   */
  getPredictionClass(code: number | null | undefined): string {
    if (code === null || code === undefined) return 'verdict-offline';
    switch (code) {
      case 1:  return 'verdict-outperform';
      case 0:  return 'verdict-underperform';
      case -1: return 'verdict-offline';
      default: return 'verdict-offline';
    }
  }

  // ── Private Helpers ────────────────────────────────────────

  /**
   * Human-readable labels for camelCase metric keys.
   */
  private static readonly LABEL_MAP: Record<string, string> = {
    totalRevenue:             'TOTAL REVENUE',
    ebit:                     'EBIT',
    pretaxIncome:             'PRETAX INCOME',
    cashAndEquivalents:       'CASH & EQUIVALENTS',
    taxProvision:             'TAX PROVISION',
    interestExpense:          'INTEREST EXPENSE',
    currentDebt:              'CURRENT DEBT',
    longTermDebt:             'LONG-TERM DEBT',
    capitalExpenditure:       'CAPEX',
    depreciationAmortization: 'D&A',
    sharesOutstanding:        'SHARES OUTSTANDING',
    priceToBook:              'PRICE / BOOK',
    roe:                      'RETURN ON EQUITY',
    priceToEarnings:          'PRICE / EARNINGS',
  };

  /** Keys that should be highlighted in accent colour */
  private static readonly HIGHLIGHT_KEYS = new Set([
    'totalRevenue', 'ebit', 'pretaxIncome', 'cashAndEquivalents',
    'sharesOutstanding', 'priceToBook', 'roe', 'priceToEarnings',
  ]);

  /** Keys that represent ratio / percentage values */
  private static readonly RATIO_KEYS = new Set([
    'roe',
  ]);

  /** Keys that represent share counts (not currency) */
  private static readonly SHARES_KEYS = new Set([
    'sharesOutstanding',
  ]);

  /** Keys that represent pure multiples (no $ or % formatting) */
  private static readonly MULTIPLE_KEYS = new Set([
    'priceToBook', 'priceToEarnings',
  ]);

  /** Keys to skip (metadata, not metrics) */
  private static readonly SKIP_KEYS = new Set([
    'recordId', 'equityId', 'fiscalYear', 'fiscalQuarter',
  ]);

  /**
   * Inspects the unified response and builds the flat metric list
   * that the template iterates via *ngFor.
   */
  private buildMetrics(data: UnifiedAnalysis): void {
    const fund = data.fundamental;

    // Determine which model is active
    if (fund?.ccaMetrics) {
      this.isCcaModel = true;
      this.valuationBadge = 'CCA BANK';
      this.valuationMetrics = this.objectToMetrics(fund.ccaMetrics);
    } else if (fund?.dcfValuation) {
      this.isCcaModel = false;
      this.valuationBadge = `FY${fund.dcfValuation.fiscalYear ?? '—'} Q${fund.dcfValuation.fiscalQuarter ?? '—'}`;
      this.valuationMetrics = this.objectToMetrics(fund.dcfValuation);
    } else if (data.dcfValuation) {
      // Fallback: top-level dcfValuation (legacy shape)
      this.isCcaModel = false;
      this.valuationBadge = `FY${data.dcfValuation.fiscalYear ?? '—'} Q${data.dcfValuation.fiscalQuarter ?? '—'}`;
      this.valuationMetrics = this.objectToMetrics(data.dcfValuation);
    } else {
      this.isCcaModel = false;
      this.valuationBadge = '';
      this.valuationMetrics = [];
    }
  }

  /**
   * Converts any flat object to a list of MetricEntry, applying
   * contextual formatting per key type.
   */
  private objectToMetrics(obj: Record<string, any>): MetricEntry[] {
    const entries: MetricEntry[] = [];

    for (const [key, raw] of Object.entries(obj)) {
      if (QuantDashboardComponent.SKIP_KEYS.has(key)) continue;

      const label = QuantDashboardComponent.LABEL_MAP[key] ?? this.camelToTitle(key);
      const highlight = QuantDashboardComponent.HIGHLIGHT_KEYS.has(key);
      const value = this.formatDynamic(key, raw);

      entries.push({ label, value, highlight });
    }
    return entries;
  }

  /**
   * Routes a value through the appropriate formatter based on its key type.
   */
  private formatDynamic(key: string, raw: any): string {
    if (raw === null || raw === undefined) return 'N/A';

    const num = typeof raw === 'number' ? raw : parseFloat(raw);
    if (isNaN(num)) return String(raw);

    if (QuantDashboardComponent.RATIO_KEYS.has(key)) {
      return this.formatPercent(num);
    }
    if (QuantDashboardComponent.SHARES_KEYS.has(key)) {
      return this.formatShares(num);
    }
    if (QuantDashboardComponent.MULTIPLE_KEYS.has(key)) {
      return num.toFixed(2) + '×';
    }
    // Default: currency
    return this.formatCurrency(num);
  }

  /**
   * Converts a camelCase key to a spaced uppercase title.
   * e.g. "priceToBook" → "PRICE TO BOOK"
   */
  private camelToTitle(key: string): string {
    return key
      .replace(/([A-Z])/g, ' $1')
      .trim()
      .toUpperCase();
  }
}
