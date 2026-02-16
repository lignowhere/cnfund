"use client";

import type { ApiResponse, TokenPair, UserInfo } from "@/lib/types";
import { buildApiUrl, resolveApiBaseUrl } from "@/lib/api-base";
import { buildNetworkError } from "@/lib/network-error";

const API_BASE_URL =
  resolveApiBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL);

async function parseApiResponse<T>(response: Response): Promise<T> {
  const payload = (await response.json()) as ApiResponse<T>;
  return payload.data;
}

async function getErrorDetail(response: Response): Promise<string> {
  const raw = await response.text();
  try {
    const parsed = JSON.parse(raw) as { detail?: string };
    return parsed.detail || raw;
  } catch {
    return raw || `Request failed with ${response.status} at ${response.url}`;
  }
}

async function safeFetch(path: string, init: RequestInit): Promise<Response> {
  try {
    return await fetch(buildApiUrl(API_BASE_URL, path), init);
  } catch (error) {
    throw buildNetworkError(error, API_BASE_URL);
  }
}

export const authApi = {
  async login(username: string, password: string): Promise<TokenPair> {
    const response = await safeFetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error(await getErrorDetail(response));
    }
    return parseApiResponse<TokenPair>(response);
  },

  async refresh(refreshToken: string): Promise<TokenPair> {
    const response = await safeFetch("/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error(await getErrorDetail(response));
    }
    return parseApiResponse<TokenPair>(response);
  },

  async logout(refreshToken: string): Promise<{ logged_out: boolean }> {
    const response = await safeFetch("/auth/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error(await getErrorDetail(response));
    }
    return parseApiResponse<{ logged_out: boolean }>(response);
  },

  async me(accessToken: string): Promise<UserInfo> {
    const response = await safeFetch("/auth/me", {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error(await getErrorDetail(response));
    }
    return parseApiResponse<UserInfo>(response);
  },
};
