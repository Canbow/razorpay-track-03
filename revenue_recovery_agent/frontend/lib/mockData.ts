import { BenchmarkKPIs, ProcessedEvent } from './types';

export const initialKPIs: BenchmarkKPIs = {
  total_transactions: 60,
  total_at_risk: 262800.0,
  total_recovered: 162300.0,
  total_unrecovered: 100500.0,
  recovery_percentage: 61.8,
  baseline_recovered: 16700.0,
  baseline_percentage: 6.4,
  net_uplift: 145600.0,
  double_debit_violations: 0,
  trai_compliance_violations: 0,
  baseline_trai_violations: 13,
};

export const initialEvents: ProcessedEvent[] = [
  {
    invoice_id: "INV-REC-0001",
    customer_id: "CUST-1001",
    amount: 1800.0,
    payment_rail: "MANDATE",
    error_code: "NETWORK_ERROR",
    error_description: "TCP handshake failure between gateway and NPCI switch",
    attempt_count: 0,
    failed_at: "2026-09-03T14:15:00.000Z",
    category: "TRANSIENT_DOWNTIME",
    guard_passed: true,
    guard_message: "PASSED_ALL_GUARDRAILS",
    recovery_status: "RECOVERED",
    recovery_plan: {
      invoice_id: "INV-REC-0001",
      action: "SCHEDULED_SILENT_RETRY",
      target_rail: "MANDATE",
      scheduled_at: "2026-09-04T02:15:00.000Z",
      reasoning: "Transient downtime diagnosed. Scheduled silent off-peak retry (+12h cooldown)."
    },
    is_recovered: true
  },
  {
    invoice_id: "INV-REC-0002",
    customer_id: "CUST-1002",
    amount: 4300.0,
    payment_rail: "MANDATE",
    error_code: "ISSUER_DOWN",
    error_description: "Issuing bank core banking system unreachable",
    attempt_count: 0,
    failed_at: "2026-09-03T14:15:00.000Z",
    category: "TRANSIENT_DOWNTIME",
    guard_passed: true,
    guard_message: "PASSED_ALL_GUARDRAILS",
    recovery_status: "RECOVERED",
    recovery_plan: {
      invoice_id: "INV-REC-0002",
      action: "SCHEDULED_SILENT_RETRY",
      target_rail: "MANDATE",
      scheduled_at: "2026-09-04T02:15:00.000Z",
      reasoning: "Transient downtime diagnosed. Scheduled silent off-peak retry (+12h cooldown)."
    },
    is_recovered: true
  },
  {
    invoice_id: "INV-REC-0026",
    customer_id: "CUST-1026",
    amount: 2500.0,
    payment_rail: "CARD",
    error_code: "INSUFFICIENT_FUNDS",
    error_description: "Customer account has insufficient funds for clearing",
    attempt_count: 0,
    failed_at: "2026-09-03T11:30:00.000Z",
    category: "CUSTOMER_ACTIONABLE",
    guard_passed: true,
    guard_message: "PASSED_ALL_GUARDRAILS",
    recovery_status: "RECOVERED",
    recovery_plan: {
      invoice_id: "INV-REC-0026",
      action: "DISPATCH_DYNAMIC_LINK",
      target_rail: "UPI",
      dynamic_link: "https://pay.rzp.io/recover/INV-REC-0026?rail=UPI&auth=intent",
      reasoning: "Customer actionable failure. Generated dynamic link with smart fallback to UPI Intent."
    },
    is_recovered: true
  },
  {
    invoice_id: "INV-REC-0046",
    customer_id: "CUST-1046",
    amount: 1000.0,
    payment_rail: "UPI",
    error_code: "INSUFFICIENT_FUNDS",
    error_description: "Account balance depleted after multiple debit attempts",
    attempt_count: 2,
    failed_at: "2026-09-03T09:46:00.000Z",
    category: "EXHAUSTED_LIMIT",
    guard_passed: false,
    guard_message: "MAX_RETRY_EXCEEDED: attempt count 2 reaches/exceeds limit 2",
    recovery_status: "ABORTED_MAX_RETRIES",
    recovery_plan: {
      invoice_id: "INV-REC-0046",
      action: "ABORT_TERMINAL",
      reasoning: "Hard stopping rule enforced: attempt count 2 reaches/exceeds limit 2"
    },
    is_recovered: false
  },
  {
    invoice_id: "INV-REC-0053",
    customer_id: "CUST-1053",
    amount: 4200.0,
    payment_rail: "CARD",
    error_code: "ACCOUNT_CLOSED",
    error_description: "Drawee account permanently closed or non-existent",
    attempt_count: 0,
    failed_at: "2026-09-03T11:53:00.000Z",
    category: "TERMINAL_FAILURE",
    guard_passed: true,
    guard_message: "PASSED_ALL_GUARDRAILS",
    recovery_status: "FAILED",
    recovery_plan: {
      invoice_id: "INV-REC-0053",
      action: "ABORT_TERMINAL",
      reasoning: "Terminal failure detected for ACCOUNT_CLOSED. Aborting dunning sequence."
    },
    is_recovered: false
  }
];
