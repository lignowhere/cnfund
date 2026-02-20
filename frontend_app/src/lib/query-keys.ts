export const queryKeys = {
  featureFlags: (token: string) => ["feature-flags", token] as const,
  dashboard: (token: string) => ["dashboard", token] as const,
  navHistory: (token: string) => ["nav-history", token] as const,
  dashboardTransactionsSummary: (token: string) =>
    ["dashboard-transactions-summary", token] as const,
  investorOptions: (token: string) => ["investor-options", token] as const,
  investorCards: (token: string) => ["investor-cards", token] as const,
  provinces: (token: string) => ["provinces", token] as const,
  wards: (token: string, provinceCode: string) => ["wards", token, provinceCode] as const,
  investorDetail: (token: string, investorId: number | null | undefined, nav?: number) =>
    ["investor-detail", token, investorId ?? null, nav ?? null] as const,
  transactionCards: (token: string) => ["transaction-cards", token] as const,
  transactionsReport: (
    token: string,
    params: {
      page: number;
      pageSize: number;
      txType?: string;
      investorId?: number;
      startDate?: string;
      endDate?: string;
    },
  ) =>
    [
      "transactions-report",
      token,
      params.page,
      params.pageSize,
      params.txType ?? null,
      params.investorId ?? null,
      params.startDate ?? null,
      params.endDate ?? null,
    ] as const,
  investorReport: (token: string, investorId: number, nav?: number) =>
    ["investor-report", token, investorId, nav ?? null] as const,
  feeHistory: (token: string) => ["fee-history", token] as const,
  backups: (token: string) => ["backups", token] as const,
};
