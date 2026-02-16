"use client";

import type {
  ApiResponse,
  BackupListItemDTO,
  DashboardDTO,
  FeatureFlagsDTO,
  FeePreviewBundleDTO,
  InvestorReportDTO,
  InvestorCardDTO,
  NavPointDTO,
  PaginatedResponse,
  TokenPair,
  TransactionCardDTO,
  TransactionsReportDTO,
  ValidationErrorPayload,
} from "@/lib/types";
import { authApi } from "@/lib/auth-api";
import { buildNetworkError } from "@/lib/network-error";
import { useAuthStore } from "@/store/auth-store";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001/api/v1";

type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
  retryOnAuth?: boolean;
};

let refreshInFlight: Promise<void> | null = null;

async function ensureSessionRefreshed(): Promise<void> {
  if (refreshInFlight) {
    return refreshInFlight;
  }
  const state = useAuthStore.getState();
  refreshInFlight = state
    .refresh()
    .catch(async (error) => {
      await useAuthStore.getState().logout();
      throw error;
    })
    .finally(() => {
      refreshInFlight = null;
    });
  return refreshInFlight;
}

async function getErrorDetail(response: Response): Promise<string> {
  const raw = await response.text();
  try {
    const parsed = JSON.parse(raw) as {
      detail?: string | ValidationErrorPayload;
    };
    if (typeof parsed.detail === "string") {
      return parsed.detail;
    }
    if (parsed.detail && typeof parsed.detail === "object" && "errors" in parsed.detail) {
      const messages = Object.entries(parsed.detail.errors)
        .map(([field, errors]) => `${field}: ${errors.join(", ")}`)
        .join(" | ");
      return messages || "Dữ liệu không hợp lệ";
    }
    return raw;
  } catch {
    return raw || `Request failed with ${response.status}`;
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = options.token ?? useAuthStore.getState().accessToken;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: options.method || "GET",
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
      cache: "no-store",
    });
  } catch (error) {
    throw buildNetworkError(error, API_BASE_URL);
  }

  if (response.status === 401 && options.retryOnAuth !== false) {
    const canRefresh = Boolean(useAuthStore.getState().refreshToken);
    if (canRefresh) {
      try {
        await ensureSessionRefreshed();
        const renewedToken = useAuthStore.getState().accessToken;
        return request<T>(path, {
          ...options,
          token: renewedToken,
          retryOnAuth: false,
        });
      } catch {
        throw new Error("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
      }
    }
  }

  if (!response.ok) {
    throw new Error(await getErrorDetail(response));
  }

  const payload = (await response.json()) as ApiResponse<T>;
  return payload.data;
}

export const apiClient = {
  async login(username: string, password: string): Promise<TokenPair> {
    return authApi.login(username, password);
  },

  async refresh(refreshToken: string): Promise<TokenPair> {
    return authApi.refresh(refreshToken);
  },

  async logout(refreshToken: string): Promise<{ logged_out: boolean }> {
    return authApi.logout(refreshToken);
  },

  async me(token: string) {
    return authApi.me(token);
  },

  async dashboard(token: string): Promise<DashboardDTO> {
    return request<DashboardDTO>("/reports/dashboard", { token });
  },

  async investorReport(token: string, investorId: number, nav?: number): Promise<InvestorReportDTO> {
    const query = nav !== undefined ? `?nav=${nav}` : "";
    return request<InvestorReportDTO>(`/reports/investor/${investorId}${query}`, { token });
  },

  async transactionsReport(
    token: string,
    params?: {
      page?: number;
      page_size?: number;
      investor_id?: number;
      tx_type?: string;
    },
  ): Promise<TransactionsReportDTO> {
    const search = new URLSearchParams();
    if (params?.page) search.set("page", String(params.page));
    if (params?.page_size) search.set("page_size", String(params.page_size));
    if (params?.investor_id !== undefined) search.set("investor_id", String(params.investor_id));
    if (params?.tx_type) search.set("tx_type", params.tx_type);
    const query = search.toString();
    return request<TransactionsReportDTO>(`/reports/transactions${query ? `?${query}` : ""}`, {
      token,
    });
  },

  async navHistory(token: string): Promise<NavPointDTO[]> {
    return request<NavPointDTO[]>("/nav/history", { token });
  },

  async investorCards(token: string): Promise<InvestorCardDTO[]> {
    return request<InvestorCardDTO[]>("/investors/cards", { token });
  },

  async investorCardsPaginated(
    token: string,
    page = 1,
    pageSize = 20,
  ): Promise<PaginatedResponse<InvestorCardDTO>> {
    return request<PaginatedResponse<InvestorCardDTO>>(
      `/investors/cards/paginated?page=${page}&page_size=${pageSize}`,
      { token },
    );
  },

  async createInvestor(
    token: string,
    payload: { name: string; phone?: string; address?: string; email?: string },
  ) {
    return request("/investors", {
      method: "POST",
      token,
      body: payload,
    });
  },

  async updateInvestor(
    token: string,
    investorId: number,
    payload: { name?: string; phone?: string; address?: string; email?: string },
  ) {
    return request(`/investors/${investorId}`, {
      method: "PUT",
      token,
      body: payload,
    });
  },

  async transactionCards(
    token: string,
    page = 1,
    pageSize = 20,
  ): Promise<PaginatedResponse<TransactionCardDTO>> {
    return request<PaginatedResponse<TransactionCardDTO>>(
      `/transactions/cards?page=${page}&page_size=${pageSize}`,
      { token },
    );
  },

  async createTransaction(
    token: string,
    payload: {
      transaction_type: "deposit" | "withdraw" | "nav_update";
      investor_id?: number;
      amount?: number;
      total_nav: number;
      transaction_date: string;
    },
  ) {
    return request("/transactions", {
      method: "POST",
      token,
      body: payload,
    });
  },

  async deleteTransaction(token: string, transactionId: number) {
    return request(`/transactions/${transactionId}`, {
      method: "DELETE",
      token,
    });
  },

  async undoTransaction(token: string, transactionId: number) {
    return request(`/transactions/${transactionId}/undo`, {
      method: "POST",
      token,
    });
  },

  async previewFees(
    token: string,
    payload: { end_date: string; total_nav: number },
  ): Promise<FeePreviewBundleDTO> {
    return request<FeePreviewBundleDTO>("/fees/preview", {
      method: "POST",
      token,
      body: payload,
    });
  },

  async applyFees(
    token: string,
    payload: {
      year: number;
      end_date: string;
      total_nav: number;
      confirm_token: string;
      acknowledge_risk: boolean;
      acknowledge_backup: boolean;
    },
  ) {
    return request("/fees/apply", {
      method: "POST",
      token,
      body: payload,
    });
  },

  async feeHistory(token: string): Promise<
    Array<{
      id: number;
      period: string;
      investor_id: number;
      fee_amount: number;
      fee_units: number;
      calculation_date: string;
      description: string;
    }>
  > {
    return request("/fees/history", { token });
  },

  async backups(token: string): Promise<BackupListItemDTO[]> {
    return request<BackupListItemDTO[]>("/backups", { token });
  },

  async featureFlags(token: string): Promise<FeatureFlagsDTO> {
    return request<FeatureFlagsDTO>("/system/feature-flags", { token });
  },

  async manualBackup(token: string): Promise<{ backup_id: string }> {
    return request<{ backup_id: string }>("/backups/manual", {
      method: "POST",
      token,
    });
  },

  async restoreBackup(
    token: string,
    payload: {
      backup_id: string;
      confirm_phrase: string;
      create_safety_backup: boolean;
    },
  ) {
    return request("/backups/restore", {
      method: "POST",
      token,
      body: payload,
    });
  },
};
