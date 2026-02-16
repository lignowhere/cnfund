"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { Eye, Loader2, Pencil, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { MoneyInput } from "@/components/form/money-input";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { apiClient } from "@/lib/api";
import { digitsToNumber } from "@/lib/number-input";
import { queryKeys } from "@/lib/query-keys";
import type { InvestorCardDTO } from "@/lib/types";
import { formatCurrency, formatDateTime, formatPercent } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";
import { useToastStore } from "@/store/toast-store";

type InvestorViewMode = "card" | "table";

function normalizeType(type: string) {
  return type
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

export default function InvestorsPage() {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.accessToken);
  const safeToken = token || "";
  const pushToast = useToastStore((state) => state.push);

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<InvestorViewMode>("card");
  const [selectedInvestor, setSelectedInvestor] = useState<InvestorCardDTO | null>(null);
  const [detailNavDigits, setDetailNavDigits] = useState("");
  const [detailNavOverflow, setDetailNavOverflow] = useState(false);
  const [detailNavApplied, setDetailNavApplied] = useState<number | undefined>(undefined);

  const flagsQuery = useQuery({
    queryKey: queryKeys.featureFlags(safeToken),
    queryFn: () => apiClient.featureFlags(safeToken),
    enabled: !!token,
  });

  const tableViewEnabled = flagsQuery.data?.table_view ?? true;

  const cardsQuery = useInfiniteQuery({
    queryKey: queryKeys.investorCards(safeToken),
    initialPageParam: 1,
    queryFn: ({ pageParam }) => apiClient.investorCardsPaginated(safeToken, pageParam, 20),
    getNextPageParam: (lastPage, pages) => {
      const loaded = pages.reduce((sum, page) => sum + page.items.length, 0);
      if (loaded >= lastPage.total) {
        return undefined;
      }
      return lastPage.page + 1;
    },
    enabled: !!token,
  });

  const investorDetailQuery = useQuery({
    queryKey: queryKeys.investorDetail(safeToken, selectedInvestor?.id, detailNavApplied),
    queryFn: () => apiClient.investorReport(safeToken, selectedInvestor!.id, detailNavApplied),
    enabled: !!token && !!selectedInvestor,
  });

  const investorItems = useMemo(
    () => cardsQuery.data?.pages.flatMap((page) => page.items) ?? [],
    [cardsQuery.data],
  );

  const investorTotal = cardsQuery.data?.pages[0]?.total ?? 0;
  const effectiveViewMode: InvestorViewMode = tableViewEnabled ? viewMode : "card";

  const txStats = useMemo(() => {
    const rows = investorDetailQuery.data?.transactions ?? [];
    const deposits = rows.filter((tx) => {
      const normalized = normalizeType(tx.type);
      return normalized.includes("nap") || normalized.includes("deposit");
    });
    const withdrawals = rows.filter((tx) => {
      const normalized = normalizeType(tx.type);
      return normalized.includes("rut") || normalized.includes("withdraw");
    });
    return {
      deposit_count: deposits.length,
      deposit_amount: deposits.reduce((sum, item) => sum + Math.abs(item.amount), 0),
      withdraw_count: withdrawals.length,
      withdraw_amount: withdrawals.reduce((sum, item) => sum + Math.abs(item.amount), 0),
    };
  }, [investorDetailQuery.data]);

  const createMutation = useMutation({
    mutationFn: () =>
      apiClient.createInvestor(safeToken, {
        name,
        phone,
        email,
        address,
      }),
    onSuccess: () => {
      setName("");
      setPhone("");
      setEmail("");
      setAddress("");
      pushToast({ title: "Đã tạo nhà đầu tư", variant: "success" });
      queryClient.invalidateQueries({ queryKey: queryKeys.investorCards(safeToken), exact: true });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard(safeToken), exact: true });
    },
    onError: (error) => {
      pushToast({
        title: "Không thể tạo nhà đầu tư",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: { investorId: number; name: string }) =>
      apiClient.updateInvestor(safeToken, payload.investorId, { name: payload.name }),
    onSuccess: (_, payload) => {
      setEditingId(null);
      pushToast({ title: "Đã cập nhật tên nhà đầu tư", variant: "success" });
      queryClient.invalidateQueries({ queryKey: queryKeys.investorCards(safeToken), exact: true });
      if (selectedInvestor?.id === payload.investorId) {
        setSelectedInvestor((current) =>
          current ? { ...current, display_name: `${payload.name} (ID: ${payload.investorId})` } : current,
        );
        queryClient.invalidateQueries({
          queryKey: queryKeys.investorDetail(safeToken, payload.investorId),
          exact: false,
        });
      }
    },
    onError: (error) => {
      pushToast({
        title: "Không thể cập nhật nhà đầu tư",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      });
    },
  });

  function openInvestorDetail(item: InvestorCardDTO) {
    setSelectedInvestor(item);
    setDetailNavDigits("");
    setDetailNavOverflow(false);
    setDetailNavApplied(undefined);
  }

  const detailNavNumber = digitsToNumber(detailNavDigits);

  return (
    <div className="app-page">
      <Card className="space-y-3">
        <h2 className="section-title">Thêm nhà đầu tư</h2>
        <div className="grid gap-2 sm:grid-cols-2">
          <Input placeholder="Tên" value={name} onChange={(e) => setName(e.target.value)} />
          <Input placeholder="Số điện thoại" value={phone} onChange={(e) => setPhone(e.target.value)} />
          <Input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <Input placeholder="Địa chỉ" value={address} onChange={(e) => setAddress(e.target.value)} />
        </div>
        <Button className="w-full" onClick={() => createMutation.mutate()} disabled={!name.trim() || createMutation.isPending}>
          {createMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          Tạo nhà đầu tư
        </Button>
      </Card>

      <Card className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="section-title">Danh sách nhà đầu tư</h2>
          {tableViewEnabled ? (
            <div className="flex rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-1">
              <button
                className={`rounded-lg px-3 py-1 text-xs font-medium ${
                  viewMode === "card"
                    ? "bg-[var(--color-primary-50)] text-[var(--color-primary)]"
                    : "text-[var(--color-muted)]"
                }`}
                onClick={() => setViewMode("card")}
                type="button"
              >
                Thẻ
              </button>
              <button
                className={`rounded-lg px-3 py-1 text-xs font-medium ${
                  viewMode === "table"
                    ? "bg-[var(--color-primary-50)] text-[var(--color-primary)]"
                    : "text-[var(--color-muted)]"
                }`}
                onClick={() => setViewMode("table")}
                type="button"
              >
                Bảng
              </button>
            </div>
          ) : (
            <p className="text-xs text-[var(--color-muted)]">Chế độ dạng thẻ</p>
          )}
        </div>

        {cardsQuery.isLoading ? (
          <LoadingState label="Đang tải danh sách nhà đầu tư..." />
        ) : cardsQuery.isError ? (
          <ErrorState message="Không tải được danh sách nhà đầu tư." />
        ) : investorItems.length ? (
          tableViewEnabled && effectiveViewMode === "table" ? (
            <div className="overflow-x-auto rounded-xl border border-[var(--color-border)]">
              <table className="min-w-[780px] text-sm">
                <thead className="sticky top-0 z-20 bg-[var(--color-surface-3)]">
                  <tr>
                    <th className="sticky left-0 z-30 bg-[var(--color-surface-3)] px-3 py-2 text-left">ID</th>
                    <th className="px-3 py-2 text-left">Tên</th>
                    <th className="px-3 py-2 text-left">Email</th>
                    <th className="px-3 py-2 text-left">Giá trị</th>
                    <th className="px-3 py-2 text-left">Lãi/Lỗ</th>
                    <th className="px-3 py-2 text-left">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {investorItems.map((item) => (
                    <tr key={item.id} className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
                      <td className="sticky left-0 z-10 bg-[var(--color-surface)] px-3 py-2">#{item.id}</td>
                      <td className="px-3 py-2">{item.display_name}</td>
                      <td className="px-3 py-2">{item.email || "-"}</td>
                      <td className="px-3 py-2">{formatCurrency(item.current_value)}</td>
                      <td className="px-3 py-2">
                        {formatCurrency(item.pnl)} ({formatPercent(item.pnl_percent)})
                      </td>
                      <td className="px-3 py-2">
                        <Button variant="secondary" className="h-9 px-3 py-1 text-xs" onClick={() => openInvestorDetail(item)}>
                          <Eye className="mr-1 h-4 w-4" />
                          Chi tiết
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null
        ) : null}

        {investorItems.length ? (
          <div className={`list-stagger space-y-2 ${effectiveViewMode === "table" ? "hidden" : ""}`}>
            {investorItems.map((item) => (
              <article
                key={item.id}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    {editingId === item.id ? (
                      <Input
                        defaultValue={item.display_name.split(" (ID")[0]}
                        onBlur={(e) => {
                          const nextName = e.target.value.trim();
                          if (nextName) {
                            updateMutation.mutate({ investorId: item.id, name: nextName });
                          } else {
                            setEditingId(null);
                          }
                        }}
                        autoFocus
                      />
                    ) : (
                      <p className="text-sm font-semibold">{item.display_name}</p>
                    )}
                    <p className="text-xs text-[var(--color-muted)]">{item.phone || "Chưa có số điện thoại"}</p>
                    <p className="text-xs text-[var(--color-muted)]">{item.email || "Chưa có email"}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="secondary" className="h-9 w-9 p-0" onClick={() => openInvestorDetail(item)} aria-label="Xem chi tiết">
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="secondary"
                      className="h-9 w-9 p-0"
                      onClick={() => setEditingId(item.id)}
                      aria-label="Sửa tên nhà đầu tư"
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-lg bg-[var(--color-surface)] px-2 py-2">
                    <p className="text-[var(--color-muted)]">Giá trị hiện tại</p>
                    <p className="font-semibold">{formatCurrency(item.current_value)}</p>
                  </div>
                  <div className="rounded-lg bg-[var(--color-surface)] px-2 py-2">
                    <p className="text-[var(--color-muted)]">Lãi / Lỗ</p>
                    <p className="font-semibold">
                      {formatCurrency(item.pnl)} ({formatPercent(item.pnl_percent)})
                    </p>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState
            title="Chưa có nhà đầu tư."
            description="Tạo nhà đầu tư đầu tiên để bắt đầu luồng giao dịch."
          />
        )}

        {cardsQuery.hasNextPage ? (
          <div className="space-y-2">
            <Button
              variant="secondary"
              className="w-full"
              onClick={() => cardsQuery.fetchNextPage()}
              disabled={cardsQuery.isFetchingNextPage}
            >
              {cardsQuery.isFetchingNextPage ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Tải thêm nhà đầu tư
            </Button>
            <p className="text-center text-xs text-[var(--color-muted)]">
              Đang hiển thị {investorItems.length}/{investorTotal} nhà đầu tư
            </p>
          </div>
        ) : null}
      </Card>

      <Dialog.Root
        open={!!selectedInvestor}
        onOpenChange={(open) => {
          if (!open) {
            setSelectedInvestor(null);
            setDetailNavDigits("");
            setDetailNavOverflow(false);
            setDetailNavApplied(undefined);
          }
        }}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40 data-[state=open]:animate-[overlay-in_180ms_ease-out]" />
          <Dialog.Content className="fixed inset-0 z-50 overflow-y-auto border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-2xl data-[state=open]:animate-[fade-up_220ms_ease-out] md:inset-x-auto md:left-1/2 md:top-1/2 md:h-auto md:max-h-[88vh] md:w-[820px] md:-translate-x-1/2 md:-translate-y-1/2 md:rounded-2xl md:p-5">
            <div className="sticky top-0 z-10 mb-3 flex items-center justify-between gap-2 border-b border-[var(--color-border)] bg-[var(--color-surface)] pb-3">
              <Dialog.Title className="section-title">
                Chi tiết nhà đầu tư
                {selectedInvestor ? ` - #${selectedInvestor.id}` : ""}
              </Dialog.Title>
              <Dialog.Close asChild>
                <Button variant="secondary" className="h-9 w-9 p-0" aria-label="Đóng chi tiết nhà đầu tư">
                  <X className="h-4 w-4" />
                </Button>
              </Dialog.Close>
            </div>

            <div className="mb-3 grid gap-2 md:grid-cols-[1fr_auto]">
              <div>
                <MoneyInput
                  value={detailNavDigits}
                  onValueChange={(value) => {
                    setDetailNavDigits(value.rawDigits);
                    setDetailNavOverflow(value.isOverflow);
                  }}
                  placeholder="2,500,000,000"
                  aria-invalid={detailNavOverflow}
                />
                <p className="input-helper">
                  NAV tùy chọn: {detailNavNumber ? formatCurrency(detailNavNumber) : "Theo NAV hiện tại"}
                </p>
                {detailNavOverflow ? <p className="inline-error">NAV quá lớn (tối đa 15 chữ số).</p> : null}
              </div>
              <Button
                variant="secondary"
                onClick={() => {
                  if (detailNavOverflow) return;
                  setDetailNavApplied(detailNavNumber && detailNavNumber > 0 ? detailNavNumber : undefined);
                }}
                disabled={detailNavOverflow}
              >
                Áp dụng NAV
              </Button>
            </div>

            {investorDetailQuery.isLoading ? (
              <LoadingState label="Đang tải báo cáo chi tiết nhà đầu tư..." />
            ) : investorDetailQuery.isError ? (
              <ErrorState message="Không tải được chi tiết nhà đầu tư." />
            ) : investorDetailQuery.data ? (
              <div className="space-y-3">
                <Card className="space-y-2">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-base font-semibold">{investorDetailQuery.data.investor.name}</p>
                      <p className="text-xs text-[var(--color-muted)]">
                        Ngày tham gia: {investorDetailQuery.data.investor.join_date}
                      </p>
                    </div>
                    <div className="text-xs text-[var(--color-muted)]">
                      <p>NAV áp dụng: {formatCurrency(investorDetailQuery.data.current_nav)}</p>
                      <p>Giá/đơn vị: {formatCurrency(investorDetailQuery.data.current_price)}</p>
                    </div>
                  </div>
                  <div className="grid gap-2 text-xs sm:grid-cols-3">
                    <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                      Điện thoại: {investorDetailQuery.data.investor.phone || "Chưa cập nhật"}
                    </p>
                    <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                      Email: {investorDetailQuery.data.investor.email || "Chưa cập nhật"}
                    </p>
                    <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                      Địa chỉ: {investorDetailQuery.data.investor.address || "Chưa cập nhật"}
                    </p>
                  </div>
                </Card>

                <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
                  <Card>
                    <p className="kpi-label">Giá trị hiện tại</p>
                    <p className="kpi-value">{formatCurrency(investorDetailQuery.data.current_balance)}</p>
                  </Card>
                  <Card>
                    <p className="kpi-label">Lãi/Lỗ hiện tại</p>
                    <p className="kpi-value">{formatCurrency(investorDetailQuery.data.current_profit)}</p>
                    <p className="text-xs text-[var(--color-muted)]">
                      {formatPercent(investorDetailQuery.data.current_profit_perc)}
                    </p>
                  </Card>
                  <Card>
                    <p className="kpi-label">Vốn gốc</p>
                    <p className="kpi-value">
                      {formatCurrency(investorDetailQuery.data.lifetime_performance.original_invested)}
                    </p>
                  </Card>
                  <Card>
                    <p className="kpi-label">Tổng phí đã thu</p>
                    <p className="kpi-value">
                      {formatCurrency(investorDetailQuery.data.lifetime_performance.total_fees_paid)}
                    </p>
                  </Card>
                </div>

                <div className="grid grid-cols-1 gap-2 lg:grid-cols-2">
                  <Card className="space-y-2">
                    <h3 className="section-title">Hiệu suất tích lũy</h3>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Lợi nhuận gộp:{" "}
                        <span className="font-semibold">
                          {formatCurrency(investorDetailQuery.data.lifetime_performance.gross_profit)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Lợi nhuận ròng:{" "}
                        <span className="font-semibold">
                          {formatCurrency(investorDetailQuery.data.lifetime_performance.net_profit)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Tỷ suất gộp:{" "}
                        <span className="font-semibold">
                          {formatPercent(investorDetailQuery.data.lifetime_performance.gross_return)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Tỷ suất ròng:{" "}
                        <span className="font-semibold">
                          {formatPercent(investorDetailQuery.data.lifetime_performance.net_return)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Tổng đơn vị hiện tại:{" "}
                        <span className="font-semibold">
                          {investorDetailQuery.data.lifetime_performance.current_units.toFixed(6)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Báo cáo lúc:{" "}
                        <span className="font-semibold">{formatDateTime(investorDetailQuery.data.report_date)}</span>
                      </p>
                    </div>
                  </Card>

                  <Card className="space-y-2">
                    <h3 className="section-title">Nạp/Rút và chỉ số phí</h3>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Tổng nạp ({txStats.deposit_count} GD):{" "}
                        <span className="font-semibold">{formatCurrency(txStats.deposit_amount)}</span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Tổng rút ({txStats.withdraw_count} GD):{" "}
                        <span className="font-semibold">{formatCurrency(txStats.withdraw_amount)}</span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Hurdle value:{" "}
                        <span className="font-semibold">
                          {formatCurrency(investorDetailQuery.data.fee_details.hurdle_value)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        HWM value:{" "}
                        <span className="font-semibold">
                          {formatCurrency(investorDetailQuery.data.fee_details.hwm_value)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Excess profit:{" "}
                        <span className="font-semibold">
                          {formatCurrency(investorDetailQuery.data.fee_details.excess_profit)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Tổng phí:{" "}
                        <span className="font-semibold">
                          {formatCurrency(investorDetailQuery.data.fee_details.total_fee)}
                        </span>
                      </p>
                    </div>
                  </Card>
                </div>

                <Card className="space-y-2">
                  <h3 className="section-title">Lịch sử giao dịch ({investorDetailQuery.data.transactions.length})</h3>
                  {investorDetailQuery.data.transactions.length ? (
                    <div className="list-stagger space-y-2">
                      {investorDetailQuery.data.transactions.slice(0, 12).map((tx) => (
                        <article
                          key={tx.id}
                          className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-2"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <p className="text-sm font-semibold">{tx.type}</p>
                            <p className="text-xs text-[var(--color-muted)]">#{tx.id}</p>
                          </div>
                          <p className="text-xs text-[var(--color-muted)]">{formatDateTime(tx.date)}</p>
                          <p className="text-sm">
                            Số tiền: {formatCurrency(tx.amount)} | NAV: {formatCurrency(tx.nav)} | Units:{" "}
                            {tx.units_change.toFixed(6)}
                          </p>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <EmptyState title="Nhà đầu tư chưa có lịch sử nạp/rút." />
                  )}
                </Card>

                <Card className="space-y-2">
                  <h3 className="section-title">Danh mục tranche ({investorDetailQuery.data.tranches.length})</h3>
                  {investorDetailQuery.data.tranches.length ? (
                    <div className="list-stagger space-y-2">
                      {investorDetailQuery.data.tranches.map((tranche) => (
                        <article
                          key={tranche.tranche_id}
                          className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-2 text-sm"
                        >
                          <p className="font-semibold">Tranche {tranche.tranche_id}</p>
                          <p className="text-xs text-[var(--color-muted)]">
                            Ngày vào: {formatDateTime(tranche.entry_date)} | NAV vào: {formatCurrency(tranche.entry_nav)}
                          </p>
                          <p className="text-xs text-[var(--color-muted)]">
                            Units: {tranche.units.toFixed(6)} | HWM: {formatCurrency(tranche.hwm)} | Vốn ban đầu:{" "}
                            {formatCurrency(tranche.original_invested_value)}
                          </p>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <EmptyState title="Không có tranche để hiển thị." />
                  )}
                </Card>

                <Card className="space-y-2">
                  <h3 className="section-title">Lịch sử phí ({investorDetailQuery.data.fee_history.length})</h3>
                  {investorDetailQuery.data.fee_history.length ? (
                    <div className="list-stagger space-y-2">
                      {investorDetailQuery.data.fee_history.slice(0, 8).map((fee) => (
                        <article
                          key={fee.id}
                          className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-2"
                        >
                          <p className="text-sm font-semibold">
                            {fee.period} - {formatCurrency(fee.fee_amount)}
                          </p>
                          <p className="text-xs text-[var(--color-muted)]">
                            Ngày tính: {fee.calculation_date} | Units phí: {fee.fee_units.toFixed(6)}
                          </p>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <EmptyState title="Nhà đầu tư chưa có lịch sử phí." />
                  )}
                </Card>
              </div>
            ) : (
              <EmptyState title="Chọn nhà đầu tư để xem chi tiết." />
            )}
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}
