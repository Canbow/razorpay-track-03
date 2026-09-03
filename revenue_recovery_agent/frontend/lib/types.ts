export type PaymentRail = 'CARD' | 'UPI' | 'NETBANKING' | 'MANDATE';

export type FailureCategory = 'TRANSIENT_DOWNTIME' | 'CUSTOMER_ACTIONABLE' | 'TERMINAL_FAILURE' | 'EXHAUSTED_LIMIT';

export type RecoveryAction = 'SCHEDULED_SILENT_RETRY' | 'DISPATCH_DYNAMIC_LINK' | 'ABORT_TERMINAL';

export type PaymentStatus = 'FAILED' | 'RETRY_SCHEDULED' | 'LINK_DISPATCHED' | 'RECOVERED' | 'ABORTED_MAX_RETRIES';

export interface BenchmarkKPIs {
  total_transactions: number;
  total_at_risk: number;
  total_recovered: number;
  total_unrecovered: number;
  recovery_percentage: number;
  baseline_recovered: number;
  baseline_percentage: number;
  net_uplift: number;
  double_debit_violations: number;
  trai_compliance_violations: number;
  baseline_trai_violations: number;
}

export interface CategorySummaryItem {
  total: number;
  count: number;
  recovered: number;
  rec_count: number;
}

export interface ProcessedEvent {
  invoice_id: string;
  customer_id: string;
  amount: number;
  payment_rail: PaymentRail;
  error_code: string;
  error_description: string;
  attempt_count: number;
  failed_at: string;
  category: string;
  guard_passed: boolean;
  guard_message: string;
  recovery_status: string;
  recovery_plan?: {
    invoice_id: string;
    action: string;
    target_rail?: string;
    scheduled_at?: string;
    dynamic_link?: string;
    reasoning: string;
  };
  is_recovered: boolean;
}

export interface AuditRecord {
  timestamp: string;
  invoice_id: string;
  event_type: string;
  action: string;
  guard_check_passed: boolean;
  details: Record<string, any>;
}

export interface SimulateRequest {
  invoice_id: string;
  customer_id: string;
  amount: number;
  payment_rail: PaymentRail;
  error_code: string;
  error_description: string;
  attempt_count: number;
  current_hour_ist: number;
  is_locked: boolean;
}

export interface SimulateResponse {
  status: string;
  input_event: any;
  current_hour_ist: number;
  failure_category: string;
  guard_passed: boolean;
  guard_message: string;
  recovery_status: string;
  recovery_plan: {
    invoice_id: string;
    action: string;
    target_rail?: string;
    scheduled_at?: string;
    dynamic_link?: string;
    reasoning: string;
  };
  is_recovered: boolean;
  audit_record?: any;
}
