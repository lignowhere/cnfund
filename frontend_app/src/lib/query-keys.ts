export const queryKeys = {
  featureFlags: () => ["feature-flags"] as const,
  dashboard: () => ["dashboard"] as const,
  navHistory: () => ["nav-history"] as const,
  dashboardTransactionsSummary: () =>
    ["dashboard-transactions-summary"] as const,
  investorOptions: () => ["investor-options"] as const,
  investorCards: () => ["investor-cards"] as const,
  provinces: () => ["provinces"] as const,
  wards: (provinceCode: string) => ["wards", provinceCode] as const,
  investorDetail: (investorId: number | null | undefined, nav?: number) =>
    ["investor-detail", investorId ?? null, nav ?? null] as const,
  transactionCards: () => ["transaction-cards"] as const,
  transactionsReport: (
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
      params.page,
      params.pageSize,
      params.txType ?? null,
      params.investorId ?? null,
      params.startDate ?? null,
      params.endDate ?? null,
    ] as const,
  investorReport: (investorId: number, nav?: number) =>
    ["investor-report", investorId, nav ?? null] as const,
  myInvestorReport: (nav?: number) =>
    ["my-investor-report", nav ?? null] as const,
  myTransactionsReport: (
    params: {
      page: number;
      pageSize: number;
      txType?: string;
      startDate?: string;
      endDate?: string;
    },
  ) =>
    [
      "my-transactions-report",
      params.page,
      params.pageSize,
      params.txType ?? null,
      params.startDate ?? null,
      params.endDate ?? null,
    ] as const,
  accountsInvestors: () => ["accounts-investors"] as const,
  feeHistory: () => ["fee-history"] as const,
  feeConfig: () => ["fee-config"] as const,
  backups: () => ["backups"] as const,
};
