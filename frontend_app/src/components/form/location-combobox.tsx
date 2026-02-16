"use client";

import { Check, ChevronsUpDown } from "lucide-react";
import { useMemo, useRef, useState } from "react";

import { cn } from "@/lib/utils";

export type LocationOption = {
  code: string;
  name: string;
};

function normalizeText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

type LocationComboboxProps = {
  options: LocationOption[];
  value: string;
  onChange: (option: LocationOption | null) => void;
  placeholder: string;
  disabled?: boolean;
  invalid?: boolean;
  className?: string;
  noMatchLabel?: string;
};

export function LocationCombobox({
  options,
  value,
  onChange,
  placeholder,
  disabled = false,
  invalid = false,
  className,
  noMatchLabel = "Không tìm thấy kết quả phù hợp",
}: LocationComboboxProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const closeTimerRef = useRef<number | null>(null);

  const selectedOption = useMemo(
    () => options.find((option) => option.code === value) ?? null,
    [options, value],
  );

  const visibleValue = isOpen ? query : selectedOption?.name ?? "";

  const filtered = useMemo(() => {
    const keyword = normalizeText(query);
    if (!keyword) return options.slice(0, 120);
    return options
      .filter((option) => normalizeText(`${option.name} ${option.code}`).includes(keyword))
      .slice(0, 120);
  }, [options, query]);

  function pick(option: LocationOption) {
    setQuery(option.name);
    setIsOpen(false);
    setHighlightedIndex(0);
    onChange(option);
  }

  return (
    <div className={cn("relative", className)}>
      <input
        type="text"
        value={visibleValue}
        placeholder={placeholder}
        disabled={disabled}
        className={cn(
          "min-h-11 w-full rounded-[var(--radius-control)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 pr-10 text-base text-[var(--color-text)] shadow-sm md:text-sm",
          "placeholder:text-[var(--color-muted)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20",
          invalid &&
            "border-[var(--color-danger)] ring-2 ring-[color-mix(in_oklab,var(--color-danger)_24%,transparent)]",
          disabled && "cursor-not-allowed opacity-70",
        )}
        onFocus={() => {
          if (disabled) return;
          setQuery(selectedOption?.name ?? "");
          setIsOpen(true);
        }}
        onBlur={() => {
          closeTimerRef.current = window.setTimeout(() => setIsOpen(false), 100);
        }}
        onChange={(event) => {
          setQuery(event.target.value);
          setIsOpen(true);
          setHighlightedIndex(0);
          if (value) onChange(null);
        }}
        onKeyDown={(event) => {
          if (!isOpen && (event.key === "ArrowDown" || event.key === "ArrowUp")) {
            event.preventDefault();
            setIsOpen(true);
            return;
          }
          if (!isOpen) return;
          if (event.key === "ArrowDown") {
            event.preventDefault();
            setHighlightedIndex((current) => Math.min(current + 1, filtered.length - 1));
          }
          if (event.key === "ArrowUp") {
            event.preventDefault();
            setHighlightedIndex((current) => Math.max(current - 1, 0));
          }
          if (event.key === "Enter") {
            event.preventDefault();
            const option = filtered[highlightedIndex];
            if (option) pick(option);
          }
          if (event.key === "Escape") {
            event.preventDefault();
            setIsOpen(false);
          }
        }}
      />
      <div className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-[var(--color-muted)]">
        <ChevronsUpDown className="h-4 w-4" />
      </div>

      {isOpen ? (
        <div className="absolute z-[70] mt-1 max-h-64 w-full overflow-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-1 shadow-[var(--shadow-card)]">
          {filtered.length ? (
            <ul className="space-y-0.5">
              {filtered.map((option, index) => (
                <li key={option.code}>
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
                      pick(option);
                    }}
                  >
                    <span>
                      {option.name} <span className="text-xs text-[var(--color-muted)]">({option.code})</span>
                    </span>
                    {option.code === value ? <Check className="h-4 w-4" /> : null}
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
