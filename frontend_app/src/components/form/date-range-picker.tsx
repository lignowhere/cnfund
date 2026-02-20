"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type DateRangeValue = {
  startDate: string;
  endDate: string;
};

type DateRangePickerProps = DateRangeValue & {
  onChange: (value: DateRangeValue) => void;
  disabled?: boolean;
};

type Preset = {
  id: string;
  label: string;
  build: (today: Date) => DateRangeValue;
};

function toIsoDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function minusDays(value: Date, days: number): Date {
  const copy = new Date(value);
  copy.setDate(copy.getDate() - days);
  return copy;
}

function normalizeRange(range: DateRangeValue): DateRangeValue {
  const { startDate, endDate } = range;
  if (!startDate || !endDate) {
    return range;
  }
  if (startDate <= endDate) {
    return range;
  }
  return { startDate: endDate, endDate: startDate };
}

const PRESETS: Preset[] = [
  {
    id: "1m",
    label: "1 tháng",
    build: (today) => ({ startDate: toIsoDate(minusDays(today, 30)), endDate: toIsoDate(today) }),
  },
  {
    id: "3m",
    label: "3 tháng",
    build: (today) => ({ startDate: toIsoDate(minusDays(today, 90)), endDate: toIsoDate(today) }),
  },
  {
    id: "6m",
    label: "6 tháng",
    build: (today) => ({ startDate: toIsoDate(minusDays(today, 180)), endDate: toIsoDate(today) }),
  },
  {
    id: "ytd",
    label: "YTD",
    build: (today) => ({
      startDate: `${today.getFullYear()}-01-01`,
      endDate: toIsoDate(today),
    }),
  },
  {
    id: "1y",
    label: "1 năm",
    build: (today) => ({ startDate: toIsoDate(minusDays(today, 365)), endDate: toIsoDate(today) }),
  },
  {
    id: "3y",
    label: "3 năm",
    build: (today) => ({ startDate: toIsoDate(minusDays(today, 1095)), endDate: toIsoDate(today) }),
  },
  {
    id: "5y",
    label: "5 năm",
    build: (today) => ({ startDate: toIsoDate(minusDays(today, 1825)), endDate: toIsoDate(today) }),
  },
];

export function DateRangePicker({ startDate, endDate, onChange, disabled = false }: DateRangePickerProps) {
  const handlePreset = (preset: Preset) => {
    onChange(normalizeRange(preset.build(new Date())));
  };

  const handleStartDateChange = (value: string) => {
    onChange(normalizeRange({ startDate: value, endDate }));
  };

  const handleEndDateChange = (value: string) => {
    onChange(normalizeRange({ startDate, endDate: value }));
  };

  const handleClear = () => {
    onChange({ startDate: "", endDate: "" });
  };

  return (
    <div className="space-y-2">
      <div className="grid gap-2 sm:grid-cols-2">
        <Input
          type="date"
          value={startDate}
          onChange={(event) => handleStartDateChange(event.target.value)}
          disabled={disabled}
          aria-label="Từ ngày"
        />
        <Input
          type="date"
          value={endDate}
          onChange={(event) => handleEndDateChange(event.target.value)}
          disabled={disabled}
          aria-label="Đến ngày"
        />
      </div>
      <div className="flex flex-wrap gap-2">
        {PRESETS.map((preset) => (
          <Button
            key={preset.id}
            type="button"
            variant="secondary"
            onClick={() => handlePreset(preset)}
            disabled={disabled}
            className="min-h-8 px-3 py-1 text-xs"
          >
            {preset.label}
          </Button>
        ))}
        <Button
          type="button"
          variant="secondary"
          onClick={handleClear}
          disabled={disabled}
          className="min-h-8 px-3 py-1 text-xs"
        >
          Toàn bộ
        </Button>
      </div>
    </div>
  );
}
