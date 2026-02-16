export type UserRole = "viewer" | "admin" | "fund_manager";

export type ApiResponse<T> = {
  success: boolean;
  message?: string;
  data: T;
};

export type ValidationErrorPayload = {
  code: "validation_error";
  errors: Record<string, string[]>;
};

export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type UserInfo = {
  username: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

export type InvestorCardDTO = {
  id: number;
  display_name: string;
  phone: string;
  email: string;
  current_value: number;
  pnl: number;
  pnl_percent: number;
};

export type TransactionCardDTO = {
  id: number;
  investor_name: string;
  type: string;
  amount: number;
  nav: number;
  date: string;
  units_change: number;
};

export type DashboardKPI = {
  total_nav: number;
  total_investors: number;
  total_units: number;
  total_fees_paid: number;
  fund_manager_value: number;
  gross_return: number;
};

export type DashboardDTO = {
  kpis: DashboardKPI;
  top_investors: DashboardTopInvestor[];
};

export type DashboardTopInvestor = {
  investor_id: number;
  investor_name: string;
  balance: number;
  profit: number;
  profit_percent: number;
};

export type FeePreviewDTO = {
  investor_id: number;
  investor_name: string;
  fee_amount: number;
  fee_rate_percent: number;
  units_to_transfer: number;
  excess_profit: number;
};

export type FeePreviewBundleDTO = {
  items: FeePreviewDTO[];
  summary: {
    total_fee_amount: number;
    total_units_to_transfer: number;
    investor_count: number;
  };
  confirm_token: string;
  generated_at: string;
};

export type FeatureFlagsDTO = {
  table_view: boolean;
  backup_restore: boolean;
  fee_safety: boolean;
  transactions_load_more: boolean;
};

export type NavPointDTO = {
  date: string;
  nav: number;
  type: string;
};

export type BackupListItemDTO = {
  backup_id: string;
  backup_type: string;
  created_at: string;
  metadata: Record<string, unknown>;
};

export type InvestorProfileDTO = {
  id: number;
  name: string;
  phone: string;
  email: string;
  address: string;
  join_date: string;
};

export type InvestorLifetimeDTO = {
  original_invested: number;
  current_value: number;
  total_fees_paid: number;
  gross_profit: number;
  net_profit: number;
  gross_return: number;
  net_return: number;
  current_units: number;
};

export type InvestorFeeDetailsDTO = {
  total_fee: number;
  balance: number;
  invested_value: number;
  profit: number;
  profit_perc: number;
  hurdle_value: number;
  hwm_value: number;
  excess_profit: number;
  units_before: number;
  units_after: number;
};

export type InvestorTrancheDTO = {
  tranche_id: string;
  entry_date: string;
  entry_nav: number;
  units: number;
  hwm: number;
  invested_value: number;
  original_invested_value: number;
  cumulative_fees_paid: number;
};

export type InvestorReportDTO = {
  investor: InvestorProfileDTO;
  current_balance: number;
  current_profit: number;
  current_profit_perc: number;
  lifetime_performance: InvestorLifetimeDTO;
  fee_details: InvestorFeeDetailsDTO;
  tranches: InvestorTrancheDTO[];
  transactions: Array<{
    id: number;
    investor_id: number;
    investor_name: string;
    date: string;
    type: string;
    amount: number;
    nav: number;
    units_change: number;
  }>;
  fee_history: Array<{
    id: number;
    period: string;
    investor_id: number;
    fee_amount: number;
    fee_units: number;
    calculation_date: string;
    description: string;
  }>;
  report_date: string;
  current_nav: number;
  current_price: number;
};

export type TransactionsReportSummaryDTO = {
  total_count: number;
  total_volume: number;
  net_cash_flow: number;
  by_type: Record<string, number>;
  earliest_date: string | null;
  latest_date: string | null;
};

export type TransactionsReportDTO = {
  summary: TransactionsReportSummaryDTO;
  items: Array<{
    id: number;
    investor_id: number;
    investor_name: string;
    date: string;
    type: string;
    amount: number;
    nav: number;
    units_change: number;
  }>;
  total: number;
  page: number;
  page_size: number;
};
