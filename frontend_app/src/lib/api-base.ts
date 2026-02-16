"use client";

const DEFAULT_API_BASE_URL = "http://localhost:8001/api/v1";

function normalizePath(pathname: string): string {
  const trimmed = pathname.replace(/\/+$/, "");
  if (!trimmed || trimmed === "/") {
    return "/api/v1";
  }
  if (/^\/api\/v\d+$/.test(trimmed)) {
    return trimmed;
  }
  if (/^\/api\/v\d+\//.test(trimmed)) {
    return trimmed;
  }
  if (trimmed.startsWith("/api/")) {
    return trimmed;
  }
  return `${trimmed}/api/v1`.replace(/\/{2,}/g, "/");
}

export function resolveApiBaseUrl(rawValue?: string): string {
  const candidate = (rawValue || "").trim() || DEFAULT_API_BASE_URL;
  try {
    const parsed = new URL(candidate.replace(/\/+$/, ""));
    parsed.pathname = normalizePath(parsed.pathname);
    return parsed.toString().replace(/\/+$/, "");
  } catch {
    return DEFAULT_API_BASE_URL;
  }
}

export function buildApiUrl(baseUrl: string, path: string): string {
  const normalizedPath = path.replace(/^\/+/, "");
  return new URL(normalizedPath, `${baseUrl}/`).toString();
}

