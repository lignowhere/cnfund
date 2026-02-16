"use client";

export function buildNetworkError(error: unknown, apiBaseUrl: string): Error {
  if (error instanceof Error && error.name !== "TypeError") {
    return error;
  }

  const hints = [
    `Không thể kết nối tới API: ${apiBaseUrl}`,
    "Kiểm tra backend API đã chạy chưa (ví dụ: http://127.0.0.1:8001/health).",
    "Kiểm tra NEXT_PUBLIC_API_BASE_URL trong frontend_app/.env.local.",
    "Kiểm tra CORS (API_ALLOWED_ORIGINS/API_ALLOWED_ORIGIN_REGEX) có cho phép origin frontend hiện tại.",
  ];

  if (typeof window !== "undefined") {
    const currentOrigin = window.location.origin;
    hints.splice(1, 0, `Origin hiện tại: ${currentOrigin}`);
    if (window.location.protocol === "https:" && apiBaseUrl.startsWith("http://")) {
      hints.push("Trang đang chạy HTTPS nhưng API lại HTTP (mixed content sẽ bị chặn).");
    }
  }

  return new Error(hints.join(" "));
}

