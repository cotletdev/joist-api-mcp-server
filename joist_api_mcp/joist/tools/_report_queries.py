"""The Reports page's GraphQL queries (`POST /{user}/core_insights`), copied from the panel 26.10.2026."""

from __future__ import annotations

REVENUE = """query GetRevenuePaged($minDateRange: IsoDate,
  $maxDateRange: IsoDate,
  $pageNum: Int,
  $numEntriesPerPage: Int,
  $clientNames: [String!],
  $sortField: RevenueSortField,
  $sortDirection: SortDirection) {
  revenue(
    minDateRange: $minDateRange
    maxDateRange: $maxDateRange
    pageNum: $pageNum
    numEntriesPerPage: $numEntriesPerPage
    clientNames: $clientNames
    sortField: $sortField
    sortDirection: $sortDirection
  ) {
    page_number
    total_entries
    grand_total_amount
    reports {
      id
      doc_id
      original_id
      name
      document_date
      due_date
      fully_paid_date
      invoice_total
      payment_amount
      balance_at_beginning_of_period
      balance_at_end_of_period
      discount
      taxes
      markup
      currency_code
      __typename
    }
    __typename
  }
}"""

INVOICES = """query GetInvoicesPaged($minDateRange: IsoDate,
  $maxDateRange: IsoDate,
  $pageNum: Int,
  $numEntriesPerPage: Int,
  $clientNames: [String!],
  $sortField: InvoiceSortField,
  $sortDirection: SortDirection) {
  invoices(
    minDateRange: $minDateRange
    maxDateRange: $maxDateRange
    pageNum: $pageNum
    numEntriesPerPage: $numEntriesPerPage
    clientNames: $clientNames
    sortField: $sortField
    sortDirection: $sortDirection
  ) {
    page_number
    total_entries
    grand_total_amount
    reports {
      id
      doc_id
      original_id
      name
      document_date
      due_date
      fully_paid_date
      status
      total
      discount
      taxes
      markup
      amount_outstanding
      currency_code
      __typename
    }
    __typename
  }
}"""

ESTIMATES = """query GetEstimatesPaged($minDateRange: IsoDate,
  $maxDateRange: IsoDate,
  $pageNum: Int,
  $numEntriesPerPage: Int,
  $clientNames: [String!],
  $sortField: EstimateSortField,
  $sortDirection: SortDirection) {
  estimates(
    minDateRange: $minDateRange
    maxDateRange: $maxDateRange
    pageNum: $pageNum
    numEntriesPerPage: $numEntriesPerPage
    clientNames: $clientNames
    sortField: $sortField
    sortDirection: $sortDirection
  ) {
    page_number
    total_entries
    grand_total_amount
    reports {
      id
      doc_id
      original_id
      name
      expires_at
      status
      total
      currency_code
      __typename
    }
    __typename
  }
}"""

SALES_TAX = """query GetSalesTaxPaged($minDateRange: IsoDate,
  $maxDateRange: IsoDate,
  $pageNum: Int,
  $numEntriesPerPage: Int,
  $clientNames: [String!],
  $taxNames: [String!],
  $sortField: SalesTaxSortField,
  $sortDirection: SortDirection) {
  salesTaxes(
    minDateRange: $minDateRange
    maxDateRange: $maxDateRange
    pageNum: $pageNum
    numEntriesPerPage: $numEntriesPerPage
    clientNames: $clientNames
    taxNames: $taxNames
    sortField: $sortField
    sortDirection: $sortDirection
  ) {
    page_number
    total_entries
    grand_total_amount
    reports {
      doc_id
      original_id
      tax_name
      subtotal
      tax_rate
      tax_collected
      total
      fully_paid_date
      status
      name
      currency_code
      __typename
    }
    __typename
  }
}"""

GRAND_TOTALS = """query GetReportsGrandTotals($minDateRange: IsoDate!, $maxDateRange: IsoDate!) {
  reportsGrandTotals(minDateRange: $minDateRange, maxDateRange: $maxDateRange) {
    invoiceTotal: invoice_total
    revenueTotal: revenue_total
    estimatesTotal: estimates_total
    __typename
  }
}"""
