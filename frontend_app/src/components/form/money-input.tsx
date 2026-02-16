"use client";

import { useCallback, useMemo, useRef } from "react";
import type { InputHTMLAttributes } from "react";

import { Input } from "@/components/ui/input";
import {
  MAX_MONEY_DIGITS,
  caretFromDigits,
  formatDigitsWithCommas,
  parseMoneyInput,
} from "@/lib/number-input";
import type { MoneyInputValue } from "@/lib/types";

type MoneyInputProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "type" | "value" | "onChange" | "inputMode" | "pattern"
> & {
  value: string;
  onValueChange: (value: MoneyInputValue) => void;
  maxDigits?: number;
};

export function MoneyInput({
  value,
  onValueChange,
  maxDigits = MAX_MONEY_DIGITS,
  placeholder = "50,000,000",
  ...props
}: MoneyInputProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  const formattedValue = useMemo(() => formatDigitsWithCommas(value), [value]);

  const handleChange = useCallback(
    (nextRaw: string, caretPosition: number | null) => {
      const digitsBeforeCaret =
        caretPosition === null
          ? nextRaw.replace(/\D/g, "").length
          : nextRaw.slice(0, caretPosition).replace(/\D/g, "").length;

      const parsed = parseMoneyInput(nextRaw, maxDigits);
      onValueChange(parsed);

      requestAnimationFrame(() => {
        const element = inputRef.current;
        if (!element) return;
        const nextCaret = caretFromDigits(element.value, digitsBeforeCaret);
        element.setSelectionRange(nextCaret, nextCaret);
      });
    },
    [maxDigits, onValueChange],
  );

  return (
    <Input
      ref={inputRef}
      type="text"
      value={formattedValue}
      onChange={(event) => handleChange(event.target.value, event.target.selectionStart)}
      inputMode="numeric"
      pattern="[0-9]*"
      autoComplete="off"
      placeholder={placeholder}
      {...props}
    />
  );
}
