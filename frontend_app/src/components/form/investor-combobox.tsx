"use client";

import { Check, ChevronsUpDown, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import type { InvestorSelectOption } from "@/lib/types";
import { cn } from "@/lib/utils";

function normalizeText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

type InvestorComboboxProps = {
  options: InvestorSelectOption[];
  value: number | null;
  onChange: (option: InvestorSelectOption | null) => void;
  placeholder?: string;
  disabled?: boolean;
  allowClear?: boolean;
  className?: string;
  noMatchLabel?: string;
  invalid?: boolean;
};

export function InvestorCombobox({
  options,
  value,
  onChange,
  placeholder = "Tìm theo tên hoặc ID nhà đầu tư",
  disabled = false,
  allowClear = false,
  className,
  noMatchLabel = "Không tìm thấy nhà đầu tư phù hợp",
  invalid = false,
}: InvestorComboboxProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const closeTimerRef = useRef<number | null>(null);

  const selectedOption = useMemo(
    () => options.find((option) => option.id === value) ?? null,
    [options, value],
  );

  useEffect(() => {
    return () => {
      if (closeTimerRef.current) {
        window.clearTimeout(closeTimerRef.current);
      }
    };
  }, []);

  const visibleValue = isOpen ? query : selectedOption?.displayName ?? "";

  const filteredOptions = useMemo(() => {
    const keyword = normalizeText(query);
    if (!keyword) return options.slice(0, 80);
    return options.filter((option) => normalizeText(option.searchText).includes(keyword)).slice(0, 80);
  }, [options, query]);

  function selectOption(option: InvestorSelectOption) {
    setQuery(option.displayName);
    setIsOpen(false);
    setHighlightedIndex(0);
    onChange(option);
  }

  return (
    <div className={cn("relative", className)}>
      <div className="relative">
        <input
          type="text"
          value={visibleValue}
          disabled={disabled}
          placeholder={placeholder}
          className={cn(
            "min-h-11 w-full rounded-[var(--radius-control)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 pr-16 text-base text-[var(--color-text)] shadow-sm md:text-sm",
            "placeholder:text-[var(--color-muted)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20",
            invalid &&
              "border-[var(--color-danger)] ring-2 ring-[color-mix(in_oklab,var(--color-danger)_24%,transparent)]",
            disabled && "cursor-not-allowed opacity-70",
          )}
          onFocus={() => {
            if (disabled) return;
            setQuery(selectedOption?.displayName ?? "");
            setIsOpen(true);
            setHighlightedIndex(0);
          }}
          onBlur={() => {
            closeTimerRef.current = window.setTimeout(() => {
              setIsOpen(false);
            }, 100);
          }}
          onChange={(event) => {
            setQuery(event.target.value);
            setIsOpen(true);
            setHighlightedIndex(0);
            if (value !== null) {
              onChange(null);
            }
          }}
          onKeyDown={(event) => {
            if (!isOpen && (event.key === "ArrowDown" || event.key === "ArrowUp")) {
              event.preventDefault();
              setQuery(selectedOption?.displayName ?? "");
              setIsOpen(true);
              return;
            }
            if (!isOpen) return;

            if (event.key === "ArrowDown") {
              event.preventDefault();
              setHighlightedIndex((current) => Math.min(current + 1, filteredOptions.length - 1));
            }
            if (event.key === "ArrowUp") {
              event.preventDefault();
              setHighlightedIndex((current) => Math.max(current - 1, 0));
            }
            if (event.key === "Enter") {
              event.preventDefault();
              const candidate = filteredOptions[highlightedIndex];
              if (candidate) {
                selectOption(candidate);
              }
            }
            if (event.key === "Escape") {
              event.preventDefault();
              setIsOpen(false);
            }
          }}
        />

        <div className="pointer-events-none absolute inset-y-0 right-3 flex items-center gap-1 text-[var(--color-muted)]">
          <ChevronsUpDown className="h-4 w-4" />
        </div>

        {allowClear && value !== null && !disabled ? (
          <button
            type="button"
            aria-label="Xóa lựa chọn nhà đầu tư"
            className="absolute inset-y-1 right-8 inline-flex w-6 items-center justify-center rounded-md text-[var(--color-muted)] hover:bg-[var(--color-surface-2)] hover:text-[var(--color-text)]"
            onClick={() => {
              onChange(null);
              setQuery("");
              setIsOpen(true);
            }}
          >
            <X className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      {isOpen ? (
        <div className="absolute z-[70] mt-1 max-h-64 w-full overflow-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-1 shadow-[var(--shadow-card)]">
          {filteredOptions.length ? (
            <ul className="space-y-0.5">
              {filteredOptions.map((option, index) => (
                <li key={option.id}>
                  <button
                    type="button"
                    className={cn(
                      "flex min-h-11 w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition-colors",
                      index === highlightedIndex
                        ? "bg-[var(--color-primary-50)] text-[var(--color-primary)]"
                        : "text-[var(--color-text)] hover:bg-[var(--color-surface-2)]",
                    )}
                    onMouseDown={(event) => {
                      event.preventDefault();
                      selectOption(option);
                    }}
                  >
                    <span>{option.displayName}</span>
                    {option.id === value ? <Check className="h-4 w-4" /> : null}
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="px-3 py-3 text-sm text-[var(--color-muted)]">{noMatchLabel}</p>
          )}
        </div>
      ) : null}
    </div>
  );
}
