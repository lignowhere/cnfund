import type { MoneyInputValue } from "@/lib/types";

export const MAX_MONEY_DIGITS = 15;

export function sanitizeDigits(value: string, maxDigits = MAX_MONEY_DIGITS): string {
  return value.replace(/\D/g, "").slice(0, maxDigits);
}

export function formatDigitsWithCommas(digits: string): string {
  if (!digits) return "";
  return digits.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

export function digitsToNumber(digits: string): number | null {
  if (!digits) return null;
  const parsed = Number(digits);
  if (!Number.isFinite(parsed)) return null;
  if (!Number.isSafeInteger(parsed)) return null;
  return parsed;
}

export function parseMoneyInput(rawValue: string, maxDigits = MAX_MONEY_DIGITS): MoneyInputValue {
  const incomingDigits = rawValue.replace(/\D/g, "");
  const isOverflow = incomingDigits.length > maxDigits;
  const rawDigits = sanitizeDigits(rawValue, maxDigits);
  return {
    rawDigits,
    numericValue: digitsToNumber(rawDigits),
    formatted: formatDigitsWithCommas(rawDigits),
    isOverflow,
  };
}

export function caretFromDigits(formatted: string, digitsBeforeCaret: number): number {
  if (digitsBeforeCaret <= 0) return 0;
  let digitsSeen = 0;
  for (let index = 0; index < formatted.length; index += 1) {
    if (/\d/.test(formatted[index])) {
      digitsSeen += 1;
      if (digitsSeen >= digitsBeforeCaret) {
        return index + 1;
      }
    }
  }
  return formatted.length;
}
